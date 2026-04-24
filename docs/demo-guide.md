# Demo Guide — Flight Booking API

Live API: **https://fight-booking-api-demo.onrender.com/docs**

---

## The Full Flow

Every booking follows the same four steps. Each step feeds data into the next.

```
1. Search flights      →  get offer_id
2. View offer details  →  confirm fare rules, baggage, payment
3. Create booking      →  get booking_reference
4. Retrieve booking    →  verify cache (MISS → HIT)
```

---

## Step 0 — Open the Swagger UI

Go to: **https://fight-booking-api-demo.onrender.com/docs**

You will see all 7 endpoints grouped by tag. Every endpoint has a **Try it out** button — click it to make the form editable, fill in the values, then click **Execute**.

---

## Step 1 — Search Flights

**Endpoint:** `POST /api/v1/flights/search`

### What to fill in

**Query parameter** (top of the form):
| Field | Value |
|---|---|
| `pageSize` | `5` |

**Request body** (paste this exactly):
```json
{
  "origin": "KUL",
  "destination": "SIN",
  "departureDate": "2026-06-01",
  "paxCount": 1,
  "cabin": "Y"
}
```

### What you get back

```json
{
  "page": 1,
  "pageSize": 5,
  "total": 14,
  "totalPages": 3,
  "items": [
    {
      "offerId": "18ee03e836b8e3f7",
      "airline": { "code": "MH", "label": "Malaysia Airlines" },
      "origin": { "code": "KUL", "city": "Kuala Lumpur", "terminal": "1" },
      "destination": { "code": "SIN", "city": "Singapore", "terminal": "1" },
      "departureTime": "2026-06-01T18:50:00+08:00",
      "arrivalTime": "2026-06-01T20:00:00+08:00",
      "stops": 0,
      "duration": "1h 10m",
      "price": {
        "total": { "amount": 87.85, "currency": "MYR" },
        "base":  { "amount": 76.08, "currency": "MYR" },
        "taxes": { "amount": 11.77, "currency": "MYR" }
      },
      "baggage": {
        "checkedPieces": 1, "checkedWeightKg": 20,
        "cabinPieces": 1,   "cabinWeightKg": 7
      },
      "seatsRemaining": 1
    }
    // ... more offers
  ]
}
```

### What to copy

**Copy the `offerId`** from whichever flight you want — you need it in Steps 2 and 3.

> Example: `18ee03e836b8e3f7`

### Demo talking points
- `total: 14` — the legacy API returned 14 raw results; the BFF paginates them cleanly.
- `departureTime` is in local timezone (`+08:00`), not raw UTC — the BFF normalised it.
- `airline.label` is `"Malaysia Airlines"`, not the raw code `"MH"`.
- `duration: "1h 10m"` is a human-readable label, not raw minutes.

---

## Step 2 — View Offer Details

**Endpoint:** `GET /api/v1/offers/{offer_id}`

### What to fill in

| Field | Value |
|---|---|
| `offer_id` | `18ee03e836b8e3f7` ← paste from Step 1 |

### What you get back

```json
{
  "offerId": "18ee03e836b8e3f7",
  "status": { "code": "LIVE", "label": "Live" },
  "fareRules": {
    "refund": { "allowed": false, "penalty": { "amount": 150.0, "currency": "MYR" } },
    "change": { "allowed": true,  "penalty": { "amount": 75.0,  "currency": "MYR" } },
    "noShow": { "allowed": null,  "penalty": { "amount": 300.0, "currency": "MYR" } }
  },
  "baggage": {
    "checkedPieces": 1, "checkedWeightKg": 30,
    "carryOnPieces": 1, "carryOnWeightKg": 7
  },
  "paymentRequirements": {
    "acceptedMethods": [
      { "code": "CC", "label": "Credit card" },
      { "code": "DC", "label": "Debit card" },
      { "code": "BT", "label": "Bank transfer" }
    ],
    "timeLimit": "2026-04-26T07:36:24+00:00",
    "instantTicketingRequired": false
  },
  "expiresAt": "2026-04-24T14:14:24+00:00"
}
```

### Demo talking points
- `fareRules` shows refund/change/no-show policies with penalty amounts — the legacy API buries this in nested structures; the BFF surfaces it cleanly.
- `acceptedMethods` labels are human-readable (`"Credit card"` not `"CC"`).
- `timeLimit` tells the frontend how long the passenger has to pay.

---

## Step 3 — Create a Booking

**Endpoint:** `POST /api/v1/bookings`

### What to fill in

