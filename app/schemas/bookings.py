from __future__ import annotations

from datetime import date

from pydantic import Field, field_validator

from app.schemas.common import APIModel, CodeLabel


class BookingPassengerRequest(APIModel):
    title: str | None = Field(default=None, max_length=12)
    first_name: str = Field(min_length=1, max_length=80, examples=["Alex"])
    last_name: str = Field(min_length=1, max_length=80, examples=["Nguyen"])
    dob: date | None = Field(default=None, examples=["1990-01-01"])
    nationality: str | None = Field(default=None, min_length=2, max_length=2)
    passport_no: str | None = Field(default=None, max_length=32)
    email: str | None = None
    phone: str | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def has_non_blank_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name cannot be blank")
        return value

    @field_validator("nationality")
    @classmethod
    def uppercase_country(cls, value: str | None) -> str | None:
        return value.upper() if value else value

    @field_validator("email")
    @classmethod
    def basic_email(cls, value: str | None) -> str | None:
        if value and "@" not in value:
            raise ValueError("email must contain @")
        return value


class CreateBookingRequest(APIModel):
    offer_id: str = Field(min_length=1, examples=["1e080aa936888c3d"])
    passengers: list[BookingPassengerRequest] = Field(min_length=1, max_length=9)
    contact_email: str = Field(examples=["alex@example.com"])
    contact_phone: str | None = Field(default=None, examples=["+60123456789"])

    @field_validator("contact_email")
    @classmethod
    def basic_contact_email(cls, value: str) -> str:
        if "@" not in value:
            raise ValueError("contactEmail must contain @")
        return value


class BookingPassenger(APIModel):
    passenger_id: str | None = None
    title: str | None = None
    first_name: str
    last_name: str
    date_of_birth: str | None = None
    nationality: str | None = None
    passport_no: str | None = None
    passenger_type: CodeLabel


class BookingContact(APIModel):
    email: str | None = None
    phone: str | None = None


class TicketingSummary(APIModel):
    status: CodeLabel | None = None
    time_limit: str | None = None
    ticket_numbers: list[str]


class BookingSummary(APIModel):
    booking_reference: str
    pnr: str | None = None
    status: CodeLabel
    offer_id: str | None = None
    passengers: list[BookingPassenger]
    contact: BookingContact | None = None
    ticketing: TicketingSummary | None = None
    created_at: str | None = None
