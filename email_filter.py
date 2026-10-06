"""Sender authorization rules for transport emails."""

import json
from pathlib import Path


def load_authorized_clients(config_path: Path) -> dict:
    if not config_path.exists():
        return {"authorized_senders": [], "authorized_domains": []}

    with config_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return {
        "authorized_senders": [
            item.strip().casefold()
            for item in data.get("authorized_senders", [])
            if item.strip()
        ],
        "authorized_domains": [
            item.strip().lstrip("@").casefold()
            for item in data.get("authorized_domains", [])
            if item.strip()
        ],
    }


def sender_is_authorized(sender: str, rules: dict) -> bool:
    sender = (sender or "").strip().casefold()
    if not sender or "@" not in sender:
        return False

    if sender in rules.get("authorized_senders", []):
        return True

    domain = sender.rsplit("@", 1)[1]
    return domain in rules.get("authorized_domains", [])
