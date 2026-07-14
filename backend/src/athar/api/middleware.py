"""
Request logging and metrics middleware.
Records latency, method, path, and status code for every request.
"""

from __future__ import annotations

import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Structured request/response logging middleware."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()

        # Process request
        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000

        # Skip logging for health checks to reduce noise
        if request.url.path not in ("/api/health", "/"):
            logger.info(
                "method=%s path=%s status=%d duration_ms=%.1f",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )

        # Inject timing header
        response.headers["X-Process-Time-Ms"] = str(round(duration_ms, 1))
        return response
