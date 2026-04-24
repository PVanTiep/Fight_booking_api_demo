from __future__ import annotations

from app.schemas.common import APIModel


class Coordinates(APIModel):
    latitude: float | None = None
    longitude: float | None = None


class Airport(APIModel):
    code: str
    city: str | None = None
    country_code: str | None = None
    timezone_offset: float | None = None
    coordinates: Coordinates | None = None


class AirportListResponse(APIModel):
    total: int
    items: list[Airport]
