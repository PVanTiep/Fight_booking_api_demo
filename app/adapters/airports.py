from __future__ import annotations

from typing import Any

from app.adapters.reference import AIRPORT_CITIES
from app.adapters.utils import first_value, nested, to_float
from app.schemas.airports import Airport, Coordinates


def normalize_airport(payload: dict[str, Any]) -> Airport:
    code = str(first_value(payload, "code", "IATA", default="UNKNOWN")).upper()
    coordinates = payload.get("coordinates") if isinstance(payload.get("coordinates"), dict) else {}
    latitude = to_float(first_value(coordinates, "lat", "latitude"))
    longitude = to_float(first_value(coordinates, "lng", "longitude"))
    return Airport(
        code=code,
        city=first_value(payload, "city", default=AIRPORT_CITIES.get(code)),
        country_code=first_value(payload, "country_code", "CC"),
        timezone_offset=to_float(first_value(payload, "tz_offset")),
        coordinates=Coordinates(latitude=latitude, longitude=longitude),
    )


def normalize_airport_list(payload: dict[str, Any]) -> list[Airport]:
    airports = nested(payload, "airports", default=[])
    if not isinstance(airports, list):
        return []
    return [normalize_airport(item) for item in airports if isinstance(item, dict)]
