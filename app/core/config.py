from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - only relevant before dependencies are installed
    load_dotenv = None

if load_dotenv:
    load_dotenv()


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    legacy_api_base_url: str = os.getenv(
        "LEGACY_API_BASE_URL", "https://mock-travel-api.vercel.app"
    )
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "5"))
    connect_timeout_seconds: float = float(os.getenv("CONNECT_TIMEOUT_SECONDS", "2"))
    retry_attempts: int = int(os.getenv("RETRY_ATTEMPTS", "2"))
    retry_min_seconds: float = float(os.getenv("RETRY_MIN_SECONDS", "0.2"))
    retry_max_seconds: float = float(os.getenv("RETRY_MAX_SECONDS", "1.0"))
    simulate_issues: bool = _bool_env("SIMULATE_ISSUES", False)
    booking_cache_ttl_seconds: int = int(os.getenv("BOOKING_CACHE_TTL_SECONDS", "120"))
    airport_cache_ttl_seconds: int = int(os.getenv("AIRPORT_CACHE_TTL_SECONDS", "86400"))
    circuit_failure_threshold: int = int(os.getenv("CIRCUIT_FAILURE_THRESHOLD", "3"))
    circuit_cooldown_seconds: int = int(os.getenv("CIRCUIT_COOLDOWN_SECONDS", "20"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
