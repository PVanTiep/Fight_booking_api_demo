# Flight Booking API — Interview Guide (English)
> For Java backend engineers preparing to discuss this Python/FastAPI project

---

## Table of Contents
0. [60-Second Interview Pitch](#0-60-second-interview-pitch)
1. [What Is This Project?](#1-what-is-this-project)
2. [Tech Stack & Python Ecosystem](#2-tech-stack--python-ecosystem)
3. [Project Architecture](#3-project-architecture)
4. [Project File Structure](#4-project-file-structure)
5. [API Endpoints](#5-api-endpoints)
6. [Data Models (Schemas)](#6-data-models-schemas)
7. [Business Logic — Services Layer](#7-business-logic--services-layer)
8. [Adapters — The Transformation Layer](#8-adapters--the-transformation-layer)
9. [Legacy API Client & Resilience](#9-legacy-api-client--resilience)
10. [Caching Strategy](#10-caching-strategy)
11. [Error Handling](#11-error-handling)
12. [Configuration & Environment](#12-configuration--environment)
13. [Testing Strategy](#13-testing-strategy)
14. [Key Design Decisions (Interview Gold)](#14-key-design-decisions-interview-gold)
15. [Python vs Java Quick Reference](#15-python-vs-java-quick-reference)
16. [Common Interview Questions & Answers](#16-common-interview-questions--answers)

---

## 0. 60-Second Interview Pitch

If the interviewer asks "Tell me about your solution", use this:

> I built a FastAPI Backend-for-Frontend wrapper around the legacy flight API. The legacy API works, but its contract is difficult for frontend teams: inconsistent URLs, deeply nested flight results, duplicate fields, mixed date formats, raw airline/cabin/status codes, and different error formats per endpoint. My wrapper exposes a consistent `/api/v1` REST API, validates inputs with Pydantic, calls the legacy API through one HTTP client, transforms raw provider data in adapter modules, adds readable labels, normalizes dates, paginates search results, caches stable data, and returns one unified error shape. I kept the design intentionally time-boxed for the 6-8 hour assignment: complete search-to-booking flow first, focused tests for risky transformations, and clear documentation of trade-offs and AI workflow.

Main points to remember:

- **Problem:** frontend should not understand messy legacy provider data.
- **Solution:** BFF wrapper with clean contracts and transformation adapters.
- **Python/FastAPI value:** automatic OpenAPI docs, Pydantic validation, async HTTP calls.
- **Architecture:** routes -> service -> legacy client + adapters -> clean schemas.
- **Risk handling:** retries only for safe reads, no retry for booking creation, TTL cache, unified errors.
- **Trade-off:** in-memory cache and focused tests are enough for this take-home; Redis/deployment/full observability can come later.

---

## 1. What Is This Project?

This is a **Backend-for-Frontend (BFF)** service built with **FastAPI** (Python).

**Think of it like this:** Imagine a legacy airline booking system that exposes a messy, inconsistent REST API (mixed date formats, unclear field names, old error formats). This project wraps that legacy API and exposes a clean, modern, consistent API to the frontend.

```
Frontend App
     │
     ▼
┌─────────────────────────────────┐
│   Flight Booking API (FastAPI)  │  ← THIS PROJECT
│   - Validates input             │
│   - Transforms data             │
│   - Caches results              │
│   - Handles errors gracefully   │
└─────────────────────────────────┘
     │
     ▼
Legacy Airline API (external, messy)
```

**Java analogy:** Think of this as a **Spring Boot** microservice acting as an **API Gateway/BFF** that integrates with a legacy SOAP/REST system.

---

## 2. Tech Stack & Python Ecosystem

| Python Tool | Java Equivalent | Purpose |
|---|---|---|
| **FastAPI** | Spring Boot | Web framework, routing, dependency injection |
| **Pydantic v2** | Bean Validation (Jakarta) + Jackson | Request/response validation & serialization |
| **httpx** | WebClient (Spring WebFlux) / OkHttp | Async HTTP client for external calls |
| **Uvicorn** | Embedded Tomcat / Jetty | ASGI server (runs the app) |
| **cachetools** | Caffeine / Guava Cache | In-memory TTL cache |
| **tenacity** | Spring Retry / Resilience4j | Retry logic with exponential backoff |
| **pytest** | JUnit 5 | Testing framework |
| **respx** | MockWebServer / WireMock | HTTP mocking for tests |
| **python-dotenv** | Spring Boot `application.properties` | Environment variable loading |
| **Settings dataclass** | `@ConfigurationProperties` | Typed configuration from env vars |

### Key Python Concepts for Java Engineers

**1. `async/await` — Python's version of reactive programming**
```python
# Python (FastAPI)
async def search_flights(request: FlightSearchRequest):
    result = await legacy_client.search(payload)  # non-blocking
    return result

# Java equivalent (Spring WebFlux)
Mono<FlightSearchResponse> searchFlights(FlightSearchRequest request) {
    return legacyClient.search(payload);
}
```

**2. Type Hints — Python's version of Java generics/types**
```python
# Python
def get_airport(code: str) -> Airport:
    ...

# Java
Airport getAirport(String code) { ... }
```

**3. Dataclasses / Pydantic Models — Python's version of Java POJOs**
```python
# Python (Pydantic)
class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    pax_count: int = 1

# Java (record or POJO with Lombok)
public record FlightSearchRequest(String origin, String destination, int paxCount) {}
```

**4. Decorators — similar to Java annotations**
```python
# Python
@router.post("/flights/search")
async def search_endpoint(...):
    ...

# Java
@PostMapping("/flights/search")
ResponseEntity<FlightSearchResponse> searchEndpoint(...) { ... }
```

---

## 3. Project Architecture

The project follows a **layered clean architecture**:

```
HTTP Request
     │
     ▼
┌──────────────┐
│   Routes     │  ← api/routes.py     (like @RestController in Spring)
│  (Endpoints) │
└──────────────┘
     │
     ▼
┌──────────────┐
│   Services   │  ← services.py       (like @Service in Spring)
│ (Use Cases)  │
└──────────────┘
     │          ─────────────────────
     ├──────────►  Adapters          ← adapters/*.py  (data transformation)
     │
     └──────────►  Legacy Client     ← clients/legacy.py  (HTTP calls)
                        │
                        ▼
               Legacy Airline API (external)
```

Each layer has one responsibility:
- **Routes**: Parse HTTP request, call service, return HTTP response
- **Services**: Orchestrate the business flow
- **Adapters**: Transform data between legacy format and clean format
- **Clients**: Make HTTP calls to the legacy API

---

## 4. Project File Structure

```
Flight Booking API/
├── app/
│   ├── main.py              # App startup, middleware, exception handlers
│   ├── services.py          # Business logic (FlightBookingService class)
│   ├── api/
│   │   └── routes.py        # All REST endpoint definitions
│   ├── adapters/            # Data transformation (legacy → clean format)
│   │   ├── airports.py
│   │   ├── bookings.py
│   │   ├── offers.py
│   │   ├── search.py
│   │   ├── reference.py     # Code dictionaries (e.g., "Y" → "Economy")
│   │   ├── errors.py        # Legacy error format normalizer
│   │   └── utils.py         # Shared helpers (date parsing, type conversion)
│   ├── clients/
│   │   └── legacy.py        # HTTP client + retry + circuit breaker
│   ├── schemas/             # Pydantic models (request/response contracts)
│   │   ├── common.py        # Base model, ErrorPayload
│   │   ├── search.py
│   │   ├── offers.py
│   │   ├── bookings.py
│   │   └── airports.py
│   └── core/
│       ├── config.py        # Settings loaded from .env
│       ├── cache.py         # TTL cache manager
│       └── errors.py        # Custom exceptions (AppError, LegacyAPIError)
├── tests/
│   ├── test_api.py          # API tests using httpx ASGITransport
│   ├── test_adapters.py     # Unit tests for transformation logic
│   └── fixtures.py          # Realistic mock response data
├── docs/
├── requirements.txt         # Like pom.xml (Python dependencies)
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## 5. API Endpoints

### Base URL: `/api/v1`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/flights/search` | Search for available flights |
| `GET` | `/offers/{offer_id}` | Get fare details for an offer |
| `POST` | `/bookings` | Create a booking |
| `GET` | `/bookings/{booking_reference}` | Get booking status |
| `GET` | `/airports` | List all airports |
| `GET` | `/airports/{code}` | Get single airport details |
| `GET` | `/health` | Health check, outside `/api/v1` |

### POST `/flights/search`
```json
// Request Body
{
  "origin": "KUL",
  "destination": "SIN",
  "departureDate": "2024-12-01",
  "returnDate": "2024-12-08",
  "paxCount": 2,
  "cabin": "Y"
}

// Response
{
  "page": 1,
  "pageSize": 10,
  "total": 25,
  "totalPages": 3,
  "items": [
    {
      "offerId": "abc123",
      "airline": { "code": "MH", "label": "Malaysia Airlines" },
      "origin": { "code": "KUL", "city": "Kuala Lumpur" },
      "destination": { "code": "SIN", "city": "Singapore" },
      "departureTime": "2024-12-01T08:00:00+08:00",
      "arrivalTime": "2024-12-01T09:25:00+08:00",
      "stops": 0,
      "durationMinutes": 85,
      "duration": "1h 25m",
      "price": { "amount": 250.00, "currency": "MYR" },
      "seatsRemaining": 4,
      "refundable": true
    }
  ]
}
```

**Cabin codes:**
- `Y` = Economy
- `W` = Premium Economy
- `J` = Business
- `F` = First Class

### POST `/bookings`
```json
// Request Body
{
  "offerId": "abc123",
  "passengers": [
    {
      "title": "MR",
      "firstName": "Nguyen",
      "lastName": "Van A",
      "dob": "1990-05-15",
      "nationality": "VN",
      "passportNo": "B12345678",
      "email": "nguyenvana@email.com",
      "phone": "+84901234567"
    }
  ],
  "contactEmail": "nguyenvana@email.com",
  "contactPhone": "+84901234567"
}

// Response
{
  "bookingReference": "ABC123",
  "pnr": "XYZ789",
  "status": { "code": "CONFIRMED", "label": "Confirmed" },
  "offerId": "abc123",
  "passengers": [...],
  "createdAt": "2024-11-01T10:00:00Z"
}
```

### GET `/bookings/{reference}` — with Caching
```
Headers in response:
  X-Cache: HIT   (served from cache)
  X-Cache: MISS  (fetched from upstream)
```

---

## 6. Data Models (Schemas)

> Pydantic models = Java DTOs with built-in validation

### Base Model — `APIModel`
```python
class APIModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,    # snake_case → camelCase in JSON
        populate_by_name=True,       # Accept both formats
    )
```
**Key point:** All response JSON uses **camelCase** automatically. The Python code uses **snake_case** internally. This is configured once in the base class.

### Key Models

**FlightSearchRequest**
- `origin`, `destination`: 3-letter IATA codes (e.g., "KUL"), auto-uppercased
- `departure_date`, `return_date`: Python `date` objects
- `pax_count`: 1–9 passengers
- `cabin`: one of Y/W/J/F

**FlightOfferSummary** — one search result item
- `offer_id`, `airline` (CodeLabel), `price` (Money)
- `stops`, `duration_minutes`, `duration` (human-friendly "1h 25m")
- `segments[]` — list of flight legs

**CreateBookingRequest**
- `offer_id`, `passengers[]`, `contact_email`, `contact_phone`
- Passenger: `title`, `first_name`, `last_name`, `dob`, `nationality`, `passport_no`
- Validators: non-blank names, valid email, 2-letter nationality code

**CodeLabel** — used everywhere
```python
class CodeLabel(BaseModel):
    code: str    # e.g., "MH"
    label: str   # e.g., "Malaysia Airlines"
```

**Money**
```python
class Money(BaseModel):
    amount: float
    currency: str  # e.g., "MYR"
```

---

## 7. Business Logic — Services Layer

**File:** `app/services.py`

**Class:** `FlightBookingService`

Think of this like a `@Service` class in Spring Boot. It:
1. Receives clean input from the route handler
2. Calls the legacy client to get raw data
3. Calls adapters to transform data
4. Uses the cache where appropriate
5. Returns clean output

### Method: `search_flights()`
```
1. Build legacy API payload from FlightSearchRequest
2. Call LegacyClient.search_flights(payload)
3. Extract all airport codes from raw response
4. Fetch airport metadata (for city names, timezones)
5. Call normalize_search_response(raw, airports, page, page_size)
6. Return FlightSearchResponse
```

### Method: `create_booking()`
```
1. Convert request to legacy format (camelCase → legacy field names)
2. Call LegacyClient.create_booking(payload) — NO retry (non-idempotent!)
3. Call normalize_booking_create(raw)
4. Cache booking by reference (120-second TTL)
5. Return BookingSummary
```

### Method: `get_booking(reference)`
```
1. Check booking cache (key = uppercase reference)
2. If HIT → return (cached_booking, "HIT")
3. If MISS → call LegacyClient.get_booking(reference)
4. Transform with normalize_booking_retrieve(raw)
5. Store in cache
6. Return (booking, "MISS")
```

---

## 8. Adapters — The Transformation Layer

**Files:** `app/adapters/*.py`

This is the most complex part of the project. The legacy API returns inconsistent, messy data. The adapters clean it up.

### What adapters do:
1. **Normalize field names**: Legacy uses `flightNum` → clean API uses `flight_number`
2. **Normalize date formats**: Legacy uses `"20241201080000"`, `"01-Dec-2024"`, Unix timestamps — all converted to ISO 8601
3. **Enrich codes with labels**: `"MH"` → `{"code": "MH", "label": "Malaysia Airlines"}`
4. **Calculate derived fields**: `duration_minutes` → `"1h 25m"`
5. **Handle multiple legacy formats**: The `normalize_booking_retrieve()` handles both `data.reservation` and `data.Reservation` (note the capital R!)

### Key Adapter: `search.py`
```
normalize_search_response(raw, airports, page, page_size)
  └── for each offer in raw response:
        └── _normalize_offer(offer, airports)
              ├── _normalize_segment(leg, airports)
              ├── _normalize_baggage(offer)
              └── Compute stops, total duration, price
```

### `reference.py` — Code Dictionaries
Contains Python dictionaries mapping codes to human labels:
```python
AIRLINES = {
    "MH": "Malaysia Airlines",
    "AK": "AirAsia",
    "CX": "Cathay Pacific",
    ...
}

CABINS = {
    "Y": "Economy",
    "W": "Premium Economy",
    "J": "Business",
    "F": "First Class",
}
```

### `utils.py` — Shared Helpers
- `parse_datetime()`: Handles 5 different date formats from legacy API
- `format_duration()`: Converts 85 minutes → `"1h 25m"`
- `first_value()`: Gets first non-None value from a dict (handles legacy field name variations)
- `nested()`: Safe nested dict access (like Optional chaining `?.` in modern Java)

---

## 9. Legacy API Client & Resilience

**File:** `app/clients/legacy.py`

**Class:** `LegacyClient`

This is the HTTP client that calls the upstream legacy API. It has three resilience mechanisms:

### 1. Timeouts
```python
connect_timeout = 2 seconds
request_timeout = 5 seconds
```

### 2. Retry Logic (using `tenacity`)
- Only for **safe/idempotent** calls (GET-like: search, get offer, get booking, airports)
- **NOT applied** to `create_booking` (POST that creates data — retrying would double-book!)
- Strategy: exponential backoff
- Retries on: HTTP 429, 503, 504, or timeout errors
- Config: `RETRY_ATTEMPTS=2`, `RETRY_MIN_SECONDS=0.2`, `RETRY_MAX_SECONDS=1.0`

**Java analogy:** Same as `@Retryable` in Spring Retry, or `Retry` in Resilience4j.

### 3. Circuit Breaker
```
CLOSED (normal) ──[failures >= threshold]──► OPEN (blocking)
                                                   │
                                     [cooldown elapsed]
                                                   │
                                                   ▼
                                              HALF-OPEN
                                          (test one request)
```
- Opens after `CIRCUIT_FAILURE_THRESHOLD=3` consecutive failures
- During open state: immediately returns error without calling legacy API
- Resets after `CIRCUIT_COOLDOWN_SECONDS=20`

**Java analogy:** Same as `CircuitBreaker` in Resilience4j.

### Error Handling
Every HTTP call is wrapped in try/except. Errors are converted to `LegacyAPIError`:
- Timeout → HTTP 504 with code `UPSTREAM_TIMEOUT`
- Network error → HTTP 503 with code `UPSTREAM_NETWORK_ERROR`
- Invalid JSON → HTTP 503 with code `UPSTREAM_INVALID_JSON`
- Legacy HTTP error → parsed through `normalize_legacy_error()` adapter

---

## 10. Caching Strategy

**File:** `app/core/cache.py`

**No database.** All caching is in-process memory (within the running Python process).

### Cache Manager
Uses `cachetools.TTLCache` (like a `ConcurrentHashMap` with expiry):

| Cache Name | Max Entries | TTL | What's Stored |
|---|---|---|---|
| `airports` | 512 | 24 hours | Individual airport by IATA code |
| `airport_list` | 1 | 24 hours | Full list of all airports |
| `bookings` | 512 | 120 seconds | Booking by reference |

### Cache Flow for GET `/bookings/{ref}`:
```
Request → Check cache
              │
         ┌────┴────┐
         │  HIT?   │
         └────┬────┘
         Yes  │   No
              │        ├──► Call legacy API
              │        ├──► Transform response
              │        └──► Store in cache
              │
         Return response + X-Cache: HIT/MISS header
```

---

## 11. Error Handling

### Custom Exceptions
**File:** `app/core/errors.py`

```python
class AppError(Exception):
    status_code: int   # HTTP status
    code: str          # Machine-readable code
    message: str       # Human-readable message
    details: dict      # Optional extra info

class LegacyAPIError(AppError):
    # Specifically for upstream API errors
```

### Unified Error Response Format
Every error, regardless of source, returns the same JSON envelope:
```json
{
  "error": {
    "code": "UPSTREAM_TIMEOUT",
    "message": "The upstream service did not respond in time",
    "status": 504,
    "requestId": "req_a1b2c3d4",
    "details": {}
  }
}
```

### Legacy Error Normalization
The legacy API returns errors in 4 different formats. The `errors.py` adapter normalizes all of them:
```json
// Format 1: {"error": {"code": "...", "message": "..."}}
// Format 2: {"errors": [{"code": "...", "detail": "..."}]}
// Format 3: {"fault": {"faultcode": "...", "faultstring": "..."}}
// Format 4: {"status": "error", "msg": "..."}
```
All become → `LegacyAPIError` with consistent fields.

### Middleware
**Request ID Middleware:** Every request gets a unique ID (`req_{uuid}`), added to:
- Internal request context
- Response header `X-Request-ID`
- Error payload `requestId` field

---

## 12. Configuration & Environment

**File:** `app/core/config.py`

Uses a frozen dataclass loaded from environment variables (`.env` file):

```bash
# .env.example
LEGACY_API_BASE_URL=https://mock-travel-api.vercel.app
REQUEST_TIMEOUT_SECONDS=5
CONNECT_TIMEOUT_SECONDS=2
RETRY_ATTEMPTS=2
RETRY_MIN_SECONDS=0.2
RETRY_MAX_SECONDS=1.0
BOOKING_CACHE_TTL_SECONDS=120
AIRPORT_CACHE_TTL_SECONDS=86400
CIRCUIT_FAILURE_THRESHOLD=3
CIRCUIT_COOLDOWN_SECONDS=20
SIMULATE_ISSUES=false
```

**Java analogy:** Like Spring Boot's `@ConfigurationProperties` with `application.properties`.

The `Settings` class is loaded once and cached with `@lru_cache` (Python's singleton pattern).

---

## 13. Testing Strategy

### Two Test Files

**`test_api.py`** — Integration tests (end-to-end from HTTP to response)
- Uses `httpx.ASGITransport` to call the FastAPI app in memory
- Similar idea to Spring's `MockMvc`: test HTTP behavior without starting a real server
- Replaces the real `LegacyClient` with a `FakeLegacyClient`
- Tests: correct JSON shape, camelCase fields, cache behavior, error envelopes

**`test_adapters.py`** — Unit tests (just the transformation logic)
- Tests each adapter function in isolation
- No HTTP involved
- Uses `fixtures.py` for realistic raw legacy data

### `fixtures.py`
Contains realistic mock legacy API responses (captured from real API calls). This is important because the adapters handle many edge cases — using simple mock data would miss bugs.

### Key Tests
1. **`test_search_endpoint_returns_camel_case_contract`**: Verify the response uses `offerId`, `departureTime`, not `offer_id`, `departure_time`
2. **`test_validation_errors_use_public_error_envelope`**: Submit bad data → verify error JSON format
3. **`test_booking_retrieval_sets_cache_header`**: Call twice → first is MISS, second is HIT

---

## 14. Key Design Decisions (Interview Gold)

These are the decisions interviewers love to ask about. Know the **what** and **why**.

### 1. BFF Pattern
**What:** A dedicated backend that serves only the frontend.
**Why:** The legacy API is messy. Exposing it directly to the frontend would require every frontend client to handle all the complexity. Centralizing it in a BFF means fixing it once.

### 2. Adapters as a separate layer
**What:** All data transformation is in `adapters/`, not in services or routes.
**Why:** Separation of concerns. If the legacy API changes a field name, only the adapter needs updating. Services don't know about legacy formats.

### 3. No retry on booking creation
**What:** Retries are only applied to read-like (idempotent) operations.
**Why:** Retrying a `POST /booking/create` could create duplicate bookings. Never retry non-idempotent operations.

### 4. In-process cache (no Redis)
**What:** Uses `cachetools` in-memory cache instead of external Redis.
**Why:** For a single-instance BFF, in-process cache is simpler and has zero network overhead. Trade-off: cache is lost on restart and not shared across instances.

### 5. Unified error format
**What:** All errors — validation, upstream, internal — return the same JSON shape.
**Why:** Frontend developers only need to handle one error format. Consistent `requestId` enables easy log tracing.

### 6. camelCase API contract
**What:** Public API uses camelCase; Python code uses snake_case internally.
**Why:** Frontend (JavaScript/TypeScript) uses camelCase by convention. The conversion is handled automatically by the Pydantic base model.

### 7. Circuit breaker
**What:** After 3 consecutive upstream failures, stop calling the legacy API for 20 seconds.
**Why:** Prevents cascading failures. If the legacy API is down, don't pile up threads waiting for timeouts. Fail fast and allow the legacy API to recover.

---

## 15. Python vs Java Quick Reference

| Concept | Java | Python (this project) |
|---|---|---|
| Class definition | `public class Foo { }` | `class Foo:` |
| Constructor | `public Foo(String x) { this.x = x; }` | `def __init__(self, x: str): self.x = x` |
| Async method | `Mono<T> method()` | `async def method() -> T:` |
| Await | `.block()` or reactive chain | `await some_coroutine()` |
| Null safe | `Optional<T>` | `Optional[T]` or `T | None` |
| List type | `List<String>` | `list[str]` |
| Dict type | `Map<String, Object>` | `dict[str, Any]` |
| Exception | `throw new RuntimeException()` | `raise RuntimeException()` |
| Catch exception | `catch (Exception e)` | `except Exception as e:` |
| Annotation | `@Service`, `@PostMapping` | `@router.post(...)` (decorator) |
| Interface | `interface IFoo { }` | Abstract class or Protocol |
| Enum-like | `enum Status { CONFIRMED }` | String constants or `Enum` class |
| Import | `import com.example.Foo;` | `from app.schemas import Foo` |
| Package | directory + `package` declaration | directory + `__init__.py` file |

---

## 16. Common Interview Questions & Answers

**Q: What is FastAPI and why use it over Django or Flask?**

A: FastAPI is a modern Python web framework designed for building APIs. Key advantages:
- **Automatic OpenAPI/Swagger docs** from your code
- **Native async/await support** (high performance, like Spring WebFlux)
- **Pydantic integration** for automatic request validation and response serialization
- **Very fast** (one of the fastest Python frameworks, comparable to Node.js)

Flask is older and simpler but requires extra libraries for all this. Django is full-stack (includes ORM, templates) — overkill for a pure API service.

---

**Q: Why use Pydantic for validation?**

A: Pydantic provides:
- Type validation at runtime (not just type hints which are ignored at runtime)
- Automatic serialization/deserialization
- Custom validators with `@field_validator`
- Clear error messages with field paths

Java equivalent: `@Valid` + Bean Validation + Jackson — but Pydantic does all three in one.

---

**Q: How does the caching work? What are the trade-offs?**

A: In-process TTL cache using `cachetools`:
- **Pros**: Zero latency (no network), no infrastructure dependency, simple to implement
- **Cons**: Cache lost on restart, not shared across multiple instances (horizontal scaling breaks cache)
- For a single-instance BFF, this is acceptable. If we scale to multiple instances, we'd switch to Redis.

---

**Q: Why is there no retry on the booking creation endpoint?**

A: `POST /booking/create` is **not idempotent**. If we retry after a timeout, the first request might have actually succeeded but we just didn't get the response. Retrying would create a duplicate booking. Reads (search, get offer, get booking, airports) are safe to retry because they don't modify state.

---

**Q: How does the circuit breaker work here?**

A: The `LegacyClient` tracks consecutive failures. After 3 failures, the circuit "opens" and all subsequent requests fail immediately with a 503 error — without actually calling the legacy API. After 20 seconds (cooldown), the circuit allows one test request. If it succeeds, the circuit closes. This prevents overwhelming a struggling legacy API with more requests.

---

**Q: What happens when the legacy API returns an error?**

A: The `normalize_legacy_error()` adapter handles 4 different legacy error formats and converts them all to a `LegacyAPIError` exception with consistent fields. The global exception handler in `main.py` catches it and returns the unified error envelope to the client.

---

**Q: How do you run this project?**

A:
```bash
# With Docker
docker-compose up

# Without Docker
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# Run tests
pytest -q

# API docs (Swagger UI)
http://localhost:8000/docs
```

---

**Q: What is ASGI vs WSGI?**

A: 
- **WSGI** (older): Synchronous, one request at a time per thread — like a traditional Servlet container
- **ASGI** (modern): Asynchronous, supports WebSockets, async I/O — like Netty or Spring WebFlux

FastAPI uses ASGI (run by Uvicorn). This is why it can handle many concurrent connections efficiently.

---

*Good luck with your interview! The key is understanding the BFF pattern, adapter layer, and resilience patterns — those are the most interview-worthy topics.*
