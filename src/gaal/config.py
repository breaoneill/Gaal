from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import time
from pathlib import Path

from .schedule import DAY_NUMBERS, WorkSchedule


@dataclass(frozen=True)
class Microsoft365Settings:
    client_id: str
    tenant_id: str
    token_cache: Path


@dataclass(frozen=True)
class ReasoningSettings:
    provider: str = "disabled"
    model: str | None = None
    endpoint: str | None = None
    api_key_env: str = "OPENAI_API_KEY"
    keychain_service: str | None = None
    keychain_account: str | None = None


@dataclass(frozen=True)
class TelegramSettings:
    chat_id: str | None = None
    chat_id_env: str = "TELEGRAM_CHAT_ID"
    chat_id_keychain_service: str | None = None
    chat_id_keychain_account: str | None = None
    token_env: str = "TELEGRAM_BOT_TOKEN"
    keychain_service: str | None = None
    keychain_account: str | None = None


def load_schedule(path: str | Path) -> WorkSchedule:
    with Path(path).open("rb") as handle:
        root = tomllib.load(handle)
    try:
        work = root["work"]
        days = tuple(work["days"])
        schedule = WorkSchedule(
            timezone=work["timezone"], days=days,
            start=time.fromisoformat(work["start"]),
            finish=time.fromisoformat(work["finish"]),
        )
        schedule.zone
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid work schedule: {exc}") from exc
    if not days or any(day not in DAY_NUMBERS for day in days):
        raise ValueError("invalid work schedule days")
    if schedule.start >= schedule.finish:
        raise ValueError("work start must be before finish")
    return schedule


def load_microsoft365(path: str | Path) -> Microsoft365Settings:
    with Path(path).open("rb") as handle:
        root = tomllib.load(handle)
    try:
        values = root["microsoft365"]
        settings = Microsoft365Settings(
            client_id=values["client_id"].strip(),
            tenant_id=values["tenant_id"].strip(),
            token_cache=Path(values["token_cache"]).expanduser(),
        )
    except (AttributeError, KeyError, TypeError) as exc:
        raise ValueError(f"invalid Microsoft 365 configuration: {exc}") from exc
    if not settings.client_id or not settings.tenant_id:
        raise ValueError("Microsoft 365 client_id and tenant_id must be non-empty")
    return settings


def load_reasoning(path: str | Path) -> ReasoningSettings:
    with Path(path).open("rb") as handle:
        root = tomllib.load(handle)
    values = root.get("reasoning", {})
    try:
        provider = values.get("provider", "disabled").strip().lower()
        settings = ReasoningSettings(
            provider=provider,
            model=values.get("model"),
            endpoint=values.get("endpoint"),
            api_key_env=values.get("api_key_env", "OPENAI_API_KEY"),
            keychain_service=values.get("keychain_service"),
            keychain_account=values.get("keychain_account"),
        )
    except (AttributeError, TypeError) as exc:
        raise ValueError(f"invalid reasoning configuration: {exc}") from exc
    if provider not in {"disabled", "ollama", "openai"}:
        raise ValueError(f"unsupported reasoning provider: {provider}")
    if provider != "disabled" and not settings.model:
        raise ValueError(f"reasoning model is required for {provider}")
    return settings


def load_telegram(path: str | Path) -> TelegramSettings:
    with Path(path).open("rb") as handle:
        root = tomllib.load(handle)
    try:
        values = root["telegram"]
        settings = TelegramSettings(
            chat_id=str(values["chat_id"]).strip() if "chat_id" in values else None,
            chat_id_env=values.get("chat_id_env", "TELEGRAM_CHAT_ID"),
            chat_id_keychain_service=values.get("chat_id_keychain_service"),
            chat_id_keychain_account=values.get("chat_id_keychain_account"),
            token_env=values.get("token_env", "TELEGRAM_BOT_TOKEN"),
            keychain_service=values.get("keychain_service"),
            keychain_account=values.get("keychain_account"),
        )
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f"invalid Telegram configuration: {exc}") from exc
    if settings.chat_id is not None and not settings.chat_id:
        raise ValueError("Telegram chat_id must be non-empty")
    if settings.chat_id is None and not settings.chat_id_keychain_service:
        raise ValueError("Telegram chat ID or Keychain service is required")
    return settings
