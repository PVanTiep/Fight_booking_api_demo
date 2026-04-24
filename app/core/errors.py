from __future__ import annotations

from typing import Any


class AppError(Exception):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class LegacyAPIError(AppError):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int,
        upstream_payload: Any | None = None,
    ) -> None:
        super().__init__(code=code, message=message, status_code=status_code)
        # Keep upstream payload for server-side logging only — never serialised into public responses.
        self.upstream_payload = upstream_payload


def is_retryable_status(status_code: int) -> bool:
    return status_code in {429, 503, 504}
