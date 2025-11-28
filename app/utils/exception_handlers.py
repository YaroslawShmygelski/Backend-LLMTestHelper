import logging

from fastapi import Request
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.settings import ENV
from app.utils.exception_types import BasicAppError
from app.utils.logging import correlation_id

logger = logging.getLogger(__name__)


async def expected_exception_handler(
    request: Request,
    exc: BasicAppError,
) -> JSONResponse:
    cid = correlation_id.get()
    logger.error(
        "Handled Application Error",
        extra={
            "status_code": exc.status_code,
            "error_message": exc.message,
            "cid": cid,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "correlation_id": cid,
        },
    )


async def unexpected_exception_handler(request: Request, exc: Exception):
    cid = correlation_id.get()
    logger.exception(
        "Unhandled exception", extra={"path": request.url.path, "cid": cid}
    )
    body = {
        "error": "INTERNAL_ERROR",
        "message": "Internal Server Error",
        "correlation_id": cid,
    }
    if ENV == "dev":
        body["error_detail"] = str(exc)
    return JSONResponse(status_code=500, content=body)


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    cid = correlation_id.get()
    logger.error(
        "HTTPException",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "detail": exc.detail,
            "cid": cid,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP_ERROR", "message": exc.detail, "correlation_id": cid},
    )
