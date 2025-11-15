import logging
import time
import uuid

from fastapi import Request, FastAPI
from starlette.types import Scope, Receive, Send

from app.utils.logging import correlation_id, log_headers, log_request_body

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):

        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope, receive=receive)

        cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        correlation_id.set(cid)

        parsed_payload, raw_body = await log_request_body(request)

        headers_to_log = await log_headers(request)

        async def receive_with_body():
            return {
                "type": "http.request",
                "body": raw_body,
                "more_body": False,
            }

        logger.info(
            "HTTP Request Interceptor",
            extra={
                "headers": headers_to_log,
                "payload": parsed_payload,
                "correlation_id": cid,
            },
        )

        status_code = None
        bytes_sent = 0

        async def send_wrapper(message):
            nonlocal status_code, bytes_sent

            # Read status code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            # Count response body size (but don't store it)
            if message["type"] == "http.response.body":
                body = message.get("body", b"")
                bytes_sent += len(body)

            return await send(message)

        start_time = time.time()

        response = await self.app(scope, receive_with_body, send_wrapper)

        execution_time = round((time.time() - start_time), 4)

        logger.info(
            "HTTP Response",
            extra={
                "method": request.method,
                "status_code": status_code,
                "path": request.url.path,
                "duration_s": execution_time,
                "bytes_sent": bytes_sent,
                "correlation_id": correlation_id.get(),
            },
        )

        return response
