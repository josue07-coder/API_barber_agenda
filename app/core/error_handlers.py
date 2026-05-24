import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.config import settings
from app.core.request_context import get_request_id


logger = logging.getLogger("barber_agenda.errors")

ERROR_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "validation_error",
    429: "rate_limited",
}


def build_error_response(
    *,
    status_code: int,
    message: str,
    error_code: str | None = None,
    details: dict[str, Any] | list[Any] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    payload = {
        "success": False,
        "message": message,
        "error_code": error_code or ERROR_CODES.get(status_code, "internal_error"),
        "details": details or {},
    }

    request_id = request_id or get_request_id()
    if request_id:
        payload["request_id"] = request_id

    return payload


def log_error(request: Request, status_code: int, error_code: str, exc: Exception) -> None:
    log_method = logger.error if status_code >= 500 else logger.warning
    log_method(
        "request_error",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "error_code": error_code,
            "request_id": getattr(request.state, "request_id", None) or get_request_id(),
            "exception_type": exc.__class__.__name__,
        },
    )


def is_development() -> bool:
    return settings.ENVIRONMENT.lower() in {"development", "dev", "local", "test"}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        status_code = exc.status_code
        error_code = ERROR_CODES.get(status_code, "bad_request")
        message = exc.detail if isinstance(exc.detail, str) else "Error en la solicitud"
        log_error(request, status_code, error_code, exc)
        return JSONResponse(
            status_code=status_code,
            content=build_error_response(
                status_code=status_code,
                message=message,
                error_code=error_code,
                request_id=getattr(request.state, "request_id", None),
            ),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        status_code = 422
        error_code = "validation_error"
        log_error(request, status_code, error_code, exc)
        return JSONResponse(
            status_code=status_code,
            content=build_error_response(
                status_code=status_code,
                message="Error de validacion",
                error_code=error_code,
                details={"errors": jsonable_encoder(exc.errors())},
                request_id=getattr(request.state, "request_id", None),
            ),
        )

    @app.exception_handler(IntegrityError)
    async def integrity_exception_handler(request: Request, exc: IntegrityError):
        status_code = 409
        error_code = "conflict"
        log_error(request, status_code, error_code, exc)
        details = {"exception": exc.__class__.__name__} if is_development() else {}
        return JSONResponse(
            status_code=status_code,
            content=build_error_response(
                status_code=status_code,
                message="Conflicto de integridad de datos",
                error_code=error_code,
                details=details,
                request_id=getattr(request.state, "request_id", None),
            ),
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        status_code = 500
        error_code = "internal_error"
        log_error(request, status_code, error_code, exc)
        details = {"exception": exc.__class__.__name__} if is_development() else {}
        return JSONResponse(
            status_code=status_code,
            content=build_error_response(
                status_code=status_code,
                message="Error interno",
                error_code=error_code,
                details=details,
                request_id=getattr(request.state, "request_id", None),
            ),
        )

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(request: Request, exc: Exception):
        status_code = 500
        error_code = "internal_error"
        log_error(request, status_code, error_code, exc)
        details = {"exception": exc.__class__.__name__} if is_development() else {}
        return JSONResponse(
            status_code=status_code,
            content=build_error_response(
                status_code=status_code,
                message="Error interno",
                error_code=error_code,
                details=details,
                request_id=getattr(request.state, "request_id", None),
            ),
        )
