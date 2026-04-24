from __future__ import annotations

from typing import Any

from app.adapters.reference import AIRCRAFT, AIRLINES, CABINS, code_label
from app.adapters.utils import (
    first_value,
    format_duration,
    nested,
    parse_datetime,
    to_float,
    to_int,
    total_pages,
)
from app.schemas.airports import Airport
from app.schemas.common import Money
from app.schemas.search import (
    AirportRef,
    BaggageSummary,
    FlightOfferSummary,
    FlightSearchResponse,
    FlightSegment,
    PriceSummary,
)


def extract_airport_codes(payload: dict[str, Any]) -> set[str]:
    codes: set[str] = set()
    for offer in _legacy_results(payload):
        for segment in _segment_list(offer):
            for leg in _leg_list(segment):
                for info_key in ("departure_info", "arrival_info"):
                    code = nested(leg, info_key, "airport", "code")
                    if code:
                        codes.add(str(code).upper())
    return codes


def normalize_search_response(
    payload: dict[str, Any],
    airports: dict[str, Airport],
    *,
    page: int,
    page_size: int,
) -> FlightSearchResponse:
    offers = [_normalize_offer(item, airports) for item in _legacy_results(payload)]
    total = len(offers)
    start = (page - 1) * page_size
    end = start + page_size
    return FlightSearchResponse(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages(total, page_size),
        items=offers[start:end],
    )


def _legacy_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = nested(payload, "data", "flight_results", "outbound", "results", default=[])
    return [item for item in results if isinstance(item, dict)]


def _segment_list(offer: dict[str, Any]) -> list[dict[str, Any]]:
    segments = nested(offer, "segments", "segment_list", default=[])
    return [segment for segment in segments if isinstance(segment, dict)]


def _leg_list(segment: dict[str, Any]) -> list[dict[str, Any]]:
    legs = segment.get("leg_data", [])
    return [leg for leg in legs if isinstance(leg, dict)]


def _normalize_offer(offer: dict[str, Any], airports: dict[str, Airport]) -> FlightOfferSummary:
    flat_legs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    segments: list[FlightSegment] = []

    for segment in _segment_list(offer):
        layover_after = to_int(nested(segment, "connection_info", "layover_min"))
        for leg in _leg_list(segment):
            flat_legs.append((segment, leg))
            segments.append(_normalize_segment(leg, airports, layover_after))

    first_leg = flat_legs[0][1] if flat_legs else {}
    last_leg = flat_legs[-1][1] if flat_legs else {}
    origin_code = str(nested(first_leg, "departure_info", "airport", "code", default="UNKNOWN")).upper()
    destination_code = str(nested(last_leg, "arrival_info", "airport", "code", default="UNKNOWN")).upper()
    origin = _airport_ref(origin_code, nested(first_leg, "departure_info", "airport", "terminal"), airports)
    destination = _airport_ref(
        destination_code,
        nested(last_leg, "arrival_info", "airport", "terminal"),
        airports,
    )
    origin_offset = _airport_offset(origin_code, airports)
    destination_offset = _airport_offset(destination_code, airports)

    pricing = offer.get("pricing") if isinstance(offer.get("pricing"), dict) else {}
    currency = str(first_value(pricing, "currency", "CurrencyCode", default="MYR"))
    total = to_float(first_value(pricing, "totalAmountDecimal", "total", "total_amount", default=0)) or 0
    base = to_float(first_value(pricing, "base_fare", "BaseFare"))
    taxes_payload = pricing.get("taxes_fees") if isinstance(pricing.get("taxes_fees"), dict) else {}
    taxes = to_float(first_value(taxes_payload, "total_tax", "TotalTax"))
    validating_carrier = first_value(offer, "validating_carrier") or nested(first_leg, "carrier", "marketing")

    duration_minutes = to_int(first_value(offer, "total_journey_time"))

    return FlightOfferSummary(
        offer_id=str(first_value(offer, "offer_id", "offerId", default="")),
        airline=code_label(validating_carrier, AIRLINES),
        origin=origin,
        destination=destination,
        departure_time=parse_datetime(
            nested(first_leg, "departure_info", "scheduled_time"),
            origin_offset,
        ),
        arrival_time=parse_datetime(
            nested(last_leg, "arrival_info", "scheduled_time"),
            destination_offset,
        ),
        stops=to_int(first_value(offer, "stops", "num_stops", default=0)) or 0,
        duration_minutes=duration_minutes,
        duration=first_value(offer, "total_journey") or format_duration(duration_minutes),
        price=PriceSummary(
            total=Money(amount=total, currency=currency),
            base=Money(amount=base, currency=currency) if base is not None else None,
            taxes=Money(amount=taxes, currency=currency) if taxes is not None else None,
        ),
        segments=segments,
        baggage=_normalize_baggage(offer.get("baggage")),
        seats_remaining=to_int(first_value(offer, "seatAvailability", "seats_remaining", "avl_seats")),
        refundable=first_value(offer, "isRefundable", "refundable"),
    )


