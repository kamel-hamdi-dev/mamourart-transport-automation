"""Mamourart Transport Automation - mission assignment and approval workflow.

The assignment engine reads missions.csv as the source of truth. Email ingestion is
handled separately by email_import.py, so imported missions are never deleted by
running the assignment engine.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import csv


MISSION_FIELDS = [
    "reference",
    "pickup",
    "delivery",
    "date",
    "driver",
    "proposed_driver",
    "status",
    "distance_km",
]

APPROVAL_FIELDS = [
    "reference",
    "proposed_driver",
    "reason",
    "distance_km",
    "decision",
    "rejected_drivers",
]


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

    @classmethod
    def from_row(cls, row: dict):
        distance = row.get("distance_km", "")
        try:
            distance_value = int(distance) if str(distance).strip() else None
        except ValueError:
            distance_value = None

        return cls(
            reference=(row.get("reference") or "").strip() or None,
            pickup=(row.get("pickup") or "").strip() or None,
            delivery=(row.get("delivery") or "").strip() or None,
            date=(row.get("date") or "").strip() or None,
            driver=(row.get("driver") or "").strip() or None,
            proposed_driver=(row.get("proposed_driver") or "").strip() or None,
            status=(row.get("status") or "New").strip() or "New",
            distance_km=distance_value,
        )

    def to_row(self):
        return {
            "reference": self.reference or "",
            "pickup": self.pickup or "",
            "delivery": self.delivery or "",
            "date": self.date or "",
            "driver": self.driver or "",
            "proposed_driver": self.proposed_driver or "",
            "status": self.status,
            "distance_km": "" if self.distance_km is None else self.distance_km,
        }


def load_csv(file_path: Path) -> list[dict]:
    if not file_path.exists():
        return []
    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(file_path: Path, rows: list[dict], fields: list[str]) -> None:
    with file_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def get_distance(from_city, to_city, distances):
    if not from_city or not to_city:
        return None
    if from_city.casefold() == to_city.casefold():
        return 0
    for row in distances:
        if (
            row.get("from_city", "").strip().casefold() == from_city.casefold()
            and row.get("to_city", "").strip().casefold() == to_city.casefold()
        ):
            try:
                return int(row.get("distance_km", ""))
            except ValueError:
                return None
    return None


def get_driver_city(driver_name, drivers):
    if not driver_name:
        return None
    for driver in drivers:
        if driver.get("name", "").strip().casefold() == driver_name.casefold():
            return driver.get("city", "").strip() or None
    return None


def driver_is_free(driver_name, mission_date, busy_drivers):
    return (driver_name.casefold(), mission_date or "") not in busy_drivers


def reserve_driver(driver_name, mission_date, busy_drivers):
    if driver_name:
        busy_drivers.add((driver_name.casefold(), mission_date or ""))


def is_excluded(driver_name, excluded_drivers):
    return any(driver_name.casefold() == name.casefold() for name in excluded_drivers)


def parse_rejected_drivers(value):
    if not value:
        return []
    return [name.strip() for name in value.split(";") if name.strip()]


def add_rejected_driver(rejected_drivers, driver_name):
    if driver_name and not is_excluded(driver_name, rejected_drivers):
        rejected_drivers.append(driver_name)


def propose_driver(mission, drivers, distances, busy_drivers, excluded_drivers=None):
    excluded_drivers = excluded_drivers or []
    pickup_city = (mission.pickup or "").strip()

    for driver in drivers:
        name = driver.get("name", "").strip()
        city = driver.get("city", "").strip()
        available = driver.get("available", "").strip().casefold() == "yes"
        if not name or not available or is_excluded(name, excluded_drivers):
            continue
        if city.casefold() != pickup_city.casefold():
            continue
        if not driver_is_free(name, mission.date, busy_drivers):
            continue

        mission.proposed_driver = name
        mission.status = "Proposed"
        mission.distance_km = 0
        reserve_driver(name, mission.date, busy_drivers)
        return mission, "Local available driver"

    candidates = []
    for driver in drivers:
        name = driver.get("name", "").strip()
        city = driver.get("city", "").strip()
        available = driver.get("available", "").strip().casefold() == "yes"
        if not name or not available or is_excluded(name, excluded_drivers):
            continue
        if not driver_is_free(name, mission.date, busy_drivers):
            continue
        distance = get_distance(pickup_city, city, distances)
        if distance is not None:
            candidates.append((distance, name))

    if candidates:
        distance, name = min(candidates, key=lambda item: item[0])
        mission.proposed_driver = name
        mission.status = "Proposed"
        mission.distance_km = distance
        reserve_driver(name, mission.date, busy_drivers)
        return mission, "Nearest available driver"

    mission.proposed_driver = None
    mission.distance_km = None
    mission.status = "Needs Review"
    return mission, "No alternative driver available"


def approval_row(mission, reason, decision, rejected_drivers):
    return {
        "reference": mission.reference or "",
        "proposed_driver": mission.proposed_driver or mission.driver or "",
        "reason": reason,
        "distance_km": "" if mission.distance_km is None else mission.distance_km,
        "decision": decision,
        "rejected_drivers": ";".join(rejected_drivers),
    }


def main():
    base_dir = Path(__file__).parent
    drivers_file = base_dir / "drivers.csv"
    distances_file = base_dir / "distances.csv"
    missions_file = base_dir / "data" / "missions.csv"
    approvals_file = base_dir / "data" / "approvals.csv"

    drivers = load_csv(drivers_file)
    distances = load_csv(distances_file)
    mission_rows = load_csv(missions_file)
    existing_approvals = load_csv(approvals_file)

    approvals_by_reference = {
        row.get("reference", "").strip(): row
        for row in existing_approvals
        if row.get("reference", "").strip()
    }

    missions = [TransportMission.from_row(row) for row in mission_rows]
    output_approvals = []
    busy_drivers = set()

    # Reserve already-finalized assignments first so new proposals do not conflict.
    for mission in missions:
        if mission.driver and mission.status.casefold() in {"assigned", "approved"}:
            reserve_driver(mission.driver, mission.date, busy_drivers)

    for mission in missions:
        reference = mission.reference or ""
        existing = approvals_by_reference.get(reference)
        status = mission.status.casefold()

        # Existing final assignment: keep it exactly as-is.
        if mission.driver and status in {"assigned", "approved"}:
            if existing:
                output_approvals.append(existing)
            continue

        # Missing core data must never be auto-assigned.
        if not mission.reference or not mission.pickup or not mission.delivery or not mission.date:
            mission.status = "Needs Review"
            if existing:
                output_approvals.append(existing)
            continue

        if not existing:
            mission, reason = propose_driver(mission, drivers, distances, busy_drivers)
            if mission.proposed_driver:
                output_approvals.append(approval_row(mission, reason, "Pending", []))
            continue

        decision = existing.get("decision", "").strip().casefold()
        rejected = parse_rejected_drivers(existing.get("rejected_drivers", ""))

        if decision == "approved":
            approved_driver = existing.get("proposed_driver", "").strip()
            if approved_driver:
                mission.driver = approved_driver
                mission.proposed_driver = None
                mission.status = "Approved"
                distance_value = existing.get("distance_km", "").strip()
                if distance_value:
                    try:
                        mission.distance_km = int(distance_value)
                    except ValueError:
                        pass
                reserve_driver(approved_driver, mission.date, busy_drivers)
            output_approvals.append(existing)

        elif decision == "pending":
            proposed = existing.get("proposed_driver", "").strip()
            mission.proposed_driver = proposed or None
            mission.status = "Proposed" if proposed else "Needs Review"
            distance_value = existing.get("distance_km", "").strip()
            if distance_value:
                try:
                    mission.distance_km = int(distance_value)
                except ValueError:
                    pass
            if proposed:
                reserve_driver(proposed, mission.date, busy_drivers)
            output_approvals.append(existing)

        elif decision == "rejected":
            rejected_driver = existing.get("proposed_driver", "").strip()
            add_rejected_driver(rejected, rejected_driver)
            mission.proposed_driver = None
            mission, reason = propose_driver(
                mission, drivers, distances, busy_drivers, rejected
            )
            if mission.proposed_driver:
                output_approvals.append(approval_row(mission, reason, "Pending", rejected))
            else:
                output_approvals.append(approval_row(mission, reason, "Rejected", rejected))

        else:
            mission.status = "Needs Review"
            output_approvals.append(existing)

    write_csv(missions_file, [mission.to_row() for mission in missions], MISSION_FIELDS)
    write_csv(approvals_file, output_approvals, APPROVAL_FIELDS)

    print(f"Processed {len(missions)} missions from missions.csv.")
    print(f"Approval records: {len(output_approvals)}")


if __name__ == "__main__":
    main()
