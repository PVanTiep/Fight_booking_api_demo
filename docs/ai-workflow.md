# AI-Assisted Development Workflow

This assignment explicitly evaluates AI-assisted engineering, so the workflow is documented as part of the deliverable.

## Tools Used

- Codex-style AI pair programming for requirement analysis, planning, implementation, and test iteration.
- Live legacy API inspection with `curl`.
- Local verification with `pytest` and direct ASGI requests.

## Prompts and Tasks

Useful prompts:

- "Read the assessment carefully and identify what the employer will value."
- "Create a system design plan with Mermaid flows for the wrapper API."
- "Compress the three-day plan into an 8-hour execution plan."
- "Implement the FastAPI wrapper now, prioritizing a working vertical slice."

AI was useful for:

- Extracting requirements from the Word document.
- Turning rubric language into concrete implementation priorities.
- Drafting architecture boundaries and Mermaid diagrams.
- Generating the initial schemas, adapters, route structure, and tests.

## Human Validation and Course Correction

The AI-generated direction was validated against the live legacy API instead of relying only on the sparse OpenAPI schema. The live checks revealed:

- Search responses have deeply nested `segment_list` and `leg_data`.
- Offer details contain conflicting baggage fields such as `max_weight_kg` and `MaxWeight`.
- Booking creation returns duplicated fields such as `booking_ref`, `BookingReference`, `pnr`, and `PNR`.
- Error responses differ across endpoints.

One course correction: the original plan was a three-day showcase. After reviewing the time guideline, it was compressed into an 8-hour execution plan with a clear cut line: core flow, clean contracts, focused tests, and documentation first; Docker, Redis, deployment, and exhaustive edge cases later.

Another course correction: the first API test approach used `fastapi.testclient`, which hung with the installed Starlette/TestClient stack. Direct `httpx.ASGITransport` requests worked, so the tests were rewritten to exercise the same ASGI app without that tooling issue.

## Validation Habits

- Read the source assignment directly from `backend-assessment.docx`.
- Queried the live legacy API for OpenAPI, search, offer, booking create, booking retrieve, airport, and error samples.
- Kept transformation logic separate from routes so it could be unit tested with captured fixtures.
- Ran syntax compilation with `python -m compileall`.
- Ran the focused test suite with `pytest`.

## What AI Accelerated

AI significantly accelerated the translation from a broad take-home brief into a concrete architecture and implementation checklist. It also helped keep the code structure consistent across routes, schemas, adapters, and tests.

## Where Human Judgment Mattered

The important decisions were scope and validation: choosing REST/FastAPI, cutting the plan to fit 8 hours, not retrying non-idempotent booking creation, caching stable metadata but not live prices, and verifying generated code against real legacy payloads.
