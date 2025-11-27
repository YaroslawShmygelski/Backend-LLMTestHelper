import asyncio
import contextvars
import json
import logging
import sys
import traceback
from datetime import datetime, UTC
from pathlib import Path
from typing import Tuple
from urllib.parse import parse_qs

from pythonjsonlogger import json as python_jsonlogger
from fastapi import Request
from app.settings import LOGGING_LEVEL, ENV

correlation_id = contextvars.ContextVar("correlation_id", default=None)
SENSITIVE_KEYS = {
    "password",
    "secret",
    "authorization",
    "jwt",
    "access_token",
    "refresh_token",
}


class CustomJsonFormatter(python_jsonlogger.JsonFormatter):
    def add_fields(self, log_data, record, message_dict):
        super().add_fields(log_data, record, message_dict)

        log_data["path"] = record.pathname
        log_data["line"] = record.lineno

        log_data.pop("pathname", None)
        log_data.pop("lineno", None)

        if not log_data.get("timestamp"):
            log_data["timestamp"] = datetime.fromtimestamp(
                record.created, UTC
            ).isoformat()

        log_data["correlation_id"] = correlation_id.get()

        log_data["path"] = str(
            Path(record.pathname).resolve().relative_to(Path().resolve())
        )

        log_data["level"] = record.levelname

        if record.exc_info:
            log_data["exception"] = "".join(
                traceback.format_exception(*record.exc_info)
            )

    def format(self, record):
        base = super().format(record)
        if record.exc_info:
            return f"{base}\n{self.formatException(record.exc_info)}"
        return base


def setup_logging():
    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(LOGGING_LEVEL)

    json_handler = logging.StreamHandler(sys.stdout)

    if ENV == "dev":
        json_formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s %(pathname)s %(lineno)d",
            json_indent=4,
        )
    else:
        json_formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s %(pathname)s %(lineno)d"
        )

    json_handler.setFormatter(json_formatter)
    root.addHandler(json_handler)

    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if ENV == "prod" else logging.WARNING
    )
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("python_multipart.multipart").setLevel(logging.ERROR)
    logging.getLogger("passlib.handlers.argon2").setLevel(logging.ERROR)


def sanitize(obj):
    if isinstance(obj, dict):
        cleaned = {}
        for key, value in obj.items():
            if any(s in key.lower() for s in SENSITIVE_KEYS):
                cleaned[key] = "***"
            else:
                cleaned[key] = sanitize(value)
        return cleaned

    if isinstance(obj, list):
        return [sanitize(item) for item in obj]

    return obj


def sanitize_result(func):
    async def async_wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        return sanitize(result)

    def sync_wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return sanitize(result)

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


@sanitize_result
async def log_headers(request: Request) -> dict:
    headers_dict = dict(request.headers)

    client_ip = request.client.host if request.client else None
    real_ip = (
        headers_dict.get("x-forwarded-for")
        or headers_dict.get("x-real-ip")
        or headers_dict.get("cf-connecting-ip")
        or client_ip
    )

    useful_headers = {
        **headers_dict,
        "real_ip": real_ip,
        "accept_language": headers_dict.get("accept-language"),
        "origin": headers_dict.get("origin"),
        "referer": headers_dict.get("referer"),
        "forwarded_for": headers_dict.get("x-forwarded-for"),
        "proto": headers_dict.get("x-forwarded-proto"),
    }

    return useful_headers


@sanitize_result
async def log_request_body(request: Request) -> Tuple[dict, bytes]:
    try:
        raw_body = await request.body()
        raw_body_str = raw_body.decode("utf-8", "ignore")
    except UnicodeDecodeError:
        return {}, b""  # Must return a tuple

    try:
        if request.headers.get("content-type") == "application/x-www-form-urlencoded":
            parsed_payload = parse_qs(raw_body_str)
            parsed_payload = sanitize(parsed_payload)
        else:
            parsed_payload = json.loads(raw_body_str)
    except json.JSONDecodeError:
        parsed_payload = {}

    return parsed_payload, raw_body


@sanitize_result
async def log_response_body(response_body_chunks: list[bytes]) -> str | dict:
    raw_body = b"".join(response_body_chunks)

    try:
        text = raw_body.decode("utf-8")
    except Exception:
        text = "<binary response body>"
    try:
        response_body = json.loads(text)
    except Exception:
        response_body = text

    return response_body


logger = logging.getLogger(__name__)
