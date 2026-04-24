from __future__ import annotations

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
        self.create_booking_calls: list[dict] = []

    async def aclose(self) -> None:
        return None

    async def search_flights(self, payload):
        return SEARCH_RESPONSE

    async def get_offer(self, offer_id):
        return OFFER_RESPONSE

    async def create_booking(self, payload):
        self.create_booking_calls.append(payload)
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
async def fake_client():
    return FakeLegacyClient()


@pytest.fixture
async def api_client(fake_client):
    app.state.legacy_client = fake_client
    app.state.cache = CacheManager(Settings())
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
