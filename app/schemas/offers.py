from __future__ import annotations

from app.schemas.common import APIModel, CodeLabel, Money


class Penalty(APIModel):
    amount: float | None = None
    currency: str | None = None


class FarePolicy(APIModel):
    allowed: bool | None = None
    penalty: Penalty | None = None


class FareRules(APIModel):
    refund: FarePolicy | None = None
    change: FarePolicy | None = None
    no_show: FarePolicy | None = None


class OfferBaggage(APIModel):
    checked_pieces: int | None = None
    checked_weight_kg: int | None = None
    carry_on_pieces: int | None = None
    carry_on_weight_kg: int | None = None


class PaymentRequirements(APIModel):
    accepted_methods: list[CodeLabel]
    time_limit: str | None = None
    instant_ticketing_required: bool | None = None


class OfferDetails(APIModel):
    offer_id: str
    status: CodeLabel
    fare_family: CodeLabel | None = None
    fare_rules: FareRules | None = None
    baggage: OfferBaggage | None = None
    payment_requirements: PaymentRequirements | None = None
    created_at: str | None = None
    expires_at: str | None = None
    price: Money | None = None