def _normalize_segment(
    leg: dict[str, Any],
    airports: dict[str, Airport],
    layover_after: int | None,
) -> FlightSegment:
    origin_code = str(nested(leg, "departure_info", "airport", "code", default="UNKNOWN")).upper()
    destination_code = str(nested(leg, "arrival_info", "airport", "code", default="UNKNOWN")).upper()
    duration_minutes = to_int(first_value(leg, "duration_minutes"))
    marketing = first_value(nested(leg, "carrier", default={}), "marketing", "mktg_carrier")
    operating = first_value(nested(leg, "carrier", default={}), "operating", "marketing")
    aircraft_code = first_value(nested(leg, "equipment", default={}), "aircraft_code", "type")
    cabin_code = first_value(leg, "cabin", "cabin_class")

    return FlightSegment(
        flight_number=first_value(nested(leg, "carrier", default={}), "number", "flight_no"),
        marketing_carrier=code_label(marketing, AIRLINES),
        operating_carrier=code_label(operating, AIRLINES),
        aircraft=code_label(aircraft_code, AIRCRAFT) if aircraft_code else None,
        cabin=code_label(cabin_code, CABINS),
        origin=_airport_ref(origin_code, nested(leg, "departure_info", "airport", "terminal"), airports),
        destination=_airport_ref(
            destination_code,
            nested(leg, "arrival_info", "airport", "terminal"),
            airports,
        ),
        departure_time=parse_datetime(
            nested(leg, "departure_info", "scheduled_time"),
            _airport_offset(origin_code, airports),
        ),
        arrival_time=parse_datetime(
            nested(leg, "arrival_info", "scheduled_time"),
            _airport_offset(destination_code, airports),
        ),
        duration_minutes=duration_minutes,
        duration=first_value(leg, "elapsed_time") or format_duration(duration_minutes),
        layover_after_minutes=layover_after,
    )


def _normalize_baggage(value: Any) -> BaggageSummary | None:
    if not isinstance(value, dict):
        return None
    checked = value.get("checked") if isinstance(value.get("checked"), dict) else {}
    cabin = value.get("cabin_baggage") if isinstance(value.get("cabin_baggage"), dict) else {}
    return BaggageSummary(
        checked_pieces=to_int(first_value(checked, "pieces", "quantity")),
        checked_weight_kg=to_int(first_value(checked, "weight_kg", "Weight", "max_weight_kg")),
        cabin_pieces=to_int(first_value(cabin, "pieces", "quantity")),
        cabin_weight_kg=to_int(first_value(cabin, "weight_kg", "MaxWeight", "max_weight_kg")),
    )


def _airport_ref(code: str, terminal: Any, airports: dict[str, Airport]) -> AirportRef:
    airport = airports.get(code)
    return AirportRef(
        code=code,
        city=airport.city if airport else None,
        terminal=str(terminal) if terminal is not None else None,
    )


def _airport_offset(code: str, airports: dict[str, Airport]) -> float | None:
    airport = airports.get(code)
    return airport.timezone_offset if airport else None
