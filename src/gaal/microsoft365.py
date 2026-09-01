from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from .models import Item


GRAPH_ROOT = "https://graph.microsoft.com/v1.0"
SCOPES = ("Mail.Read",)


class AuthenticationRequired(RuntimeError):
    pass


class GraphError(RuntimeError):
    pass


class TokenProvider(Protocol):
    def get_token(self, *, interactive: bool = False) -> str: ...


class DeviceCodeCredential:
    """Delegated Mail.Read credential with an owner-only MSAL token cache."""

    def __init__(self, *, client_id: str, tenant_id: str, cache_path: str | Path,
                 prompt: Callable[[str], None] = print):
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.cache_path = Path(cache_path)
        self.prompt = prompt

    def _msal(self):
        try:
            import msal
        except ImportError as exc:
            raise RuntimeError(
                "Microsoft 365 support is not installed; install gaal[microsoft365]"
            ) from exc
        return msal

    def _save(self, cache) -> None:
        if not cache.has_state_changed:
            return
        self.cache_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.cache_path.parent, 0o700)
        descriptor, temporary = tempfile.mkstemp(dir=self.cache_path.parent)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(cache.serialize())
            os.replace(temporary, self.cache_path)
            os.chmod(self.cache_path, 0o600)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def get_token(self, *, interactive: bool = False) -> str:
        msal = self._msal()
        cache = msal.SerializableTokenCache()
        if self.cache_path.exists():
            cache.deserialize(self.cache_path.read_text(encoding="utf-8"))
        app = msal.PublicClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            token_cache=cache,
        )
        accounts = app.get_accounts()
        result = app.acquire_token_silent(list(SCOPES), account=accounts[0]) if accounts else None
        if not result and interactive:
            flow = app.initiate_device_flow(scopes=list(SCOPES))
            if "user_code" not in flow:
                raise AuthenticationRequired("Microsoft did not start device authentication")
            self.prompt(flow["message"])
            result = app.acquire_token_by_device_flow(flow)
        self._save(cache)
        if not result or "access_token" not in result:
            detail = result.get("error_description") if isinstance(result, dict) else None
            raise AuthenticationRequired(detail or "run 'gaal auth-microsoft365' to sign in")
        return result["access_token"]


def _utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _summary(subject: str, preview: str, limit: int = 500) -> str:
    subject = " ".join((subject or "(no subject)").split())
    preview = " ".join((preview or "").split())
    combined = f"{subject} — {preview}" if preview else subject
    return combined[:limit].rstrip()


def _source(message: dict[str, Any]) -> str:
    sender = (message.get("from") or {}).get("emailAddress") or {}
    return sender.get("name") or sender.get("address") or "Unknown sender"


def normalize_message(message: dict[str, Any]) -> Item:
    message_id = message.get("internetMessageId") or message.get("id")
    if not isinstance(message_id, str) or not message_id:
        raise ValueError("Microsoft Graph message has no stable ID")
    return Item.from_dict({
        "id": message_id,
        "thread_id": message.get("conversationId") or message_id,
        "occurred_at": message["receivedDateTime"],
        "source": _source(message),
        "summary": _summary(message.get("subject", ""), message.get("bodyPreview", "")),
        "status": "open",
    })


class GraphMailSource:
    """Read received mailbox messages through Graph without mutation permissions."""

    def __init__(self, credential: TokenProvider,
                 request: Callable[[str, dict[str, str]], dict[str, Any]] | None = None):
        self.credential = credential
        self.request = request or self._request

    def _request(self, url: str, headers: dict[str, str]) -> dict[str, Any]:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != "graph.microsoft.com":
            raise GraphError("refusing a Microsoft Graph pagination URL on another host")
        try:
            with urlopen(Request(url, headers=headers), timeout=30) as response:
                return json.load(response)
        except HTTPError as exc:
            raise GraphError(f"Microsoft Graph returned HTTP {exc.code}") from exc
        except URLError as exc:
            raise GraphError("Microsoft Graph is unavailable") from exc

    def read(self, start: datetime, end: datetime) -> list[Item]:
        if start.tzinfo is None or end.tzinfo is None or start >= end:
            raise ValueError("mail window must be an ordered pair of aware datetimes")
        query = urlencode({
            "$filter": f"receivedDateTime ge {_utc(start)} and receivedDateTime lt {_utc(end)}",
            "$orderby": "receivedDateTime asc",
            "$select": "id,internetMessageId,conversationId,parentFolderId,receivedDateTime,from,subject,bodyPreview",
            "$top": "100",
        })
        headers = {"Authorization": f"Bearer {self.credential.get_token()}",
                   "Accept": "application/json"}
        excluded_folder_ids = set()
        for folder in ("sentitems", "deleteditems"):
            payload = self.request(f"{GRAPH_ROOT}/me/mailFolders/{folder}?$select=id", headers)
            folder_id = payload.get("id")
            if not isinstance(folder_id, str) or not folder_id:
                raise GraphError(f"Microsoft Graph returned an invalid {folder} folder")
            excluded_folder_ids.add(folder_id)
        url = f"{GRAPH_ROOT}/me/messages?{query}"
        messages: list[dict[str, Any]] = []
        for _ in range(100):
            payload = self.request(url, headers)
            page = payload.get("value")
            if not isinstance(page, list):
                raise GraphError("Microsoft Graph returned an invalid message page")
            messages.extend(message for message in page
                            if message.get("parentFolderId") not in excluded_folder_ids)
            next_url = payload.get("@odata.nextLink")
            if not next_url:
                break
            if not isinstance(next_url, str):
                raise GraphError("Microsoft Graph returned an invalid pagination URL")
            url = next_url
        else:
            raise GraphError("Microsoft Graph pagination exceeded the safety limit")
        return [normalize_message(message) for message in messages]
