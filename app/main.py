from __future__ import annotations

import logging
import logging.config
from contextlib import asynccontextmanager
import uuid

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import router
from app.clients.legacy import LegacyClient
from app.core.cache import CacheManager
from app.core.config import get_settings
from app.core.errors import AppError
from app.schemas.common import ErrorPayload, ErrorResponse

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["console"]},
    }
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.legacy_client = LegacyClient(settings)
    app.state.cache = CacheManager(settings)
    logger.info("startup complete legacy_api=%s", settings.legacy_api_base_url)
    yield
    await app.state.legacy_client.aclose()
    logger.info("shutdown complete")


app = FastAPI(
    title="Flight Booking API Wrapper",
    description=(
        "Frontend-friendly BFF over the legacy flight API. "
        "It normalizes nested payloads, mixed date formats, cryptic codes, and inconsistent errors."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Cache"],
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
    upstream = getattr(exc, "upstream_payload", None)
    if upstream is not None:
        logger.error(
            "upstream error code=%s status=%s request_id=%s payload=%s",
            exc.code,
            exc.status_code,
            getattr(request.state, "request_id", "req_unknown"),
            upstream,
        )
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


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    _HTTP_CODES = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}
    return _error_response(
        request,
        code=_HTTP_CODES.get(exc.status_code, f"HTTP_{exc.status_code}"),
        message=str(exc.detail),
        status_code=exc.status_code,
        details={},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled exception request_id=%s",
        getattr(request.state, "request_id", "req_unknown"),
    )
    return _error_response(
        request,
        code="INTERNAL_ERROR",
        message="An unexpected error occurred.",
        status_code=500,
        details={},
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
