"""Redis-backed rate limiting shared by all API workers."""

import logging

from fastapi import Request
from redis.asyncio import Redis
from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from .config import settings

logger = logging.getLogger(__name__)

_FIXED_WINDOW = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return {current, ttl}
"""


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply a global limit and a stricter limit to expensive Elo requests."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if request.url.path == "/health":
            return await call_next(request)

        redis: Redis = request.app.state.redis
        client_ip = request.client.host if request.client else "unknown"
        limits = [
            (
                "global",
                settings.rate_limit_requests,
                settings.rate_limit_window_seconds,
            )
        ]
        if request.url.path == "/analytics/elo":
            limits.append(
                (
                    "elo",
                    settings.elo_rate_limit_requests,
                    settings.rate_limit_window_seconds,
                )
            )

        try:
            for bucket, maximum, window in limits:
                key = f"rate-limit:{bucket}:{client_ip}"
                current, ttl = await redis.eval(
                    _FIXED_WINDOW,
                    1,
                    key,
                    window,
                )
                if int(current) > maximum:
                    retry_after = max(int(ttl), 1)
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Too many requests"},
                        headers={"Retry-After": str(retry_after)},
                    )
        except RedisError:
            # Redis is checked during startup. A transient failure must not turn
            # every API response into 500; log it so monitoring can alert.
            logger.exception("Rate limiter unavailable")

        return await call_next(request)
