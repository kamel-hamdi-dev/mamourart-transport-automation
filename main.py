"""Mamourart Transport Automation - nearest available driver assignment."""

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


def load_csv(file_path: Path) -> list[dict]:
    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def get_distance(
    from_city: str,
    to_city: str,
    distances: list[dict],
) -> Optional[int]:

    if from_city.casefold() == to_city.casefold():
        return 0

    for row in distances:
        if (
            row["from_city"].strip().casefold() == from_city.casefold()
            and row["to_city"].strip().casefold() == to_city.casefold()
        ):
            return int(row["distance_km"])

    return None


def driver_is_free(
    driver_name: str,
    mission_date: Optional[str],
    busy_drivers: set,
) -> bool:

    key = (
        driver_name.casefold(),
        mission_date,
    )

    return key not in busy_drivers


def reserve_driver(
    driver_name: str,
    mission_date: Optional[str],
    busy_drivers: set,
) -> None:

    busy_drivers.add(
        (
            driver_name.casefold(),
            mission_date,
        )
    )


def assign_driver(
    mission: TransportMission,
    drivers: list[dict],
    distances: list[dict],
    busy_drivers: set,
) -> TransportMission:

    # Driver already specified in the email
    if mission.driver:
        reserve_driver(
            mission.driver,
            mission.date,
            busy_drivers,
        )
        return mission

    pickup_city = (mission.pickup or "").strip()

    # 1. Prefer a free driver in the same city
    for driver in drivers:
        driver_name = driver["name"].strip()
        driver_city = driver["city"].strip()

        available = (
            driver["available"].strip().casefold() == "yes"
        )

        same_city = (
            driver_city.casefold()
            == pickup_city.casefold()
        )

        free = driver_is_free(
            driver_name,
            mission.date,
            busy_drivers,
        )

        if available and same_city and free:
            mission.driver = driver_name
            mission.status = "Assigned"

            reserve_driver(
                driver_name,
                mission.date,
                busy_drivers,
            )

            print(
                f"Local driver assigned: {driver_name} "
                f"to mission {mission.reference}"
            )

            return mission

    # 2. Find the nearest free driver
    candidates = []

    for driver in drivers:
        driver_name = driver["name"].strip()
        driver_city = driver["city"].strip()

        available = (
            driver["available"].strip().casefold() == "yes"
        )

        free = driver_is_free(
            driver_name,
            mission.date,
            busy_drivers,
        )

        if not available or not free:
            continue

        distance = get_distance(
            pickup_city,
            driver_city,
            distances,
        )

        if distance is not None:
            candidates.append(
                (
                    distance,
                    driver_name,
                    driver_city,
                )
            )

    if candidates:
        candidates.sort(key=lambda item: item[0])

        distance, driver_name, driver_city = candidates[0]

        mission.driver = driver_name
        mission.status = "Assigned"

        reserve_driver(
            driver_name,
            mission.date,
            busy_drivers,
        )

        print(
            f"Nearest driver assigned: {driver_name} "
            f"from {driver_city} "
            f"({distance} km) "
            f"to mission {mission.reference}"
        )

        return mission

    print(
        f"No available driver for mission "
        f"{mission.reference}"
    )

    mission.status = "New"
    return mission


def main() -> None:
    base_dir = Path(__file__).parent

    emails_dir = base_dir / "emails"
    drivers_file = base_dir / "drivers.csv"
    distances_file = base_dir / "distances.csv"
    missions_file = base_dir / "missions.csv"

    drivers = load_csv(drivers_file)
    distances = load_csv(distances_file)

    email_files = sorted(
        emails_dir.glob("*.txt")
    )

    missions = []
    busy_drivers = set()

    for email_file in email_files:
        email_text = email_file.read_text(
            encoding="utf-8"
        )

        mission = parse_transport_email(email_text)

        mission = assign_driver(
            mission,
            drivers,
            distances,
            busy_drivers,
        )

        missions.append(mission)

    with missions_file.open(
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
            writer.writerow(
                asdict(mission)
            )

    print(
        f"Processed {len(missions)} transport missions."
    )
    print(
        f"CSV created: {missions_file}"
    )


if __name__ == "__main__":
    main()