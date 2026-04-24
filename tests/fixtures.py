SEARCH_RESPONSE = {
    "Status": "OK",
    "data": {
        "flight_results": {
            "outbound": {
                "results": [
                    {
                        "offer_id": "offer-direct",
                        "segments": {
                            "segment_list": [
                                {
                                    "leg_data": [
                                        {
                                            "departure_info": {
                                                "airport": {"code": "KUL", "terminal": "1"},
                                                "scheduled_time": "15-May-2026 08:25 AM",
                                            },
                                            "arrival_info": {
                                                "airport": {"code": "SIN", "terminal": "2"},
                                                "scheduled_time": 1778807460,
                                            },
                                            "carrier": {
                                                "operating": "MH",
                                                "marketing": "MH",
                                                "flight_no": "501",
                                                "number": "MH501",
                                            },
                                            "equipment": {"aircraft_code": "359"},
                                            "cabin": "Y",
                                            "duration_minutes": 46,
                                            "elapsed_time": "0h 46m",
                                        }
                                    ]
                                }
                            ]
                        },
                        "stops": 0,
                        "total_journey_time": 46,
                        "pricing": {
                            "currency": "MYR",
                            "total": 97.08,
                            "base_fare": 82.91,
                            "taxes_fees": {"total_tax": 14.17},
                        },
                        "seats_remaining": 6,
                        "validating_carrier": "MH",
                        "baggage": {
                            "checked": {"pieces": 1, "weight_kg": 20},
                            "cabin_baggage": {"pieces": 1, "weight_kg": 7},
                        },
                        "refundable": False,
                    }
                ]
            }
        }
    },
}

OFFER_RESPONSE = {
    "data": {
        "offer": {
            "id": "offer-direct",
            "status": "LIVE",
            "fare_details": {
                "rules": {
                    "refund": {"allowed": True, "penalty": {"amount": 150, "currency": "MYR"}},
                    "change": {"allowed": True, "penalty": {"amount": 100, "currency": "MYR"}},
                },
                "fare_family": "FULL",
                "FareFamily": "FL",
            },
            "baggage_allowance": {
                "checked": {"quantity": 1, "max_weight_kg": 25, "MaxWeight": "30KG"},
                "carry_on": {"quantity": 1, "max_weight_kg": 7},
            },
            "payment_requirements": {
                "accepted_methods": ["CC", "BT"],
                "time_limit": 1777147572,
                "instant_ticketing_required": True,
            },
            "created_at": "20260424080612",
            "expires_at": "2026-04-24T09:39:12+00:00",
        }
    }
}

BOOKING_CREATE_RESPONSE = {
    "Result": "SUCCESS",
    "data": {
        "booking_ref": "EG4A452D",
        "BookingReference": "EG4A452D",
        "pnr": "Z65222K",
        "PNR": "Z65222K",
        "status": "CONFIRMED",
        "StatusCode": "HK",
        "offer_id": "offer-direct",
        "passengers": [
            {
                "pax_id": "PAX1",
                "title": "Mr",
                "first_name": "Alex",
                "FirstName": "Alex",
                "last_name": "Nguyen",
                "LastName": "Nguyen",
                "dob": "1990-01-01",
                "DateOfBirth": "1990-01-01",
                "nationality": "MY",
                "passport_no": "A1234567",
                "type": "ADT",
                "PaxType": "ADT",
            }
        ],
        "contact": {"email": "alex@example.com", "phone": "+60123456789"},
        "ticketing": {
            "status": "PENDING",
            "time_limit": "20260425093031",
            "ticket_numbers": [],
        },
        "created_at": "24/04/2026 08:30",
        "CreatedDateTime": 1777019431,
    },
}

BOOKING_RETRIEVE_RESPONSE = {
    "status": "ok",
    "data": {"reservation": BOOKING_CREATE_RESPONSE["data"]},
}


def airport(code: str, city: str, offset: float = 8) -> dict:
    return {
        "code": code,
        "IATA": code,
        "city": city,
        "country_code": "MY" if code == "KUL" else "SG",
        "tz_offset": offset,
        "coordinates": {"lat": 1.0, "lng": 2.0},
    }
