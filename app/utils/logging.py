import contextvars
import json
import logging
import sys
import traceback
from typing import Tuple
from urllib.parse import parse_qs

from pythonjsonlogger import json as python_jsonlogger
from fastapi import Request
from app.settings import LOGGING_LEVEL

correlation_id = contextvars.ContextVar("correlation_id", default=None)


class CustomJsonFormatter(python_jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        if not log_record.get("timestamp"):
            log_record["timestamp"] = self.formatTime(record)

        log_record["correlation_id"] = correlation_id.get()

        log_record["level"] = record.levelname

        if record.exc_info:
            log_record["exception"] = "".join(
                traceback.format_exception(*record.exc_info)
            )


def setup_logging():
    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(LOGGING_LEVEL)

    handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s %(pathname)s %(lineno)d"
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)

    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("python_multipart.multipart").setLevel(logging.ERROR)
    logging.getLogger("passlib.handlers.argon2").setLevel(logging.ERROR)


async def log_headers(request: Request) -> dict:
    headers_dict = dict(request.headers)
    for key in ("authorization", "cookie", "set-cookie"):
        if key in headers_dict:
            headers_dict[key] = "***MASKED***"

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


async def log_request_body(request: Request) -> Tuple[dict, bytes]:
    try:
        raw_body = await request.body()
        raw_body_str = raw_body.decode("utf-8", "ignore")
    except UnicodeDecodeError:
        return {}, b""  # Must return a tuple

    try:
        if request.headers.get("content-type") == "application/x-www-form-urlencoded":
            parsed_payload = parse_qs(raw_body_str)
            if "password" in parsed_payload:
                parsed_payload["password"] = ["***MASKED***"]
        else:
            parsed_payload = json.loads(raw_body_str)
    except json.JSONDecodeError:
        parsed_payload = {}

    return parsed_payload, raw_body


logger = logging.getLogger(__name__)
