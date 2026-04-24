from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class APIModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class CodeLabel(APIModel):
    code: str
    label: str


class Money(APIModel):
    amount: float
    currency: str


class ErrorPayload(APIModel):
    code: str
    message: str
    status: int
    request_id: str = Field(alias="requestId")
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(APIModel):
    error: ErrorPayload
