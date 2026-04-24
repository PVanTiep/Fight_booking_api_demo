from __future__ import annotations

from typing import Any

from app.adapters.airports import normalize_airport, normalize_airport_list
from app.adapters.bookings import normalize_booking_create, normalize_booking_retrieve
from app.adapters.offers import normalize_offer_details
from app.adapters.search import extract_airport_codes, normalize_search_response
from app.clients.legacy import LegacyClient
from app.core.cache import CacheManager
from app.schemas.airports import Airport, AirportListResponse
from app.schemas.bookings import BookingSummary, CreateBookingRequest
from app.schemas.offers import OfferDetails
from app.schemas.search import FlightSearchRequest, FlightSearchResponse


class FlightBookingService:
    def __init__(self, legacy: LegacyClient, cache: CacheManager) -> None:
        self.legacy = legacy
        self.cache = cache

    async def search_flights(
        self,
        request: FlightSearchRequest,
        *,
        page: int,
        page_size: int,
    ) -> FlightSearchResponse:
        payload = {
            "origin": request.origin,
            "destination": request.destination,
            "departure_date": request.departure_date.isoformat(),
            "return_date": request.return_date.isoformat() if request.return_date else None,
            "pax_count": request.pax_count,
            "cabin": request.cabin,
        }
        raw = await self.legacy.search_flights(payload)
        airports = await self._airport_map(extract_airport_codes(raw))
        return normalize_search_response(raw, airports, page=page, page_size=page_size)

    async def get_offer_details(self, offer_id: str) -> OfferDetails:
        raw = await self.legacy.get_offer(offer_id)
        return normalize_offer_details(raw)

    async def create_booking(self, request: CreateBookingRequest) -> BookingSummary:
        payload = {
            "offer_id": request.offer_id,
            "passengers": [
                {
                    "title": passenger.title,
                    "first_name": passenger.first_name,
                    "last_name": passenger.last_name,
                    "dob": passenger.dob.isoformat() if passenger.dob else None,
                    "nationality": passenger.nationality,
                    "passport_no": passenger.passport_no,
                    "email": passenger.email,
                    "phone": passenger.phone,
                }
                for passenger in request.passengers
            ],
            "contact_email": request.contact_email,
            "contact_phone": request.contact_phone,
        }
        raw = await self.legacy.create_booking(payload)
        booking = normalize_booking_create(raw)
        if booking.booking_reference:
            self.cache.bookings[booking.booking_reference.upper()] = booking
        return booking

    async def get_booking(self, reference: str) -> tuple[BookingSummary, str]:
        cache_key = reference.upper()
        cached = self.cache.bookings.get(cache_key)
        if isinstance(cached, BookingSummary):
            return cached, "HIT"

        raw = await self.legacy.get_booking(reference)
        booking = normalize_booking_retrieve(raw)
        if booking.booking_reference:
            self.cache.bookings[booking.booking_reference.upper()] = booking
        return booking, "MISS"

    async def list_airports(self) -> AirportListResponse:
        cached = self.cache.airport_list.get("all")
        if isinstance(cached, list):
            return AirportListResponse(total=len(cached), items=cached)

        raw = await self.legacy.list_airports()
        airports = normalize_airport_list(raw)
        self.cache.airport_list["all"] = airports
        for airport in airports:
            self.cache.airports[airport.code] = airport
        return AirportListResponse(total=len(airports), items=airports)

    async def get_airport(self, code: str) -> Airport:
        normalized_code = code.upper()
        cached = self.cache.airports.get(normalized_code)
        if isinstance(cached, Airport):
            return cached

        raw = await self.legacy.get_airport(normalized_code)
        airport = normalize_airport(raw)
        self.cache.airports[airport.code] = airport
        return airport

    async def _airport_map(self, codes: set[str]) -> dict[str, Airport]:
        airports: dict[str, Airport] = {}
        for code in codes:
            try:
                airports[code] = await self.get_airport(code)
            except Exception:
                continue
        return airports


def strip_none_values(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item is not None}
