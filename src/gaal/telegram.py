from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import Notification


class TelegramError(RuntimeError):
    pass


def _post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = Request(url, data=json.dumps(payload).encode("utf-8"),
                      headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
    except HTTPError as exc:
        raise TelegramError(f"Telegram returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise TelegramError("Telegram is unavailable") from exc
    if not isinstance(result, dict) or result.get("ok") is not True:
        raise TelegramError("Telegram rejected the message")
    return result


class TelegramBotDestination:
    def __init__(self, *, token: str, chat_id: str,
                 request: Callable[[str, dict[str, Any]], dict[str, Any]] = _post):
        if not token or not chat_id:
            raise ValueError("Telegram token and chat ID must be non-empty")
        self._token, self._chat_id, self._request = token, chat_id, request
        digest = hashlib.sha256(chat_id.encode("utf-8")).hexdigest()[:12]
        self.name = f"telegram:{digest}"

    def deliver(self, notification: Notification, *, dry_run: bool) -> None:
        if dry_run:
            return
        if not 1 <= len(notification.body) <= 4096:
            raise TelegramError("Telegram briefing must fit in one message")
        self._request(f"https://api.telegram.org/bot{self._token}/sendMessage", {
            "chat_id": self._chat_id,
            "text": notification.body,
            "link_preview_options": {"is_disabled": True},
        })
