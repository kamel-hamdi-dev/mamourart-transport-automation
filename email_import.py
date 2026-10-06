"""Mamourart Email Integration V1: authorized email -> validated mission -> missions.csv."""

import json
import os
from pathlib import Path

from email_filter import load_authorized_clients, sender_is_authorized
from email_parser import parse_transport_email, validate_mission
from email_reader import read_messages
from mission_creator import append_mission


BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config" / "clients.json"
PROCESSED_FILE = BASE_DIR / "data" / "processed_emails.json"
INBOX_DIR = BASE_DIR / "inbox"
MISSIONS_FILE = BASE_DIR / "data" / "missions.csv"


def load_processed_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        with path.open("r", encoding="utf-8") as file:
            values = json.load(file)
        return {str(value) for value in values}
    except (json.JSONDecodeError, OSError):
        return set()


def save_processed_ids(path: Path, values: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(sorted(values), file, indent=2)


def import_emails(source: str | None = None) -> dict:
    source = source or os.environ.get("MAMOURART_EMAIL_SOURCE", "local")
    rules = load_authorized_clients(CONFIG_FILE)
    processed = load_processed_ids(PROCESSED_FILE)

    stats = {
        "seen": 0,
        "imported": 0,
        "unauthorized": 0,
        "invalid": 0,
        "duplicate": 0,
        "already_processed": 0,
    }

    for message in read_messages(source, INBOX_DIR):
        stats["seen"] += 1

        if message.message_id in processed:
            stats["already_processed"] += 1
            continue

        if not sender_is_authorized(message.sender, rules):
            stats["unauthorized"] += 1
            processed.add(message.message_id)
            continue

        mission = parse_transport_email(message.body)
        missing = validate_mission(mission)
        if missing:
            stats["invalid"] += 1
            processed.add(message.message_id)
            print(
                f"Needs Review: {message.subject or message.message_id} "
                f"(missing: {', '.join(missing)})"
            )
            continue

        if append_mission(MISSIONS_FILE, mission):
            stats["imported"] += 1
            print(
                f"Imported mission {mission.reference}: "
                f"{mission.pickup} -> {mission.delivery}"
            )
        else:
            stats["duplicate"] += 1
            print(f"Duplicate mission ignored: {mission.reference}")

        processed.add(message.message_id)

    save_processed_ids(PROCESSED_FILE, processed)
    return stats


def main():
    stats = import_emails()
    print(
        "Email import completed: "
        f"seen={stats['seen']}, imported={stats['imported']}, "
        f"duplicates={stats['duplicate']}, invalid={stats['invalid']}, "
        f"unauthorized={stats['unauthorized']}, "
        f"already_processed={stats['already_processed']}"
    )


if __name__ == "__main__":
    main()
