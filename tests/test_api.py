import pytest

from app.core.errors import AppError


# ---------------------------------------------------------------------------
# Flight search
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_search_endpoint_returns_camel_case_contract(api_client):
    response = await api_client.post(
        "/api/v1/flights/search?pageSize=5",
        json={
            "origin": "KUL",
            "destination": "SIN",
            "departureDate": "2026-05-15",
            "paxCount": 1,
            "cabin": "Y",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["pageSize"] == 5
    assert body["items"][0]["offerId"] == "offer-direct"
    assert body["items"][0]["airline"]["label"] == "Malaysia Airlines"


@pytest.mark.anyio
async def test_search_past_departure_date_returns_422(api_client):
    response = await api_client.post(
        "/api/v1/flights/search",
        json={
            "origin": "KUL",
            "destination": "SIN",
            "departureDate": "2020-01-01",
            "paxCount": 1,
            "cabin": "Y",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.anyio
async def test_search_return_before_departure_returns_422(api_client):
    response = await api_client.post(
        "/api/v1/flights/search",
        json={
            "origin": "KUL",
            "destination": "SIN",
            "departureDate": "2026-05-15",
            "returnDate": "2026-05-10",
            "paxCount": 1,
            "cabin": "Y",
        },
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Offer details
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_offer_details_returns_normalized_offer(api_client):
    response = await api_client.get("/api/v1/offers/offer-direct")

    assert response.status_code == 200
    body = response.json()
    assert body["offerId"] == "offer-direct"
    assert body["fareRules"]["refund"]["allowed"] is True
    assert body["baggage"]["checkedWeightKg"] == 25


@pytest.mark.anyio
async def test_get_offer_invalid_id_returns_422(api_client):
    response = await api_client.get("/api/v1/offers/" + "x" * 65)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_booking_returns_201(api_client):
    response = await api_client.post(
        "/api/v1/bookings",
        json={
            "offerId": "offer-direct",
            "passengers": [
                {
                    "firstName": "Alex",
                    "lastName": "Nguyen",
                    "dob": "1990-01-01",
                    "nationality": "MY",
                    "passportNo": "A1234567",
                    "email": "alex@example.com",
                    "phone": "+60123456789",
                }
            ],
            "contactEmail": "alex@example.com",
            "contactPhone": "+60123456789",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["bookingReference"] == "EG4A452D"
    assert body["status"]["label"] == "Confirmed"


@pytest.mark.anyio
async def test_validation_errors_use_public_error_envelope(api_client):
    response = await api_client.post(
        "/api/v1/bookings",
        json={"offerId": "offer-direct", "passengers": [], "contactEmail": "bad-email"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "requestId" in body["error"]


@pytest.mark.anyio
async def test_create_booking_too_many_passengers_returns_422(api_client):
    passenger = {
        "firstName": "Test",
        "lastName": "User",
        "email": "t@example.com",
    }
    response = await api_client.post(
        "/api/v1/bookings",
        json={
            "offerId": "offer-direct",
            "passengers": [passenger] * 10,
            "contactEmail": "t@example.com",
        },
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_booking_retrieval_sets_cache_header(api_client, fake_client):
    first = await api_client.get("/api/v1/bookings/EG4A452D")
    second = await api_client.get("/api/v1/bookings/EG4A452D")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.headers["X-Cache"] == "MISS"
    assert second.headers["X-Cache"] == "HIT"
    assert fake_client.booking_reads == 1


@pytest.mark.anyio
async def test_booking_invalid_reference_returns_422(api_client):
    response = await api_client.get("/api/v1/bookings/!!bad!!")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Airports
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_airports_returns_normalized_list(api_client):
    response = await api_client.get("/api/v1/airports")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    codes = {item["code"] for item in body["items"]}
    assert codes == {"KUL", "SIN"}


@pytest.mark.anyio
async def test_get_airport_by_code(api_client):
    response = await api_client.get("/api/v1/airports/KUL")

    assert response.status_code == 200
    assert response.json()["code"] == "KUL"


@pytest.mark.anyio
async def test_get_airport_invalid_code_returns_422(api_client):
    response = await api_client.get("/api/v1/airports/kuL")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Error envelope consistency
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_upstream_error_uses_error_envelope(api_client, fake_client):
    async def raise_app_error(_):
        raise AppError(code="UPSTREAM_503", message="Legacy down.", status_code=503)

    fake_client.search_flights = raise_app_error

    response = await api_client.post(
        "/api/v1/flights/search",
        json={
            "origin": "KUL",
            "destination": "SIN",
            "departureDate": "2026-05-15",
            "paxCount": 1,
            "cabin": "Y",
        },
    )

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "UPSTREAM_503"
    assert "requestId" in body["error"]
    assert "upstream" not in body["error"].get("details", {})


@pytest.mark.anyio
async def test_404_uses_error_envelope(api_client):
    response = await api_client.get("/api/v1/nonexistent-path")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"


@pytest.mark.anyio
async def test_request_id_header_present(api_client):
    response = await api_client.get("/health")
    assert "x-request-id" in response.headers
