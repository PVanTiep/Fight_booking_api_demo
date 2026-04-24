# Flight Booking API Wrapper

[![CI](https://github.com/PVanTiep/Fight_booking_api_demo/actions/workflows/ci.yml/badge.svg)](https://github.com/PVanTiep/Fight_booking_api_demo/actions/workflows/ci.yml)
[![Live on Render](https://img.shields.io/badge/Live-Render-46E3B7?logo=render)](https://fight-booking-api-demo.onrender.com/docs)

FastAPI Backend-for-Frontend wrapper for the legacy flight API at `https://mock-travel-api.vercel.app`.

The wrapper exposes clean, frontend-friendly REST endpoints while hiding the legacy API's inconsistent URLs, nested response shapes, duplicate fields, mixed date formats, raw codes, and inconsistent error formats.

---

## Table of Contents

- [Live Demo](#live-demo)
- [What It Provides](#what-it-provides)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Public Endpoints](#public-endpoints)
- [Example Requests](#example-requests)
- [Error Shape](#error-shape)
- [Testing](#testing)
- [Documentation](#documentation)

---

## Live Demo

| | |
|---|---|
| **Swagger UI** | https://fight-booking-api-demo.onrender.com/docs |
| **Health check** | https://fight-booking-api-demo.onrender.com/health |

> **New here?** Read the [step-by-step demo guide](docs/demo-guide.md) — it walks through a full search → book → retrieve flow with real copy-paste values.

---

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

---

## Tech Stack

- Python 3.12
- FastAPI
- Pydantic v2
- httpx
- cachetools
- tenacity
- pytest

---

## Quick Start

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/uvicorn app.main:app --reload
```

Open:

- API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

---

## Configuration

Environment variables are documented in `.env.example`.

| Variable | Default | Description |
|---|---|---|
| `LEGACY_API_BASE_URL` | `https://mock-travel-api.vercel.app` | Upstream legacy API base URL |
| `SIMULATE_ISSUES` | `false` | Pass `simulate_issues=true` to upstream |
| `BOOKING_CACHE_TTL_SECONDS` | `120` | TTL for booking retrieval cache |
| `AIRPORT_CACHE_TTL_SECONDS` | `86400` | TTL for airport metadata cache |
| `RETRY_ATTEMPTS` | `2` | Retry attempts for safe upstream reads |
| `CIRCUIT_FAILURE_THRESHOLD` | `3` | Failures before circuit opens |
| `CIRCUIT_COOLDOWN_SECONDS` | `20` | Cooldown before circuit resets |

---

## Public Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/flights/search` | Search flights — returns paginated, normalized offers |
| `GET` | `/api/v1/offers/{offer_id}` | Offer details — fare rules, baggage, payment methods |
| `POST` | `/api/v1/bookings` | Create a booking after local validation |
| `GET` | `/api/v1/bookings/{booking_reference}` | Retrieve booking with `X-Cache` header |
| `GET` | `/api/v1/airports` | List all normalized airports |
| `GET` | `/api/v1/airports/{code}` | Get one airport by IATA code |
| `GET` | `/health` | Health check |

---

## Example Requests

Search flights:

```bash
curl -sS -X POST "https://fight-booking-api-demo.onrender.com/api/v1/flights/search?pageSize=5" \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "KUL",
    "destination": "SIN",
    "departureDate": "2026-06-01",
    "paxCount": 1,
    "cabin": "Y"
  }'
```

Get offer details:

```bash
curl -sS "https://fight-booking-api-demo.onrender.com/api/v1/offers/{offer_id}"
```

Create booking:

```bash
curl -sS -X POST "https://fight-booking-api-demo.onrender.com/api/v1/bookings" \
  -H "Content-Type: application/json" \
  -d '{
    "offerId": "{offer_id}",
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
  }'
```

Retrieve booking (run twice to see `X-Cache: MISS` → `HIT`):

```bash
curl -si "https://fight-booking-api-demo.onrender.com/api/v1/bookings/{booking_reference}"
```

---

## Error Shape

All errors — validation, upstream failures, 404s — use one response shape:

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

---

## Testing

```bash
.venv/bin/pytest -q --cov=app --cov-report=term-missing
```

Tests cover:

- Search transformation, pagination, and label enrichment
- Offer detail normalization and price extraction
- All four legacy error response formats
- Booking create and retrieve normalization
- Cache `MISS` → `HIT` flow
- Input validation (past dates, bad emails, oversized passenger lists)
- All API endpoints including error envelope shape

---

## Documentation

| Document | Description |
|---|---|
| [Demo Guide](docs/demo-guide.md) | Step-by-step walkthrough with real copy-paste values |
| [System Diagrams](docs/diagrams.md) | Architecture diagram and request/response data flow |
| [Implementation Plan](docs/implementation-plan.md) | Design decisions and technical notes |
| [AI Workflow](docs/ai-workflow.md) | Notes on the AI-assisted development process |
