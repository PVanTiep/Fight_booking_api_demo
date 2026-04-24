from __future__ import annotations

from typing import Any

from app.adapters.reference import BOOKING_STATUSES, PASSENGER_TYPES, code_label
from app.adapters.utils import first_value, nested, parse_datetime
from app.schemas.bookings import (
    BookingContact,
    BookingPassenger,
    BookingSummary,
    TicketingSummary,
)


def normalize_booking_create(payload: dict[str, Any]) -> BookingSummary:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    return _normalize_reservation(data)


def normalize_booking_retrieve(payload: dict[str, Any]) -> BookingSummary:
    reservation = nested(payload, "data", "reservation", default=None)
    if not isinstance(reservation, dict):
        reservation = nested(payload, "data", "Reservation", default={})
    return _normalize_reservation(reservation if isinstance(reservation, dict) else {})


def _normalize_reservation(reservation: dict[str, Any]) -> BookingSummary:
    passengers = reservation.get("passengers") if isinstance(reservation.get("passengers"), list) else []
    contact = reservation.get("contact") if isinstance(reservation.get("contact"), dict) else {}
    ticketing = reservation.get("ticketing") if isinstance(reservation.get("ticketing"), dict) else {}
    status_code = first_value(reservation, "StatusCode", "status", default="UNKNOWN")

    return BookingSummary(
        booking_reference=str(first_value(reservation, "booking_ref", "BookingReference", default="")),
        pnr=first_value(reservation, "pnr", "PNR"),
        status=code_label(status_code, BOOKING_STATUSES),
        offer_id=first_value(reservation, "offer_id", "offerId"),
        passengers=[
            _passenger(item) for item in passengers if isinstance(item, dict)
        ],
        contact=BookingContact(
            email=first_value(contact, "email", "EmailAddress"),
            phone=first_value(contact, "phone"),
        )
        if contact
        else None,
        ticketing=TicketingSummary(
            status=code_label(first_value(ticketing, "status"), BOOKING_STATUSES)
            if ticketing
            else None,
            time_limit=parse_datetime(first_value(ticketing, "time_limit")),
            ticket_numbers=[
                str(ticket)
                for ticket in (ticketing.get("ticket_numbers") or [])
                if ticket
            ],
        )
        if ticketing
        else None,
        created_at=parse_datetime(first_value(reservation, "CreatedDateTime", "created_at")),
    )


def _passenger(value: dict[str, Any]) -> BookingPassenger:
    passenger_type = first_value(value, "PaxType", "type", default="ADT")
    return BookingPassenger(
        passenger_id=first_value(value, "pax_id", "passenger_id"),
        title=first_value(value, "title"),
        first_name=str(first_value(value, "first_name", "FirstName", default="")),
        last_name=str(first_value(value, "last_name", "LastName", default="")),
        date_of_birth=first_value(value, "dob", "DateOfBirth"),
        nationality=first_value(value, "nationality"),
        passport_no=first_value(value, "passport_no"),
        passenger_type=code_label(passenger_type, PASSENGER_TYPES),
    )
