"""Expose request duration for browser and release performance checks."""
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware


class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        started = perf_counter()
        response = await call_next(request)
        response.headers['Server-Timing'] = f'app;dur={(perf_counter() - started) * 1000:.2f}'
        return response
