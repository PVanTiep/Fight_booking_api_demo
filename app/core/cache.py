from __future__ import annotations

from cachetools import TTLCache

from app.core.config import Settings


class CacheManager:
    def __init__(self, settings: Settings) -> None:
        self.airport_list: TTLCache[str, object] = TTLCache(
            maxsize=1, ttl=settings.airport_cache_ttl_seconds
        )
        self.airports: TTLCache[str, object] = TTLCache(
            maxsize=512, ttl=settings.airport_cache_ttl_seconds
        )
        self.bookings: TTLCache[str, object] = TTLCache(
            maxsize=512, ttl=settings.booking_cache_ttl_seconds
        )
