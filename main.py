"""Mamourart Transport Automation - approval workflow."""

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
    proposed_driver: Optional[str] = None
    status: str = "New"
    distance_km: Optional[int] = None


FIELD_PATTERNS = {
    "reference": r"^Reference\s*:\s*(.+)$",
    "pickup": r"^Pickup\s*:\s*(.+)$",
    "delivery": r"^Delivery\s*:\s*(.+)$",
    "date": r"^Date\s*:\s*(.+)$",
    "driver": r"^Driver\s*:\s*(.+)$",
}


def extract_field(email_text, pattern):
    match = re.search(
        pattern,
        email_text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    return match.group(1).strip() if match else None


def parse_transport_email(email_text):
    values = {
        field: extract_field(email_text, pattern)
        for field, pattern in FIELD_PATTERNS.items()
    }

    mission = TransportMission(**values)

    if mission.driver:
        mission.status = "Assigned"

    return mission


def load_csv(file_path):
    if not file_path.exists():
        return []

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def get_distance(from_city, to_city, distances):
    if from_city.casefold() == to_city.casefold():
        return 0

    for row in distances:
        if (
            row["from_city"].strip().casefold()
            == from_city.casefold()
            and row["to_city"].strip().casefold()
            == to_city.casefold()
        ):
            return int(row["distance_km"])

    return None


def get_driver_city(driver_name, drivers):
    for driver in drivers:
        if (
            driver["name"].strip().casefold()
            == driver_name.strip().casefold()
        ):
            return driver["city"].strip()

    return None


def driver_is_free(driver_name, mission_date, busy_drivers):
    return (
        driver_name.casefold(),
        mission_date,
    ) not in busy_drivers


def reserve_driver(driver_name, mission_date, busy_drivers):
    busy_drivers.add(
        (
            driver_name.casefold(),
            mission_date,
        )
    )


def apply_existing_approval(
    mission,
    approval,
    drivers,
    distances,
    busy_drivers,
):
    proposed_driver = approval["proposed_driver"].strip()
    decision = approval["decision"].strip().casefold()

    mission.proposed_driver = proposed_driver

    if approval.get("distance_km"):
        mission.distance_km = int(approval["distance_km"])

    if decision == "approved":
        mission.driver = proposed_driver
        mission.proposed_driver = None
        mission.status = "Approved"

        reserve_driver(
            mission.driver,
            mission.date,
            busy_drivers,
        )

        print(
            f"Approved assignment: "
            f"{mission.driver} -> {mission.reference}"
        )

        return mission

    mission.status = "Proposed"

    reserve_driver(
        proposed_driver,
        mission.date,
        busy_drivers,
    )

    return mission


def propose_driver(
    mission,
    drivers,
    distances,
    busy_drivers,
):
    pickup_city = (mission.pickup or "").strip()

    if mission.driver:
        driver_city = get_driver_city(
            mission.driver,
            drivers,
        )

        if driver_city:
            mission.distance_km = get_distance(
                pickup_city,
                driver_city,
                distances,
            )

        reserve_driver(
            mission.driver,
            mission.date,
            busy_drivers,
        )

        return mission, "Driver provided in email"

    # Local driver first
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
            mission.proposed_driver = driver_name
            mission.status = "Proposed"
            mission.distance_km = 0

            reserve_driver(
                driver_name,
                mission.date,
                busy_drivers,
            )

            return mission, "Local available driver"

    # Nearest available driver
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

        mission.proposed_driver = driver_name
        mission.status = "Proposed"
        mission.distance_km = distance

        reserve_driver(
            driver_name,
            mission.date,
            busy_drivers,
        )

        return mission, "Nearest available driver"

    mission.status = "New"
    return mission, "No available driver"


def main():
    base_dir = Path(__file__).parent

    emails_dir = base_dir / "emails"
    drivers_file = base_dir / "drivers.csv"
    distances_file = base_dir / "distances.csv"
    missions_file = base_dir / "missions.csv"
    approvals_file = base_dir / "approvals.csv"

    drivers = load_csv(drivers_file)
    distances = load_csv(distances_file)

    existing_approvals = load_csv(approvals_file)

    approvals_by_reference = {
        row["reference"].strip(): row
        for row in existing_approvals
    }

    email_files = sorted(
        emails_dir.glob("*.txt")
    )

    missions = []
    approvals = []
    busy_drivers = set()

    for email_file in email_files:
        email_text = email_file.read_text(
            encoding="utf-8"
        )

        mission = parse_transport_email(email_text)

        # Mission already has a driver from the email
        if mission.driver:
            mission, reason = propose_driver(
                mission,
                drivers,
                distances,
                busy_drivers,
            )

        # Existing human decision
        elif mission.reference in approvals_by_reference:
            approval = approvals_by_reference[
                mission.reference
            ]

            mission = apply_existing_approval(
                mission,
                approval,
                drivers,
                distances,
                busy_drivers,
            )

            reason = approval["reason"]

            approvals.append(approval)

        # New mission requiring proposal
        else:
            mission, reason = propose_driver(
                mission,
                drivers,
                distances,
                busy_drivers,
            )

            if mission.status == "Proposed":
                approval = {
                    "reference": mission.reference,
                    "proposed_driver": (
                        mission.proposed_driver
                    ),
                    "reason": reason,
                    "distance_km": (
                        mission.distance_km
                    ),
                    "decision": "Pending",
                }

                approvals.append(approval)

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
                "proposed_driver",
                "status",
                "distance_km",
            ],
        )

        writer.writeheader()

        for mission in missions:
            writer.writerow(asdict(mission))

    with approvals_file.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "reference",
                "proposed_driver",
                "reason",
                "distance_km",
                "decision",
            ],
        )

        writer.writeheader()
        writer.writerows(approvals)

    print(
        f"Processed {len(missions)} missions."
    )

    print(
        f"Approval records: {len(approvals)}"
    )


if __name__ == "__main__":
    main()