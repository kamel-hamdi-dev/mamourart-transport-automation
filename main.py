"""Mamourart Transport Automation - first Python prototype."""

from dataclasses import asdict, dataclass
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
    sample_email = """
Subject: New transport mission
Reference: TR-1001
Pickup: Paris
Delivery: Lyon
Date: 2026-10-04
Driver: Ahmed
"""

    mission = parse_transport_email(sample_email)

    print("Extracted transport mission:")
    for key, value in asdict(mission).items():
        print(f"- {key}: {value}")
if __name__ == "__main__":
    main()
