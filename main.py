"""Mamourart Transport Automation - first Python prototype."""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional
import re


@dataclass
class TransportMission:
    reference: Optional[str] = None
    pickup: Optional[str] = None
    delivery: Optional[str] = None
    date: Optional[str] = None
    driver: Optional[str] = None


FIELD_PATTERNS = {
    "reference": r"^Reference\s*:\s*(.+)$",
    "pickup": r"^Pickup\s*:\s*(.+)$",
    "delivery": r"^Delivery\s*:\s*(.+)$",
    "date": r"^Date\s*:\s*(.+)$",
    "driver": r"^Driver\s*:\s*(.+)$",
}


def extract_field(email_text: str, pattern: str) -> Optional[str]:
    match = re.search(
        pattern,
        email_text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    return match.group(1).strip() if match else None


def parse_transport_email(email_text: str) -> TransportMission:
    values = {
        field: extract_field(email_text, pattern)
        for field, pattern in FIELD_PATTERNS.items()
    }
    return TransportMission(**values)


def main() -> None:
    email_file = Path(__file__).with_name("sample_email.txt")

    email_text = email_file.read_text(encoding="utf-8")
    mission = parse_transport_email(email_text)

    print("Extracted transport mission:")
    for key, value in asdict(mission).items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()