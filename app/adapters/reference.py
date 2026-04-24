from __future__ import annotations

from app.schemas.common import CodeLabel


AIRLINES = {
    "3K": "Jetstar Asia",
    "AK": "AirAsia",
    "CX": "Cathay Pacific",
    "MH": "Malaysia Airlines",
    "OD": "Batik Air Malaysia",
    "SQ": "Singapore Airlines",
    "TG": "Thai Airways",
    "TR": "Scoot",
}

AIRCRAFT = {
    "320": "Airbus A320",
    "321": "Airbus A321",
    "333": "Airbus A330-300",
    "359": "Airbus A350-900",
    "388": "Airbus A380-800",
    "738": "Boeing 737-800",
    "789": "Boeing 787-9",
}

AIRPORT_CITIES = {
    "BKI": "Kota Kinabalu",
    "BKK": "Bangkok",
    "CGK": "Jakarta",
    "DEL": "Delhi",
    "DMK": "Bangkok",
    "DXB": "Dubai",
    "HAN": "Hanoi",
    "HKG": "Hong Kong",
    "ICN": "Seoul",
    "KCH": "Kuching",
    "KUL": "Kuala Lumpur",
    "LGK": "Langkawi",
    "LHR": "London",
    "MNL": "Manila",
    "NRT": "Tokyo",
    "PEN": "Penang",
    "PNH": "Phnom Penh",
    "RGN": "Yangon",
    "SGN": "Ho Chi Minh City",
    "SIN": "Singapore",
    "SYD": "Sydney",
}

BOOKING_STATUSES = {
    "CONFIRMED": "Confirmed",
    "HK": "Confirmed",
    "PENDING": "Pending ticketing",
    "CANCELLED": "Cancelled",
    "UC": "Unable to confirm",
}

CABINS = {
    "Y": "Economy",
    "W": "Premium Economy",
    "J": "Business",
    "F": "First",
}

FARE_FAMILIES = {
    "FL": "Full Flex",
    "FULL": "Full Flex",
    "LITE": "Lite",
    "VALUE": "Value",
}

PASSENGER_TYPES = {
    "ADT": "Adult",
    "CHD": "Child",
    "INF": "Infant",
}

PAYMENT_METHODS = {
    "BT": "Bank transfer",
    "CC": "Credit card",
    "DC": "Debit card",
}


def code_label(code: str | None, mapping: dict[str, str], unknown: str = "Unknown") -> CodeLabel:
    normalized = (code or "UNKNOWN").upper()
    return CodeLabel(code=normalized, label=mapping.get(normalized, unknown))


def loose_label(value: str | None, mapping: dict[str, str], unknown: str = "Unknown") -> CodeLabel:
    normalized = value or "UNKNOWN"
    fallback = value.replace("_", " ").title() if value else unknown
    return CodeLabel(code=normalized, label=mapping.get(normalized.upper(), fallback))
