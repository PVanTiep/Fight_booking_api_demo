import httpx
import pytest

from app.core.cache import CacheManager
from app.core.config import Settings
from app.main import app
from tests.fixtures import (
    BOOKING_CREATE_RESPONSE,
    BOOKING_RETRIEVE_RESPONSE,
    OFFER_RESPONSE,
    SEARCH_RESPONSE,
    airport,
)


class FakeLegacyClient:
    def __init__(self) -> None:
        self.booking_reads = 0

    async def aclose(self) -> None:
        return None

    async def search_flights(self, payload):
        return SEARCH_RESPONSE

    async def get_offer(self, offer_id):
        return OFFER_RESPONSE

    async def create_booking(self, payload):
        return BOOKING_CREATE_RESPONSE

    async def get_booking(self, reference):
        self.booking_reads += 1
        return BOOKING_RETRIEVE_RESPONSE

    async def list_airports(self):
        return {"airports": [airport("KUL", "Kuala Lumpur"), airport("SIN", "Singapore")]}

    async def get_airport(self, code):
        return airport(code, "Kuala Lumpur" if code == "KUL" else "Singapore")


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def api_client():
    app.state.legacy_client = FakeLegacyClient()
    app.state.cache = CacheManager(Settings())
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


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
async def test_booking_retrieval_sets_cache_header():
    fake = FakeLegacyClient()
    app.state.legacy_client = fake
    app.state.cache = CacheManager(Settings())

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.get("/api/v1/bookings/EG4A452D")
        second = await client.get("/api/v1/bookings/EG4A452D")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.headers["X-Cache"] == "MISS"
    assert second.headers["X-Cache"] == "HIT"
    assert fake.booking_reads == 1
