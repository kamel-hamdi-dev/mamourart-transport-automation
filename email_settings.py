"""Resolve safe IMAP settings for Mamourart Transport Automation."""

from dataclasses import dataclass
import json
import os
from pathlib import Path


PROVIDERS = {
    "gmail": {
        "host": "imap.gmail.com",
        "port": 993,
        "auth": "app_password_or_oauth",
    },
    "outlook": {
        "host": "outlook.office365.com",
        "port": 993,
        "auth": "oauth2_required",
    },
    "ovh": {
        "host": "imap.mail.ovh.net",
        "port": 993,
        "auth": "password",
    },
    "infomaniak": {
        "host": "mail.infomaniak.com",
        "port": 993,
        "auth": "password",
    },
    "custom": {
        "host": "",
        "port": 993,
        "auth": "password",
    },
}


@dataclass(frozen=True)
class ImapSettings:
    provider: str
    host: str
    port: int
    user: str
    password: str
    mailbox: str
    search_query: str
    max_messages: int
    timeout_seconds: int


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as file:
            value = json.load(file)
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _as_int(value, default: int, minimum: int = 1, maximum: int = 10000) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return min(max(number, minimum), maximum)


def load_imap_settings(base_dir: Path | None = None) -> ImapSettings:
    base_dir = base_dir or Path(__file__).parent
    config = _read_json(base_dir / "config" / "mailbox.json")

    provider = (
        os.environ.get("MAMOURART_IMAP_PROVIDER")
        or config.get("provider")
        or "custom"
    ).strip().casefold()

    if provider not in PROVIDERS:
        raise RuntimeError(
            "Unknown email provider. Use gmail, outlook, ovh, infomaniak or custom."
        )

    preset = PROVIDERS[provider]

    if preset["auth"] == "oauth2_required":
        raise RuntimeError(
            "Microsoft Outlook/Microsoft 365 requires OAuth2/Modern Authentication. "
            "Password-only IMAP is intentionally disabled in this MVP."
        )

    host = (
        os.environ.get("MAMOURART_IMAP_HOST")
        or config.get("host")
        or preset["host"]
    ).strip()
    port = _as_int(
        os.environ.get("MAMOURART_IMAP_PORT") or config.get("port") or preset["port"],
        preset["port"],
        1,
        65535,
    )
    user = (
        os.environ.get("MAMOURART_IMAP_USER")
        or config.get("user")
        or ""
    ).strip()
    password = os.environ.get("MAMOURART_IMAP_PASSWORD", "")
    mailbox = (
        os.environ.get("MAMOURART_IMAP_MAILBOX")
        or config.get("mailbox")
        or "INBOX"
    ).strip() or "INBOX"
    search_query = (
        os.environ.get("MAMOURART_IMAP_SEARCH")
        or config.get("search")
        or "UNSEEN"
    ).strip() or "UNSEEN"
    max_messages = _as_int(
        os.environ.get("MAMOURART_IMAP_MAX_MESSAGES")
        or config.get("max_messages")
        or 50,
        50,
        1,
        500,
    )
    timeout_seconds = _as_int(
        os.environ.get("MAMOURART_IMAP_TIMEOUT") or 30,
        30,
        5,
        120,
    )

    if not host:
        raise RuntimeError("Missing IMAP host. Configure config/mailbox.json or MAMOURART_IMAP_HOST.")
    if not user:
        raise RuntimeError("Missing mailbox email/username.")
    if not password:
        raise RuntimeError(
            "Missing mailbox secret. Set MAMOURART_IMAP_PASSWORD only in the local process/environment."
        )

    return ImapSettings(
        provider=provider,
        host=host,
        port=port,
        user=user,
        password=password,
        mailbox=mailbox,
        search_query=search_query,
        max_messages=max_messages,
        timeout_seconds=timeout_seconds,
    )
