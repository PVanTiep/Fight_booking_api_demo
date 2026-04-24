from app.adapters.airports import normalize_airport
from app.adapters.bookings import normalize_booking_create
from app.adapters.errors import normalize_legacy_error
from app.adapters.offers import normalize_offer_details
from app.adapters.search import normalize_search_response
from tests.fixtures import BOOKING_CREATE_RESPONSE, OFFER_RESPONSE, SEARCH_RESPONSE, airport


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


def test_offer_details_normalizes_policy_and_baggage():
    response = normalize_offer_details(OFFER_RESPONSE)

    assert response.offer_id == "offer-direct"
    assert response.fare_rules.refund.allowed is True
    assert response.baggage.checked_weight_kg == 25
    assert response.payment_requirements.accepted_methods[0].label == "Credit card"


def test_booking_normalization_uses_clean_reference_and_status():
    booking = normalize_booking_create(BOOKING_CREATE_RESPONSE)

    assert booking.booking_reference == "EG4A452D"
    assert booking.status.code == "HK"
    assert booking.status.label == "Confirmed"
    assert booking.passengers[0].passenger_type.label == "Adult"


def test_legacy_error_formats_normalize_to_single_exception_shape():
    error = normalize_legacy_error(
        404,
        {"errors": [{"code": "NOT_FOUND", "detail": "Offer not found"}]},
    )

    assert error.status_code == 404
    assert error.code == "NOT_FOUND"
    assert error.message == "Offer not found"
