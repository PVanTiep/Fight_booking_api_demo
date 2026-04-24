import pytest

from app.adapters.airports import normalize_airport, normalize_airport_list
from app.adapters.bookings import normalize_booking_create, normalize_booking_retrieve
from app.adapters.errors import normalize_legacy_error
from app.adapters.offers import normalize_offer_details
from app.adapters.search import normalize_search_response
from app.adapters.utils import (
    format_duration,
    parse_datetime,
    to_int,
    total_pages,
)
from tests.fixtures import BOOKING_CREATE_RESPONSE, BOOKING_RETRIEVE_RESPONSE, OFFER_RESPONSE, SEARCH_RESPONSE, airport


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def test_search_transformer_flattens_and_labels_offer():
    airports = {
        "KUL": normalize_airport(airport("KUL", "Kuala Lumpur")),
        "SIN": normalize_airport(airport("SIN", "Singapore")),
    }

    response = normalize_search_response(SEARCH_RESPONSE, airports, page=1, page_size=10)

    assert response.total == 1
    offer = response.items[0]
    assert offer.offer_id == "offer-direct"
    assert offer.airline.label == "Malaysia Airlines"
    assert offer.origin.city == "Kuala Lumpur"
    assert offer.destination.city == "Singapore"
    assert offer.price.total.amount == 97.08
    assert offer.segments[0].aircraft.label == "Airbus A350-900"
    assert offer.departure_time.startswith("2026-05-15T08:25:00")


def test_search_empty_results_returns_zero_total():
    empty = {"data": {"flight_results": {"outbound": {"results": []}}}}
    response = normalize_search_response(empty, {}, page=1, page_size=10)
    assert response.total == 0
    assert response.items == []
    assert response.total_pages == 0


def test_search_pagination_slices_correctly():
    airports = {
        "KUL": normalize_airport(airport("KUL", "Kuala Lumpur")),
        "SIN": normalize_airport(airport("SIN", "Singapore")),
    }
    response = normalize_search_response(SEARCH_RESPONSE, airports, page=2, page_size=1)
    assert response.page == 2
    assert response.items == []


# ---------------------------------------------------------------------------
# Offer details
# ---------------------------------------------------------------------------


def test_offer_details_normalizes_policy_and_baggage():
    response = normalize_offer_details(OFFER_RESPONSE)

    assert response.offer_id == "offer-direct"
    assert response.fare_rules.refund.allowed is True
    assert response.baggage.checked_weight_kg == 25
    assert response.payment_requirements.accepted_methods[0].label == "Credit card"


def test_offer_details_price_is_none_when_no_pricing_field():
    response = normalize_offer_details(OFFER_RESPONSE)
    assert response.price is None


def test_offer_details_price_extracted_when_pricing_present():
    payload_with_price = {
        "data": {
            "offer": {
                **OFFER_RESPONSE["data"]["offer"],
                "pricing": {"currency": "MYR", "total": 250.50},
            }
        }
    }
    response = normalize_offer_details(payload_with_price)
    assert response.price is not None
    assert response.price.amount == 250.50
    assert response.price.currency == "MYR"


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------


def test_booking_normalization_uses_clean_reference_and_status():
    booking = normalize_booking_create(BOOKING_CREATE_RESPONSE)

    assert booking.booking_reference == "EG4A452D"
    assert booking.status.code == "HK"
    assert booking.status.label == "Confirmed"
    assert booking.passengers[0].passenger_type.label == "Adult"


def test_booking_retrieve_normalizes_nested_reservation():
    booking = normalize_booking_retrieve(BOOKING_RETRIEVE_RESPONSE)

    assert booking.booking_reference == "EG4A452D"
    assert booking.status.label == "Confirmed"
    assert booking.contact.email == "alex@example.com"
    assert booking.ticketing is not None


def test_booking_ticket_numbers_handles_none_value():
    payload = {
        "data": {
            "booking_ref": "TEST001",
            "status": "CONFIRMED",
            "StatusCode": "HK",
            "passengers": [],
            "ticketing": {"status": "PENDING", "ticket_numbers": None},
        }
    }
    booking = normalize_booking_create(payload)
    assert booking.ticketing.ticket_numbers == []


