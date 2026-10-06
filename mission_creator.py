"""Append validated email missions to missions.csv without overwriting existing missions."""

from dataclasses import asdict
from pathlib import Path
import csv

from email_parser import ParsedMission


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


def load_missions(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def reference_exists(path: Path, reference: str) -> bool:
    target = (reference or "").strip().casefold()
    return any(
        row.get("reference", "").strip().casefold() == target
        for row in load_missions(path)
    )


def append_mission(path: Path, mission: ParsedMission) -> bool:
    if reference_exists(path, mission.reference or ""):
        return False

    row = {
        "reference": mission.reference or "",
        "pickup": mission.pickup or "",
        "delivery": mission.delivery or "",
        "date": mission.date or "",
        "driver": mission.driver or "",
        "proposed_driver": "",
        "status": "New" if not mission.driver else "Assigned",
        "distance_km": "",
    }

    file_exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=MISSION_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    return True
