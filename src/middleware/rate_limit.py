"""Small in-memory rate limiter suitable for local/demo deployments."""

import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Limit requests per client IP over a rolling one-minute window."""

    def __init__(self, app, requests_per_minute: int) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.buckets: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Reject requests that exceed the configured rolling-window budget."""
        client = request.client.host if request.client else "unknown"
        now = time.time()
        bucket = self.buckets[client]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= self.requests_per_minute:
            return Response("Rate limit exceeded", status_code=429)
        bucket.append(now)
        return await call_next(request)
