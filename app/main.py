from __future__ import annotations

from contextlib import asynccontextmanager
import uuid

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.clients.legacy import LegacyClient
from app.core.cache import CacheManager
from app.core.config import get_settings
from app.core.errors import AppError
from app.schemas.common import ErrorPayload, ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.legacy_client = LegacyClient(settings)
    app.state.cache = CacheManager(settings)
    yield
    await app.state.legacy_client.aclose()


app = FastAPI(
    title="Flight Booking API Wrapper",
    description=(
        "Frontend-friendly BFF over the legacy flight API. "
        "It normalizes nested payloads, mixed date formats, cryptic codes, and inconsistent errors."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return _error_response(
        request,
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(
        request,
        code="VALIDATION_ERROR",
        message="Request validation failed.",
        status_code=422,
        details={"fields": jsonable_encoder(exc.errors())},
    )


def _error_response(
    request: Request,
    *,
    code: str,
    message: str,
    status_code: int,
    details: dict,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "req_unknown")
    body = ErrorResponse(
        error=ErrorPayload(
            code=code,
            message=message,
            status=status_code,
            requestId=request_id,
            details=details,
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(body.model_dump(by_alias=True)),
    )


app.include_router(router)
