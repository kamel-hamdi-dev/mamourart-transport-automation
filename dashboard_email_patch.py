"""Helpers for safely importing emails from the dashboard."""

import json
import os
from pathlib import Path
import subprocess
import sys


BASE_DIR = Path(__file__).parent
EMAIL_IMPORT_FILE = BASE_DIR / "email_import.py"
MAILBOX_CONFIG = BASE_DIR / "config" / "mailbox.json"


def _mailbox_config():
    if not MAILBOX_CONFIG.exists():
        return {}

    try:
        with MAILBOX_CONFIG.open("r", encoding="utf-8") as file:
            value = json.load(file)
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def mailbox_is_configured():
    config = _mailbox_config()
    return bool(str(config.get("user", "")).strip())


def run_email_import(secret=None):
    env = os.environ.copy()

    if mailbox_is_configured():
        env["MAMOURART_EMAIL_SOURCE"] = "imap"

        if secret:
            env["MAMOURART_IMAP_PASSWORD"] = secret
    else:
        env["MAMOURART_EMAIL_SOURCE"] = "local"

    try:
        result = subprocess.run(
            [sys.executable, str(EMAIL_IMPORT_FILE)],
            cwd=BASE_DIR,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        return (
            result.returncode == 0,
            result.stdout.strip(),
            result.stderr.strip(),
        )

    except Exception as error:
        return False, "", str(error)