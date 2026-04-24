from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query, Request, Response

from app.schemas.airports import Airport, AirportListResponse
from app.schemas.bookings import BookingSummary, CreateBookingRequest
from app.schemas.offers import OfferDetails
from app.schemas.search import FlightSearchRequest, FlightSearchResponse
from app.services import FlightBookingService

router = APIRouter()

_OFFER_ID_PATTERN = r"^[A-Za-z0-9_\-]{1,64}$"
_BOOKING_REF_PATTERN = r"^[A-Za-z0-9]{4,16}$"
_IATA_PATTERN = r"^[A-Z]{3}$"


def get_service(request: Request) -> FlightBookingService:
    return FlightBookingService(request.app.state.legacy_client, request.app.state.cache)


@router.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "flight-booking-wrapper"}


@router.post(
    "/api/v1/flights/search",
    response_model=FlightSearchResponse,
    tags=["Flights"],
)
async def search_flights(
    payload: FlightSearchRequest,
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50, alias="pageSize"),
    service: FlightBookingService = Depends(get_service),
) -> FlightSearchResponse:
    return await service.search_flights(payload, page=page, page_size=page_size)


@router.get(
    "/api/v1/offers/{offer_id}",
    response_model=OfferDetails,
    tags=["Offers"],
)
async def get_offer(
    offer_id: str = Path(pattern=_OFFER_ID_PATTERN),
    service: FlightBookingService = Depends(get_service),
) -> OfferDetails:
    return await service.get_offer_details(offer_id)


@router.post(
    "/api/v1/bookings",
    response_model=BookingSummary,
    status_code=201,
    tags=["Bookings"],
)
async def create_booking(
    payload: CreateBookingRequest,
    service: FlightBookingService = Depends(get_service),
) -> BookingSummary:
    return await service.create_booking(payload)


@router.get(
    "/api/v1/bookings/{booking_reference}",
    response_model=BookingSummary,
    tags=["Bookings"],
)
async def get_booking(
    response: Response,
    booking_reference: str = Path(pattern=_BOOKING_REF_PATTERN),
    service: FlightBookingService = Depends(get_service),
) -> BookingSummary:
    booking, cache_status = await service.get_booking(booking_reference)
    response.headers["X-Cache"] = cache_status
    return booking


@router.get(
    "/api/v1/airports",
    response_model=AirportListResponse,
    tags=["Airports"],
)
async def list_airports(
    service: FlightBookingService = Depends(get_service),
) -> AirportListResponse:
    return await service.list_airports()


@router.get(
    "/api/v1/airports/{code}",
    response_model=Airport,
    tags=["Airports"],
)
async def get_airport(
    code: str = Path(min_length=3, max_length=3, pattern=_IATA_PATTERN),
    service: FlightBookingService = Depends(get_service),
) -> Airport:
    return await service.get_airport(code)
