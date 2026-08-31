from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime

from .adapters import JsonFileSource, StdoutDestination
from .config import load_microsoft365, load_reasoning, load_schedule, load_telegram
from .microsoft365 import DeviceCodeCredential, GraphMailSource
from .store import SQLiteStore
from .workflow import WorkflowFailure, run_daily
from .reasoning import ReasoningError, make_reasoning_provider
from .secrets import resolve_secret
from .telegram import TelegramBotDestination


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="gaal", description="Standalone Gaal briefings")
    commands = root.add_subparsers(dest="command", required=True)
    daily = commands.add_parser("daily", help="generate a deterministic daily briefing")
    daily.add_argument("--config", required=True)
    source = daily.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", help="normalized JSON fixture")
    source.add_argument("--microsoft365", action="store_true", help="read the configured Inbox")
    daily.add_argument("--date", required=True, help="scheduled local date")
    daily.add_argument("--run-at", required=True, help="offset-aware actual run time")
    daily.add_argument("--state", required=True, help="SQLite state database")
    daily.add_argument("--deliver-telegram", action="store_true",
                       help="explicitly deliver to the configured Telegram chat")
    audit = commands.add_parser("last-run", help="print the most recent audit record")
    audit.add_argument("--state", required=True)
    auth = commands.add_parser("auth-microsoft365", help="sign in with delegated Mail.Read access")
    auth.add_argument("--config", required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "last-run":
            store = SQLiteStore(args.state)
            print(json.dumps(store.last_run(), indent=2))
            return 0
        if args.command == "auth-microsoft365":
            settings = load_microsoft365(args.config)
            credential = DeviceCodeCredential(client_id=settings.client_id,
                                              tenant_id=settings.tenant_id,
                                              cache_path=settings.token_cache)
            credential.get_token(interactive=True)
            print("Microsoft 365 authentication is ready.")
            return 0
        store = SQLiteStore(args.state)
        if args.microsoft365:
            settings = load_microsoft365(args.config)
            source = GraphMailSource(DeviceCodeCredential(
                client_id=settings.client_id, tenant_id=settings.tenant_id,
                cache_path=settings.token_cache,
            ))
        else:
            source = JsonFileSource(args.input)
        run_at = datetime.fromisoformat(args.run_at)
        if run_at.tzinfo is None or run_at.utcoffset() is None:
            raise ValueError("run-at must include a UTC offset")
        if args.deliver_telegram:
            telegram = load_telegram(args.config)
            chat_id = telegram.chat_id or resolve_secret(
                env_name=telegram.chat_id_env,
                keychain_service=telegram.chat_id_keychain_service,
                keychain_account=telegram.chat_id_keychain_account,
            )
            destination = TelegramBotDestination(
                token=resolve_secret(env_name=telegram.token_env,
                                     keychain_service=telegram.keychain_service,
                                     keychain_account=telegram.keychain_account),
                chat_id=chat_id,
            )
        else:
            destination = StdoutDestination(sys.stdout.write)
        run_daily(scheduled_date=date.fromisoformat(args.date), actual_run_time=run_at,
                  schedule=load_schedule(args.config), source=source,
                  destination=destination, store=store,
                  dry_run=not args.deliver_telegram,
                  reasoning=make_reasoning_provider(load_reasoning(args.config)))
    except (OSError, ValueError, WorkflowFailure) as exc:
        detail = exc.__cause__ if isinstance(exc, WorkflowFailure) else None
        suffix = f": {detail}" if isinstance(detail, ReasoningError) else ""
        print(f"gaal: {exc}{suffix}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
