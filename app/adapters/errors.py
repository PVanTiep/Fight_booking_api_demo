from __future__ import annotations

from typing import Any

from app.core.errors import LegacyAPIError


def normalize_legacy_error(status_code: int, payload: Any) -> LegacyAPIError:
    code = f"UPSTREAM_{status_code}"
    message = "The flight provider returned an error."

    if isinstance(payload, dict):
        if isinstance(payload.get("error"), dict):
            error = payload["error"]
            code = str(error.get("code") or code)
            message = str(error.get("message") or message)
        elif isinstance(payload.get("errors"), list) and payload["errors"]:
            error = payload["errors"][0]
            if isinstance(error, dict):
                code = str(error.get("code") or code)
                message = str(error.get("detail") or error.get("message") or message)
        elif isinstance(payload.get("fault"), dict):
            fault = payload["fault"]
            code = str(fault.get("faultcode") or code)
            message = str(fault.get("faultstring") or message)
        elif payload.get("status") == "error":
            code = "UPSTREAM_ERROR"
            message = str(payload.get("msg") or message)

    public_status = status_code if 400 <= status_code < 500 else 503

    return LegacyAPIError(
        code=code,
        message=message,
        status_code=public_status,
        upstream_payload=payload,
    )
