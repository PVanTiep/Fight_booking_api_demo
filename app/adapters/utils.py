from __future__ import annotations

from datetime import datetime, timezone, timedelta
from math import ceil
from typing import Any


def first_value(source: dict[str, Any] | None, *keys: str, default: Any = None) -> Any:
    if not isinstance(source, dict):
        return default
    for key in keys:
        value = source.get(key)
        if value is not None and value != "":
            return value
    return default


def nested(source: dict[str, Any] | None, *keys: str, default: Any = None) -> Any:
    current: Any = source
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, str) and value.upper().rstrip().endswith("KG"):
        value = value.upper().rstrip()[:-2].rstrip()
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def fixed_timezone(offset_hours: float | int | None) -> timezone:
    if offset_hours is None:
        return timezone.utc
    whole_hours = int(float(offset_hours))
    minutes = int(round((float(offset_hours) - whole_hours) * 60))
    return timezone(timedelta(hours=whole_hours, minutes=minutes))


def parse_datetime(value: Any, offset_hours: float | int | None = None) -> str | None:
    if value is None or value == "":
        return None

    tz = fixed_timezone(offset_hours)

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, timezone.utc).astimezone(tz).isoformat()

    text = str(value).strip()
    if not text:
        return None

    if text.isdigit() and len(text) == 14:
        return datetime.strptime(text, "%Y%m%d%H%M%S").replace(tzinfo=tz).isoformat()

    iso_text = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(iso_text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=tz)
        return parsed.isoformat()
    except ValueError:
        pass

    for fmt in (
        "%d/%m/%Y %H:%M",
        "%d-%b-%Y %I:%M %p",
        "%d-%b-%Y %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y",
    ):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=tz).isoformat()
        except ValueError:
            continue

    return None


def format_duration(minutes: int | None) -> str | None:
    if minutes is None:
        return None
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins:02d}m" if hours else f"{mins}m"


def total_pages(total: int, page_size: int) -> int:
    return max(1, ceil(total / page_size)) if total else 0
