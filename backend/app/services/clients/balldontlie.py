"""Async client for BALLDONTLIE free-tier NBA endpoints."""

import asyncio
import time
from collections.abc import Awaitable, Callable, Sequence
from typing import Any

import httpx

from ...config import settings


class BallDontLieError(RuntimeError):
    """Base error for safe-to-log BALLDONTLIE client failures."""


class BallDontLieConfigurationError(BallDontLieError):
    """Raised when required provider configuration is missing."""


class BallDontLieAuthenticationError(BallDontLieError):
    """Raised when the provider rejects the configured API key."""


class BallDontLieRateLimitError(BallDontLieError):
    """Raised when a request remains rate-limited after one retry."""


class RequestLimiter:
    """Space request starts so one process respects the provider limit."""

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


shared_limiter = RequestLimiter(
    settings.balldontlie_request_interval_seconds,
)


class BallDontLieClient:
    """Authenticated BALLDONTLIE transport with injectable test seams."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        http_client: httpx.AsyncClient | None = None,
        limiter: RequestLimiter | None = None,
    ) -> None:
        if not api_key.strip():
            raise BallDontLieConfigurationError(
                "BALLDONTLIE API key is required"
            )
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._owns_http_client = http_client is None
        self._http = http_client or httpx.AsyncClient(timeout=30.0)
        self._limiter = limiter or shared_limiter

    async def __aenter__(self) -> "BallDontLieClient":
        return self

    async def __aexit__(self, *_args: object) -> None:
        if self._owns_http_client:
            await self._http.aclose()

    async def _get_paginated(
        self,
        path: str,
        params: list[tuple[str, str]] | None = None,
    ) -> list[dict[str, Any]]:
        base_params = list(params or [])
        base_params.append(("per_page", "100"))
        records: list[dict[str, Any]] = []
        seen_cursors: set[str] = set()
        cursor: str | None = None

        while True:
            page_params = list(base_params)
            if cursor is not None:
                page_params.append(("cursor", cursor))
            response = await self._request(path, page_params)
            data, next_cursor = self._parse_page(response)
            records.extend(data)
            if next_cursor is None:
                return records
            cursor = str(next_cursor)
            if cursor in seen_cursors:
                raise BallDontLieError(
                    "Invalid BALLDONTLIE response: repeated pagination cursor"
                )
            seen_cursors.add(cursor)

    async def _request(
        self,
        path: str,
        params: list[tuple[str, str]],
    ) -> httpx.Response:
        for attempt in range(2):
            await self._limiter.wait()
            try:
                response = await self._http.get(
                    f"{self._base_url}{path}",
                    params=params,
                    headers={"Authorization": self._api_key},
                )
            except httpx.HTTPError as exc:
                raise BallDontLieError(
                    f"BALLDONTLIE request failed: {type(exc).__name__}"
                ) from exc

            if response.status_code == 401:
                raise BallDontLieAuthenticationError(
                    "BALLDONTLIE rejected the configured API key"
                )
            if response.status_code == 429:
                if attempt == 1:
                    raise BallDontLieRateLimitError(
                        "BALLDONTLIE rate limit remained active after retry"
                    )
                await asyncio.sleep(self._retry_after(response))
                continue
            if response.is_error:
                raise BallDontLieError(
                    "BALLDONTLIE request failed with HTTP status "
                    f"{response.status_code}"
                )
            return response

        raise BallDontLieRateLimitError(
            "BALLDONTLIE rate limit remained active after retry"
        )

    @staticmethod
    def _retry_after(response: httpx.Response) -> float:
        try:
            delay = float(response.headers.get("Retry-After", "0"))
        except ValueError:
            return 0.0
        return min(60.0, max(0.0, delay))

    @staticmethod
    def _parse_page(
        response: httpx.Response,
    ) -> tuple[list[dict[str, Any]], object | None]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise BallDontLieError(
                "Invalid BALLDONTLIE response: expected JSON"
            ) from exc
        if not isinstance(payload, dict):
            raise BallDontLieError(
                "Invalid BALLDONTLIE response: expected an object"
            )
        data = payload.get("data")
        meta = payload.get("meta", {})
        if not isinstance(data, list) or not isinstance(meta, dict):
            raise BallDontLieError(
                "Invalid BALLDONTLIE response: malformed list envelope"
            )
        return data, meta.get("next_cursor")

    async def get_teams(self) -> list[dict[str, Any]]:
        return await self._get_paginated("/teams")

    async def get_players(self) -> list[dict[str, Any]]:
        return await self._get_paginated("/players")

    async def get_games(
        self,
        *,
        dates: Sequence[str] = (),
        seasons: Sequence[int] = (),
        season_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        params = [("dates[]", value) for value in dates]
        params += [("seasons[]", str(value)) for value in seasons]
        if season_type is not None:
            params.append(("season_type", season_type))
        if start_date is not None:
            params.append(("start_date", start_date))
        if end_date is not None:
            params.append(("end_date", end_date))
        return await self._get_paginated("/games", params)


def create_client() -> BallDontLieClient:
    """Build a production client from application settings."""
    return BallDontLieClient(
        api_key=settings.balldontlie_api_key,
        base_url=settings.balldontlie_base_url,
        limiter=shared_limiter,
    )
