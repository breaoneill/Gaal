import io
import json
import socket
import ssl
import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, call, patch
from urllib.error import HTTPError, URLError

import test_gaal
from test_gaal import item, NOW, SCHEDULE
from gaal.reasoning import OpenAIReasoningProvider, ProviderAPIError, ReasoningError
from gaal.secrets import resolve_secret
from gaal.store import SQLiteStore
from gaal.workflow import run_daily, WorkflowFailure


def response(url, payload, headers):
    template = test_gaal.GaalTests().reasoning_payload()["items"][0]
    values = [{**template, "id": value["id"]} for value in json.loads(payload["input"])]
    return {"output": [{"content": [{"type": "output_text", "text": json.dumps({"items": values})}]}],
            "usage": {"input_tokens": 100, "output_tokens": 100}}


class ReliabilityTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.state = Path(directory.name) / "test.db"

    def provider(self, request):
        return OpenAIReasoningProvider(model="test", api_key="secret", request=request)

    def test_transient_success_and_exhaustion(self):
        errors = [ProviderAPIError(provider="OpenAI", status=status)
                  for status in (429, 500, 502, 503, 504)]
        errors += [TimeoutError(), ConnectionResetError(), URLError(TimeoutError()),
                   URLError(socket.gaierror(socket.EAI_AGAIN, "temporary DNS"))]
        for error in errors:
            with self.subTest(error=repr(error)), patch("gaal.reasoning.time.sleep") as sleep:
                good = response("", {"input": '[{"id":"item-0"}]'}, {})
                request = Mock(side_effect=[error, error, good])
                self.assertEqual(len(self.provider(request).interpret([item()])), 1)
                self.assertEqual(request.call_count, 3)
                self.assertEqual(sleep.call_args_list, [call(1), call(2)])
                sleep.reset_mock()
                request = Mock(side_effect=error)
                with self.assertRaises(type(error)) as raised:
                    self.provider(request).interpret([item()])
                self.assertIs(raised.exception, error)
                self.assertEqual(request.call_count, 3)
                self.assertEqual(sleep.call_args_list, [call(1), call(2)])

    def test_deterministic_errors_are_not_retried(self):
        errors = [ProviderAPIError(provider="OpenAI", status=status)
                  for status in (400, 401, 403, 404, 422, 501)]
        errors += [ProviderAPIError(provider="OpenAI", status=429, error_type="insufficient_quota"),
                   URLError(ssl.SSLCertVerificationError("certificate")),
                   URLError(socket.gaierror(socket.EAI_NONAME, "invalid name")),
                   URLError("unknown error"), ValueError("invalid"), ReasoningError("schema")]
        for error in errors:
            with self.subTest(error=repr(error)), patch("gaal.reasoning.time.sleep") as sleep:
                request = Mock(side_effect=error)
                with self.assertRaises(type(error)):
                    self.provider(request).interpret([item()])
                request.assert_called_once()
                sleep.assert_not_called()

    def test_invalid_responses_are_not_retried(self):
        good = response("", {"input": '[{"id":"item-0"}]'}, {})
        invalid_schema = response("", {"input": '[]'}, {})
        invalid_json = {**good, "output": [{"content": [{"type": "output_text", "text": "bad json"}]}]}
        for value in ({}, invalid_schema, invalid_json):
            with self.subTest(value=value), patch("gaal.reasoning.time.sleep") as sleep:
                request = Mock(return_value=value)
                with self.assertRaises(ReasoningError):
                    self.provider(request).interpret([item()])
                request.assert_called_once()
                sleep.assert_not_called()

    def test_transport_wrapped_network_error_retries(self):
        with patch("gaal.reasoning.urlopen", side_effect=URLError(TimeoutError())) as request, \
             patch("gaal.reasoning.time.sleep"):
            with self.assertRaises(ReasoningError):
                OpenAIReasoningProvider(model="test", api_key="secret").interpret([item()])
            self.assertEqual(request.call_count, 3)

    def test_exhaustion_keeps_workflow_diagnostic(self):
        from gaal.cli import _failure_notification
        body = b'{"error":{"type":"server_error","code":"server_error","message":"temporary failure"}}'
        def fail(*args, **kwargs):
            raise HTTPError("https://api.openai.com/v1/responses", 500, "error", {}, io.BytesIO(body))
        store = SQLiteStore(self.state)
        destination = Mock(name="destination")
        destination.name = "test"
        with patch("gaal.reasoning.urlopen", side_effect=fail) as request, \
             patch("gaal.reasoning.time.sleep"), self.assertRaises(WorkflowFailure) as raised:
            run_daily(scheduled_date=NOW.date(), actual_run_time=NOW, schedule=SCHEDULE,
                      source=Mock(read=Mock(return_value=[item()])), destination=destination,
                      store=store, dry_run=False,
                      reasoning=OpenAIReasoningProvider(model="test", api_key="secret"))
        self.assertEqual(request.call_count, 3)
        self.assertEqual(raised.exception.stage, "reasoning")
        self.assertIn("HTTP: 500", _failure_notification(raised.exception).body)
        self.assertIn("server_error", _failure_notification(raised.exception).body)
        self.assertEqual(store.last_run()["failure_stage"], "reasoning")
        destination.deliver.assert_not_called()

    def test_linux_secret_and_environment_precedence(self):
        with patch("gaal.secrets.sys.platform", "linux"), \
             patch.dict("os.environ", {}, clear=True), patch("gaal.secrets.subprocess.run") as run:
            for service in (None, "configured-keychain"):
                with self.assertRaisesRegex(ValueError, "TEST_SECRET is not set"):
                    resolve_secret(env_name="TEST_SECRET", keychain_service=service)
            run.assert_not_called()
            with patch.dict("os.environ", {"TEST_SECRET": "secret"}):
                self.assertEqual(resolve_secret(env_name="TEST_SECRET", keychain_service="keychain"), "secret")
            run.assert_not_called()

    def test_progress_is_bounded_and_contains_only_safe_counts(self):
        values = [item(id=f"private-id-{i}", source="private-sender", summary="private-content")
                  for i in range(244)]
        request = Mock(side_effect=response)
        with self.assertLogs("gaal", level="INFO") as logs:
            self.provider(request).interpret(values)
        self.assertEqual([r.getMessage() for r in logs.records], [
            "Gaal daily: reasoning 60/244", "Gaal daily: reasoning 100/244",
            "Gaal daily: reasoning 160/244", "Gaal daily: reasoning 200/244",
            "Gaal daily: reasoning 244/244"])
        for dry_run in (False, True):
            destination = Mock()
            destination.name = "private-destination"
            with self.assertLogs("gaal", level="INFO") as logs:
                run_daily(scheduled_date=NOW.date(), actual_run_time=NOW, schedule=SCHEDULE,
                          source=Mock(read=Mock(return_value=values)), destination=destination,
                          store=SQLiteStore(self.state), dry_run=dry_run)
            self.assertEqual([r.getMessage() for r in logs.records], [
                "Gaal daily: fetched 244 messages", "Gaal daily: classified 244",
                "Gaal daily: dry run completed" if dry_run else "Gaal daily: delivered successfully"])

    def test_retry_logs_do_not_include_exception_details(self):
        request = Mock(side_effect=ProviderAPIError(provider="OpenAI", status=500,
                                                   message="private content and secret"))
        with patch("gaal.reasoning.time.sleep"), self.assertLogs("gaal", level="INFO") as logs:
            with self.assertRaises(ProviderAPIError):
                self.provider(request).interpret([item()])
        self.assertEqual([r.getMessage() for r in logs.records], [
            "Gaal daily: transient reasoning failure; retry 2/3 in 1s",
            "Gaal daily: transient reasoning failure; retry 3/3 in 2s"])
