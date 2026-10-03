"""Mamourart Transport Automation - driver schedule conflict check."""

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

    return mission


def load_drivers(drivers_file: Path) -> list[dict]:
    with drivers_file.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def assign_driver(
    mission: TransportMission,
    drivers: list[dict],
    busy_drivers: set,
) -> TransportMission:

    if mission.driver:
        busy_drivers.add(
            (
                mission.driver.casefold(),
                mission.date,
            )
        )
        return mission

    for driver in drivers:
        driver_name = driver["name"].strip()
        driver_city = driver["city"].strip()
        available = driver["available"].strip().casefold() == "yes"

        same_city = (
            driver_city.casefold()
            == (mission.pickup or "").strip().casefold()
        )

        schedule_key = (
            driver_name.casefold(),
            mission.date,
        )

        already_busy = schedule_key in busy_drivers

        if same_city and available and not already_busy:
            mission.driver = driver_name
            mission.status = "Assigned"

            busy_drivers.add(schedule_key)

            print(
                f"Auto-assigned {driver_name} "
                f"to mission {mission.reference}"
            )

            return mission

        if same_city and available and already_busy:
            print(
                f"Schedule conflict: {driver_name} "
                f"is already busy on {mission.date}"
            )

    mission.status = "New"
    return mission


def main() -> None:
    base_dir = Path(__file__).parent
    emails_dir = base_dir / "emails"
    drivers_file = base_dir / "drivers.csv"
    csv_file = base_dir / "missions.csv"

    drivers = load_drivers(drivers_file)
    email_files = sorted(emails_dir.glob("*.txt"))

    missions = []
    busy_drivers = set()

    for email_file in email_files:
        email_text = email_file.read_text(encoding="utf-8")

        mission = parse_transport_email(email_text)

        mission = assign_driver(
            mission,
            drivers,
            busy_drivers,
        )

        missions.append(mission)

    with csv_file.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

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