```json
{
  "offerId": "18ee03e836b8e3f7",
  "passengers": [
    {
      "firstName": "Alex",
      "lastName": "Nguyen",
      "dob": "1990-01-15",
      "nationality": "MY",
      "passportNo": "A1234567",
      "email": "alex@example.com",
      "phone": "+60123456789"
    }
  ],
  "contactEmail": "alex@example.com",
  "contactPhone": "+60123456789"
}
```

### What you get back (HTTP 201)

```json
{
  "bookingReference": "EG6E1D13",
  "pnr": "Q96715N",
  "status": { "code": "HK", "label": "Confirmed" },
  "offerId": "18ee03e836b8e3f7",
  "passengers": [
    {
      "passengerId": "PAX1",
      "firstName": "Alex",
      "lastName": "Nguyen",
      "dateOfBirth": "1990-01-15",
      "nationality": "MY",
      "passportNo": "A1234567",
      "passengerType": { "code": "ADT", "label": "Adult" }
    }
  ],
  "contact": {
    "email": "alex@example.com",
    "phone": "+60123456789"
  },
  "ticketing": {
    "status": { "code": "PENDING", "label": "Pending ticketing" },
    "timeLimit": "2026-04-26T08:36:32+00:00",
    "ticketNumbers": []
  },
  "createdAt": "2026-04-24T13:36:32+00:00"
}
```

### What to copy

**Copy the `bookingReference`** — you need it in Step 4.

> Example: `EG6E1D13`

### Demo talking points
- Response is **HTTP 201** (Created), not 200 — correct REST semantics.
- `status.label` is `"Confirmed"` (not raw code `"HK"` from the legacy API).
- `passengerType.label` is `"Adult"` (not raw `"ADT"`).
- The BFF validated the passenger and contact data **before** sending to the legacy API — try submitting with a bad email like `"not-an-email"` to see the validation error.

### Bonus — show a validation error

Submit this to trigger a clean 422 response:
```json
{
  "offerId": "18ee03e836b8e3f7",
  "passengers": [],
  "contactEmail": "not-an-email"
}
```

Response:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "status": 422,
    "requestId": "req_abc123",
    "details": { "fields": [...] }
  }
}
```

---

## Step 4 — Retrieve Booking (with Cache)

**Endpoint:** `GET /api/v1/bookings/{booking_reference}`

### What to fill in

| Field | Value |
|---|---|
| `booking_reference` | `EG6E1D13` ← paste from Step 3 |

### Call it twice — this is the key demo moment

**First call** — response header:
```
X-Cache: MISS
```
The BFF fetched it from the legacy API and stored it in cache.

**Second call** — response header:
```
X-Cache: HIT
```
The BFF served it directly from memory — zero upstream calls.

> In Swagger UI, look at the **Response headers** section after each Execute.

### Demo talking points
- `X-Cache: MISS` → `HIT` shows the TTL caching working in real time.
- The response body is identical both times — the frontend gets a consistent contract.
- Cache TTL is configurable via `BOOKING_CACHE_TTL_SECONDS` env var.

---

## Step 5 (Bonus) — Airport Data

### List all airports

**Endpoint:** `GET /api/v1/airports`

No input needed. Returns all available airports with city, country, timezone offset, and coordinates.

### Get one airport

**Endpoint:** `GET /api/v1/airports/{code}`

| Field | Value |
|---|---|
| `code` | `KUL` |

Try also: `SIN`, `BKK`, `NRT`, `DXB`

---

## Validation Errors to Demo

These all return `{"error": {"code": "VALIDATION_ERROR", ...}}` — every error has the same envelope.

| What to try | Why it fails |
|---|---|
| `departureDate: "2020-01-01"` | Date is in the past |
| `origin: "KUL"` + `destination: "KUL"` | Same origin and destination |
| `cabin: "X"` | Unsupported cabin class |
| `passengers: []` | At least 1 passenger required |
| `contactEmail: "bademail"` | Missing `@` |
| `GET /api/v1/airports/kuL` | Code must be 3 uppercase letters |
| `GET /api/v1/nonexistent` | 404 uses the same error envelope |

---

## Quick Reference — All Endpoints

| Method | Endpoint | Input needed |
|---|---|---|
| `GET` | `/health` | None |
| `POST` | `/api/v1/flights/search` | origin, destination, departureDate |
| `GET` | `/api/v1/offers/{offer_id}` | offer_id from search |
| `POST` | `/api/v1/bookings` | offer_id + passenger details |
| `GET` | `/api/v1/bookings/{booking_reference}` | booking_reference from booking |
| `GET` | `/api/v1/airports` | None |
| `GET` | `/api/v1/airports/{code}` | 3-letter IATA code |
