# Flight Booking API Wrapper

**Live:** https://fight-booking-api-demo.onrender.com/docs

FastAPI Backend-for-Frontend wrapper for the legacy flight API at `https://mock-travel-api.vercel.app`.

The wrapper exposes clean, frontend-friendly REST endpoints while hiding the legacy API's inconsistent URLs, nested response shapes, duplicate fields, mixed date formats, raw codes, and inconsistent error formats.

## What It Provides

- Consistent public API under `/api/v1`.
- Flattened paginated flight search responses.
- Offer details with normalized fare rules, baggage, payment methods, and readable labels.
- Booking creation with wrapper-side passenger/contact validation.
- Booking retrieval with short TTL caching and `X-Cache` headers.
- Airport metadata normalization and 24h TTL caching.
- Unified error envelope for validation and legacy API failures.
- Retry/timeout behavior for safe upstream reads.
- OpenAPI docs at `/docs`.

## Tech Stack

- Python 3.12
- FastAPI
- Pydantic v2
- httpx
- cachetools
- tenacity
- pytest

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Run locally:

```bash
.venv/bin/uvicorn app.main:app --reload
```

Open:

- API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## Configuration

Environment variables are documented in `.env.example`.

Important settings:

- `LEGACY_API_BASE_URL`: upstream legacy API base URL.
- `SIMULATE_ISSUES`: set to `true` to pass `simulate_issues=true` to upstream calls.
- `BOOKING_CACHE_TTL_SECONDS`: TTL for booking retrieval cache.
- `AIRPORT_CACHE_TTL_SECONDS`: TTL for airport metadata cache.
- `RETRY_ATTEMPTS`: retry attempts for safe upstream reads.

## Public Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/flights/search` | Search flights and return paginated clean offers. |
| `GET` | `/api/v1/offers/{offer_id}` | Get normalized offer details. |
| `POST` | `/api/v1/bookings` | Create a booking after local validation. |
| `GET` | `/api/v1/bookings/{booking_reference}` | Retrieve a booking summary with cache headers. |
| `GET` | `/api/v1/airports` | List normalized airports. |
| `GET` | `/api/v1/airports/{code}` | Get one normalized airport. |
| `GET` | `/health` | Health check. |

## Example Requests

Search flights:

```bash
curl -sS -X POST "http://127.0.0.1:8000/api/v1/flights/search?pageSize=5" \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "KUL",
    "destination": "SIN",
    "departureDate": "2026-05-15",
    "paxCount": 1,
    "cabin": "Y"
  }'
```

Get offer details:

```bash
curl -sS "http://127.0.0.1:8000/api/v1/offers/{offer_id}"
```

Create booking:

```bash
curl -sS -X POST "http://127.0.0.1:8000/api/v1/bookings" \
  -H "Content-Type: application/json" \
  -d '{
    "offerId": "{offer_id}",
    "passengers": [
      {
        "title": "Mr",
        "firstName": "Alex",
        "lastName": "Nguyen",
        "dob": "1990-01-01",
        "nationality": "MY",
        "passportNo": "A1234567",
        "email": "alex@example.com",
        "phone": "+60123456789"
      }
    ],
    "contactEmail": "alex@example.com",
    "contactPhone": "+60123456789"
  }'
```

Retrieve booking:

```bash
curl -i "http://127.0.0.1:8000/api/v1/bookings/{booking_reference}"
```

## Error Shape

All wrapper-managed errors use one response shape:

```json
{
  "error": {
    "code": "UPSTREAM_TIMEOUT",
    "message": "The flight provider did not respond in time.",
    "status": 503,
    "requestId": "req_abc123",
    "details": {}
  }
}
```

## Testing

```bash
.venv/bin/pytest -q
```

Current focused tests cover:

- Search transformation and label enrichment.
- Offer detail normalization.
- Booking confirmation normalization.
- Public validation error envelope.
- Booking cache `MISS` then `HIT`.

## Documentation

- Step-by-step demo guide with real examples: `docs/demo-guide.md`
- System architecture and data flow diagrams: `docs/diagrams.md`
- System design and implementation plan: `docs/implementation-plan.md`
- AI workflow notes: `docs/ai-workflow.md`
