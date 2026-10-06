"""Parse transport mission data from an email body."""

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Optional


@dataclass
class ParsedMission:
    reference: Optional[str] = None
    pickup: Optional[str] = None
    delivery: Optional[str] = None
    date: Optional[str] = None
    driver: Optional[str] = None


FIELD_PATTERNS = {
    "reference": r"^\s*(?:Reference|Ref)\s*:\s*(.+?)\s*$",
    "pickup": r"^\s*(?:Pickup|Loading|From)\s*:\s*(.+?)\s*$",
    "delivery": r"^\s*(?:Delivery|Unloading|To)\s*:\s*(.+?)\s*$",
    "date": r"^\s*(?:Date|Pickup Date|Loading Date)\s*:\s*(.+?)\s*$",
    "driver": r"^\s*Driver\s*:\s*(.+?)\s*$",
}


def _extract(text: str, pattern: str) -> Optional[str]:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def _normalize_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    value = value.strip()
    formats = (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
    )

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return value


def parse_transport_email(text: str) -> ParsedMission:
    values = {
        field: _extract(text, pattern)
        for field, pattern in FIELD_PATTERNS.items()
    }
    values["date"] = _normalize_date(values.get("date"))
    return ParsedMission(**values)


def validate_mission(mission: ParsedMission) -> list[str]:
    required = ("reference", "pickup", "delivery", "date")
    return [field for field in required if not getattr(mission, field)]
