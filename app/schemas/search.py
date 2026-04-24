from __future__ import annotations

from datetime import date

from pydantic import Field, field_validator, model_validator

from app.schemas.common import APIModel, CodeLabel, Money


class FlightSearchRequest(APIModel):
    origin: str = Field(min_length=3, max_length=3, examples=["KUL"])
    destination: str = Field(min_length=3, max_length=3, examples=["SIN"])
    departure_date: date = Field(examples=["2026-05-15"])
    return_date: date | None = None
    pax_count: int = Field(default=1, ge=1, le=9)
    cabin: str = Field(default="Y", min_length=1, max_length=1, examples=["Y"])

    @field_validator("origin", "destination", "cabin")
    @classmethod
    def uppercase(cls, value: str) -> str:
        return value.upper()

    @field_validator("cabin")
    @classmethod
    def supported_cabin(cls, value: str) -> str:
        if value not in {"Y", "W", "J", "F"}:
            raise ValueError("cabin must be one of Y, W, J, F")
        return value

    @model_validator(mode="after")
    def origin_and_destination_must_differ(self) -> "FlightSearchRequest":
        if self.origin == self.destination:
            raise ValueError("origin and destination must be different")
        return self


class AirportRef(APIModel):
    code: str
    city: str | None = None
    terminal: str | None = None


class PriceSummary(APIModel):
    total: Money
    base: Money | None = None
    taxes: Money | None = None


class BaggageSummary(APIModel):
    checked_pieces: int | None = None
    checked_weight_kg: int | None = None
    cabin_pieces: int | None = None
    cabin_weight_kg: int | None = None


class FlightSegment(APIModel):
    flight_number: str | None = None
    marketing_carrier: CodeLabel
    operating_carrier: CodeLabel
    aircraft: CodeLabel | None = None
    cabin: CodeLabel
    origin: AirportRef
    destination: AirportRef
    departure_time: str | None = None
    arrival_time: str | None = None
    duration_minutes: int | None = None
    duration: str | None = None
    layover_after_minutes: int | None = None


class FlightOfferSummary(APIModel):
    offer_id: str
    airline: CodeLabel
    origin: AirportRef
    destination: AirportRef
    departure_time: str | None = None
    arrival_time: str | None = None
    stops: int
    duration_minutes: int | None = None
    duration: str | None = None
    price: PriceSummary
    segments: list[FlightSegment]
    baggage: BaggageSummary | None = None
    seats_remaining: int | None = None
    refundable: bool | None = None


class FlightSearchResponse(APIModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    items: list[FlightOfferSummary]
