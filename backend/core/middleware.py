"""
NSBM EduSphere — Core Middleware
Correlation ID tracing and standard request processing middleware
"""
import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from backend.core.logging import logger

CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Extracts or generates an X-Correlation-ID for distributed tracing across services.
    Propagates the correlation ID into request state and the outbound response header.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = request.headers.get(CORRELATION_ID_HEADER)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        request.state.correlation_id = correlation_id
        response: Response = await call_next(request)
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs incoming HTTP requests, response status, and execution duration in milliseconds"""
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        correlation_id = getattr(request.state, "correlation_id", "N/A")

        # Skip logging noisy static assets
        if not request.url.path.startswith("/assets"):
            logger.info(
                f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)",
                extra={
                    "correlation_id": correlation_id,
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                }
            )

        return response
