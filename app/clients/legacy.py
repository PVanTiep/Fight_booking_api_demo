from __future__ import annotations

import time
from typing import Any

import httpx
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt, wait_exponential

from app.adapters.errors import normalize_legacy_error
from app.core.config import Settings
from app.core.errors import AppError, LegacyAPIError, is_retryable_status


class CircuitBreaker:
    def __init__(self, *, threshold: int, cooldown_seconds: int) -> None:
        self.threshold = threshold
        self.cooldown_seconds = cooldown_seconds
        self.failures = 0
        self.opened_at: float | None = None

    def is_open(self) -> bool:
        if self.opened_at is None:
            return False
        if time.monotonic() - self.opened_at >= self.cooldown_seconds:
            self.opened_at = None
            self.failures = 0
            return False
        return True

    def record_success(self) -> None:
        self.failures = 0
        self.opened_at = None

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.threshold:
            self.opened_at = time.monotonic()


class LegacyClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        timeout = httpx.Timeout(
            settings.request_timeout_seconds,
            connect=settings.connect_timeout_seconds,
        )
        self._client = httpx.AsyncClient(
            base_url=settings.legacy_api_base_url.rstrip("/"),
            timeout=timeout,
        )
        self._breaker = CircuitBreaker(
            threshold=settings.circuit_failure_threshold,
            cooldown_seconds=settings.circuit_cooldown_seconds,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def search_flights(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/v1/flightsearch",
            json=payload,
            retry_safe=True,
        )

    async def get_offer(self, offer_id: str) -> dict[str, Any]:
        return await self._request(
            "GET",
            f"/api/v2/offer/{offer_id}",
            retry_safe=True,
        )

    async def create_booking(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/booking/create",
            json=payload,
            retry_safe=False,
        )

    async def get_booking(self, reference: str) -> dict[str, Any]:
        return await self._request(
            "GET",
            f"/api/v1/reservations/{reference}",
            retry_safe=True,
        )

    async def list_airports(self) -> dict[str, Any]:
        return await self._request("GET", "/api/airports", retry_safe=True)

    async def get_airport(self, code: str) -> dict[str, Any]:
        return await self._request("GET", f"/api/airports/{code}", retry_safe=True)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        retry_safe: bool,
    ) -> dict[str, Any]:
        if retry_safe and self._breaker.is_open():
            raise AppError(
                code="UPSTREAM_CIRCUIT_OPEN",
                message="The flight provider is temporarily unavailable.",
                status_code=503,
            )

        try:
            if retry_safe:
                result = await self._request_with_retry(method, path, json=json)
            else:
                result = await self._send(method, path, json=json)
        except LegacyAPIError as exc:
            if is_retryable_status(exc.status_code):
                self._breaker.record_failure()
            raise
        except AppError:
            self._breaker.record_failure()
            raise

        self._breaker.record_success()
        return result

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None,
    ) -> dict[str, Any]:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.settings.retry_attempts),
            wait=wait_exponential(
                multiplier=self.settings.retry_min_seconds,
                max=self.settings.retry_max_seconds,
            ),
            retry=retry_if_exception(_is_retryable_exception),
            reraise=True,
        ):
            with attempt:
                return await self._send(method, path, json=json)
        raise AppError(
            code="UPSTREAM_RETRY_FAILED",
            message="The flight provider did not return a usable response.",
            status_code=503,
        )

    async def _send(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None,
    ) -> dict[str, Any]:
        params = {"simulate_issues": "true"} if self.settings.simulate_issues else None
        try:
            response = await self._client.request(method, path, json=json, params=params)
        except httpx.TimeoutException as exc:
            raise LegacyAPIError(
                code="UPSTREAM_TIMEOUT",
                message="The flight provider did not respond in time.",
                status_code=504,
            ) from exc
        except httpx.RequestError as exc:
            raise LegacyAPIError(
                code="UPSTREAM_NETWORK_ERROR",
                message="Could not reach the flight provider.",
                status_code=503,
            ) from exc

        payload: Any
        try:
            payload = response.json()
        except ValueError as exc:
            raise LegacyAPIError(
                code="UPSTREAM_INVALID_JSON",
                message="The flight provider returned invalid JSON.",
                status_code=503,
            ) from exc

        if response.status_code >= 400:
            raise normalize_legacy_error(response.status_code, payload)

        if not isinstance(payload, dict):
            raise LegacyAPIError(
                code="UPSTREAM_UNEXPECTED_SHAPE",
                message="The flight provider returned an unexpected response shape.",
                status_code=503,
                upstream_payload=payload,
            )

        return payload


def _is_retryable_exception(exc: BaseException) -> bool:
    return isinstance(exc, LegacyAPIError) and is_retryable_status(exc.status_code)