# ---------------------------------------------------------------------------
# Legacy error normalization
# ---------------------------------------------------------------------------


def test_legacy_error_formats_normalize_to_single_exception_shape():
    error = normalize_legacy_error(
        404,
        {"errors": [{"code": "NOT_FOUND", "detail": "Offer not found"}]},
    )

    assert error.status_code == 404
    assert error.code == "NOT_FOUND"
    assert error.message == "Offer not found"


def test_legacy_error_object_format():
    error = normalize_legacy_error(
        400,
        {"error": {"code": "INVALID_REQUEST", "message": "Bad payload"}},
    )
    assert error.code == "INVALID_REQUEST"
    assert error.message == "Bad payload"
    assert error.status_code == 400


def test_legacy_error_fault_format():
    error = normalize_legacy_error(
        503,
        {"fault": {"faultcode": "SOAP_FAULT", "faultstring": "Service unavailable"}},
    )
    assert error.code == "SOAP_FAULT"
    assert error.message == "Service unavailable"
    assert error.status_code == 503


def test_legacy_error_status_error_format():
    error = normalize_legacy_error(
        500,
        {"status": "error", "msg": "Something went wrong"},
    )
    assert error.code == "UPSTREAM_ERROR"
    assert error.message == "Something went wrong"
    assert error.status_code == 503


def test_legacy_error_upstream_payload_not_in_details():
    error = normalize_legacy_error(500, {"some": "internal data"})
    assert "upstream" not in error.details


# ---------------------------------------------------------------------------
# Utils
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        (None, None),
        ("", None),
        (0, 0),
        ("30KG", 30),
        ("30kg", 30),
        ("30 KG", 30),
        ("30 kg", 30),
        ("25", 25),
        (25, 25),
        (25.9, 25),
    ],
)
def test_to_int_handles_various_inputs(raw, expected):
    assert to_int(raw) == expected


@pytest.mark.parametrize(
    "minutes, expected",
    [
        (None, None),
        (0, "0m"),
        (45, "45m"),
        (60, "1h 00m"),
        (90, "1h 30m"),
        (125, "2h 05m"),
    ],
)
def test_format_duration(minutes, expected):
    assert format_duration(minutes) == expected


@pytest.mark.parametrize(
    "total, page_size, expected",
    [
        (0, 10, 0),
        (1, 10, 1),
        (10, 10, 1),
        (11, 10, 2),
        (100, 10, 10),
    ],
)
def test_total_pages(total, page_size, expected):
    assert total_pages(total, page_size) == expected


def test_parse_datetime_iso_string():
    result = parse_datetime("2026-05-15T08:25:00+00:00")
    assert result == "2026-05-15T08:25:00+00:00"


def test_parse_datetime_unix_timestamp():
    result = parse_datetime(0)
    assert result == "1970-01-01T00:00:00+00:00"


def test_parse_datetime_yyyymmddhhmmss():
    result = parse_datetime("20260424080612")
    assert result is not None
    assert "2026-04-24" in result


def test_parse_datetime_dd_slash_mm_yyyy_time():
    result = parse_datetime("24/04/2026 08:30")
    assert result is not None
    assert "2026-04-24" in result


def test_parse_datetime_returns_none_for_garbage():
    assert parse_datetime("not-a-date") is None


def test_parse_datetime_returns_none_for_none():
    assert parse_datetime(None) is None


# ---------------------------------------------------------------------------
# Airports
# ---------------------------------------------------------------------------


def test_normalize_airport_list_returns_all_items():
    payload = {"airports": [airport("KUL", "Kuala Lumpur"), airport("SIN", "Singapore")]}
    result = normalize_airport_list(payload)
    assert len(result) == 2
    assert result[0].code == "KUL"
    assert result[1].code == "SIN"


def test_normalize_airport_list_handles_missing_key():
    assert normalize_airport_list({}) == []
    assert normalize_airport_list({"airports": "not-a-list"}) == []
