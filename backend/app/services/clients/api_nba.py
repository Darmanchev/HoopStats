import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from app.config import settings


class ApiNbaError(RuntimeError):
    """Base error safe to expose in synchronization logs."""


class ApiNbaConfigurationError(ApiNbaError):
    """Required API-NBA configuration is missing."""


class ApiNbaAuthenticationError(ApiNbaError):
    """API-NBA rejected the configured key."""


class ApiNbaQuotaError(ApiNbaError):
    """API-NBA rejected a request because its quota was exhausted."""


class RequestLimiter:
    """Space request starts so one process respects API-NBA's free tier."""

    def __init__(
        self,
        interval_seconds: float,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.interval_seconds = max(0.0, interval_seconds)
        self._clock = clock
        self._sleep = sleep
        self._last_request_at: float | None = None
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        async with self._lock:
            now = self._clock()
            if self._last_request_at is not None:
                delay = self.interval_seconds - (now - self._last_request_at)
                if delay > 0:
                    await self._sleep(delay)
            self._last_request_at = self._clock()


shared_limiter = RequestLimiter(settings.api_nba_request_interval_seconds)


class ApiNbaClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        http_client: httpx.AsyncClient | None = None,
        limiter: RequestLimiter | None = None,
        retry_sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        rate_limit_retry_seconds: float = 60.0,
    ) -> None:
        if not api_key.strip():
            raise ApiNbaConfigurationError("API-NBA key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._owns_http_client = http_client is None
        self._http = http_client or httpx.AsyncClient(timeout=60.0)
        self._limiter = limiter or shared_limiter
        self._retry_sleep = retry_sleep
        self._rate_limit_retry_seconds = max(0.0, rate_limit_retry_seconds)

    async def __aenter__(self) -> "ApiNbaClient":
        return self

    async def __aexit__(self, *_args: object) -> None:
        if self._owns_http_client:
            await self._http.aclose()

    async def _get(
        self,
        path: str,
        params: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        for attempt in range(2):
            await self._limiter.wait()
            try:
                response = await self._http.get(
                    f"{self._base_url}{path}",
                    params=params,
                    headers={"x-apisports-key": self._api_key},
                )
            except httpx.HTTPError as exc:
                raise ApiNbaError(
                    f"API-NBA request failed: {type(exc).__name__}"
                ) from exc

            if response.status_code in {401, 403}:
                raise ApiNbaAuthenticationError(
                    "API-NBA rejected the configured key"
                )
            if response.status_code == 429:
                if attempt == 0:
                    await self._retry_sleep(self._retry_after(response))
                    continue
                raise ApiNbaQuotaError("API-NBA request quota is exhausted")
            if response.is_error:
                raise ApiNbaError(
                    "API-NBA request failed with HTTP status "
                    f"{response.status_code}"
                )

            try:
                payload = response.json()
            except ValueError as exc:
                raise ApiNbaError(
                    "Invalid API-NBA response: expected JSON"
                ) from exc
            if not isinstance(payload, dict):
                raise ApiNbaError("Invalid API-NBA response object")

            errors = payload.get("errors")
            if errors:
                message = str(errors)
                if self._is_rate_limit_error(message) and attempt == 0:
                    await self._retry_sleep(self._retry_after(response))
                    continue
                if any(
                    word in message.lower()
                    for word in ("limit", "quota", "request")
                ):
                    raise ApiNbaQuotaError(f"API-NBA quota error: {message}")
                raise ApiNbaError(f"API-NBA provider error: {message}")

            records = payload.get("response")
            if not isinstance(records, list) or not all(
                isinstance(record, dict) for record in records
            ):
                raise ApiNbaError("Invalid API-NBA response envelope")
            return records

        raise ApiNbaQuotaError("API-NBA request quota is exhausted")

    @staticmethod
    def _is_rate_limit_error(message: str) -> bool:
        normalized = message.lower()
        return any(
            marker in normalized
            for marker in ("ratelimit", "rate limit", "too many requests", "per minute")
        )

    def _retry_after(self, response: httpx.Response) -> float:
        value = response.headers.get("Retry-After")
        if value is None:
            return self._rate_limit_retry_seconds
        try:
            return max(0.0, float(value))
        except ValueError:
            return self._rate_limit_retry_seconds

    async def get_teams(self) -> list[dict[str, Any]]:
        return await self._get("/teams")

    async def get_players(self, *, team_id: int, season: int) -> list[dict[str, Any]]:
        return await self._get(
            "/players",
            {"team": str(team_id), "season": str(season)},
        )

    async def get_player_statistics(
        self,
        *,
        team_id: int,
        season: int,
    ) -> list[dict[str, Any]]:
        return await self._get(
            "/players/statistics",
            {"team": str(team_id), "season": str(season)},
        )


def create_client() -> ApiNbaClient:
    return ApiNbaClient(
        api_key=settings.api_nba_key,
        base_url=settings.api_nba_base_url,
        limiter=shared_limiter,
        rate_limit_retry_seconds=settings.api_nba_rate_limit_retry_seconds,
    )
