"""Rate limiting middleware for abuse protection (F089)."""
import asyncio
import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory rate limiter; tokens are cleared on shutdown."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_times: dict[str, list[float]] = defaultdict(list)
        self.lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if self.requests_per_minute <= 0:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60

        async with self.lock:
            self.request_times[client_ip] = [
                t for t in self.request_times[client_ip] if t > window_start
            ]
            request_count = len(self.request_times[client_ip])

            if request_count >= self.requests_per_minute:
                return Response("Rate limit exceeded", status_code=429)

            self.request_times[client_ip].append(now)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - request_count - 1
        )
        return response
