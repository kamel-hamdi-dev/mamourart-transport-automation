"""Mamourart Transport Automation - export missions with status."""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional
import csv
import re


@dataclass
class TransportMission:
    reference: Optional[str] = None
    pickup: Optional[str] = None
    delivery: Optional[str] = None
    date: Optional[str] = None
    driver: Optional[str] = None
    status: str = "New"


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

    mission = TransportMission(**values)

    if mission.driver:
        mission.status = "Assigned"
    else:
        mission.status = "New"

    return mission


def main() -> None:
    base_dir = Path(__file__).parent
    emails_dir = base_dir / "emails"
    csv_file = base_dir / "missions.csv"

    email_files = sorted(emails_dir.glob("*.txt"))
    missions = []

    for email_file in email_files:
        email_text = email_file.read_text(encoding="utf-8")
        mission = parse_transport_email(email_text)
        missions.append(mission)

    with csv_file.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "reference",
                "pickup",
                "delivery",
                "date",
                "driver",
                "status",
            ],
        )

        writer.writeheader()

        for mission in missions:
            writer.writerow(asdict(mission))

    print(f"Processed {len(missions)} transport missions.")
    print(f"CSV created: {csv_file}")


if __name__ == "__main__":
    main()