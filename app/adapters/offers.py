from __future__ import annotations

from typing import Any

from app.adapters.reference import BOOKING_STATUSES, FARE_FAMILIES, PAYMENT_METHODS, code_label, loose_label
from app.adapters.utils import first_value, nested, parse_datetime, to_float, to_int
from app.schemas.common import Money
from app.schemas.offers import (
    FarePolicy,
    FareRules,
    OfferBaggage,
    OfferDetails,
    PaymentRequirements,
    Penalty,
)


def normalize_offer_details(payload: dict[str, Any]) -> OfferDetails:
    offer = nested(payload, "data", "offer", default={})
    if not isinstance(offer, dict):
        offer = {}
    fare_details = offer.get("fare_details") if isinstance(offer.get("fare_details"), dict) else {}
    rules = fare_details.get("rules") if isinstance(fare_details.get("rules"), dict) else {}
    baggage = offer.get("baggage_allowance") if isinstance(offer.get("baggage_allowance"), dict) else {}
    payment = offer.get("payment_requirements") if isinstance(offer.get("payment_requirements"), dict) else {}

    return OfferDetails(
        offer_id=str(first_value(offer, "id", "offer_id", default="")),
        status=loose_label(first_value(offer, "status", "StatusCode"), BOOKING_STATUSES, "Live"),
        fare_family=code_label(first_value(fare_details, "FareFamily", "fare_family"), FARE_FAMILIES)
        if fare_details
        else None,
        fare_rules=FareRules(
            refund=_policy(rules.get("refund")),
            change=_policy(rules.get("change")),
            no_show=_policy(rules.get("no_show")),
        )
        if rules
        else None,
        baggage=_baggage(baggage),
        payment_requirements=PaymentRequirements(
            accepted_methods=[
                code_label(method, PAYMENT_METHODS)
                for method in payment.get("accepted_methods", [])
                if method
            ],
            time_limit=parse_datetime(first_value(payment, "time_limit")),
            instant_ticketing_required=payment.get("instant_ticketing_required"),
        )
        if payment
        else None,
        created_at=parse_datetime(first_value(offer, "created_at")),
        expires_at=parse_datetime(first_value(offer, "expires_at")),
        price=None,
    )


def _policy(value: Any) -> FarePolicy | None:
    if not isinstance(value, dict):
        return None
    penalty = value.get("penalty") if isinstance(value.get("penalty"), dict) else {}
    return FarePolicy(
        allowed=value.get("allowed"),
        penalty=Penalty(
            amount=to_float(first_value(penalty, "amount")),
            currency=first_value(penalty, "currency", "CurrencyCode"),
        )
        if penalty
        else None,
    )


def _baggage(value: dict[str, Any]) -> OfferBaggage | None:
    if not value:
        return None
    checked = value.get("checked") if isinstance(value.get("checked"), dict) else {}
    carry_on = value.get("carry_on") if isinstance(value.get("carry_on"), dict) else {}
    return OfferBaggage(
        checked_pieces=to_int(first_value(checked, "pieces", "quantity")),
        checked_weight_kg=to_int(first_value(checked, "max_weight_kg", "Weight", "MaxWeight")),
        carry_on_pieces=to_int(first_value(carry_on, "pieces", "quantity")),
        carry_on_weight_kg=to_int(first_value(carry_on, "max_weight_kg", "Weight", "MaxWeight")),
    )
