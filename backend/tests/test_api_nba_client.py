from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import httpx
import pytest

from app.services.clients.api_nba import (
    ApiNbaAuthenticationError,
    ApiNbaClient,
    ApiNbaConfigurationError,
    ApiNbaError,
    ApiNbaQuotaError,
    RequestLimiter,
)


async def no_sleep(_delay: float) -> None:
    return None


@asynccontextmanager
async def api_nba_client_for(
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    limiter: RequestLimiter | None = None,
    retry_sleep: Callable[[float], Awaitable[None]] = no_sleep,
    rate_limit_retry_seconds: float = 60.0,
) -> AsyncIterator[ApiNbaClient]:
    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        yield ApiNbaClient(
            api_key="secret",
            base_url="https://example.test",
            http_client=http_client,
            limiter=limiter or RequestLimiter(0),
            retry_sleep=retry_sleep,
            rate_limit_retry_seconds=rate_limit_retry_seconds,
        )


def test_client_rejects_missing_api_key() -> None:
    with pytest.raises(ApiNbaConfigurationError, match="key is required"):
        ApiNbaClient(api_key="  ", base_url="https://example.test")


@pytest.mark.asyncio
async def test_players_request_uses_key_team_and_season() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-apisports-key"] == "secret"
        assert request.url.path == "/players"
        assert dict(request.url.params) == {"team": "10", "season": "2025"}
        return httpx.Response(200, json={"errors": [], "response": []})

    async with api_nba_client_for(handler) as client:
        assert await client.get_players(team_id=10, season=2025) == []


@pytest.mark.asyncio
async def test_requests_are_spaced_for_free_plan() -> None:
    current_time = 0.0
    request_times: list[float] = []

    def clock() -> float:
        return current_time

    async def sleep(delay: float) -> None:
        nonlocal current_time
        current_time += delay

    def handler(_request: httpx.Request) -> httpx.Response:
        request_times.append(clock())
        return httpx.Response(200, json={"errors": [], "response": []})

    limiter = RequestLimiter(6.2, clock=clock, sleep=sleep)
    async with api_nba_client_for(handler, limiter=limiter) as client:
        await client.get_teams()
        await client.get_teams()
        await client.get_teams()

    assert request_times == [0.0, 6.2, 12.4]


@pytest.mark.asyncio
async def test_statistics_request_uses_expected_endpoint() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/players/statistics"
        assert dict(request.url.params) == {"team": "20", "season": "2025"}
        return httpx.Response(200, json={"errors": {}, "response": [{"game": {"id": 1}}]})

    async with api_nba_client_for(handler) as client:
        assert await client.get_player_statistics(team_id=20, season=2025) == [
            {"game": {"id": 1}}
        ]


@pytest.mark.asyncio
async def test_http_200_provider_quota_error_is_rejected() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"errors": {"requests": "Daily limit reached"}, "response": []},
        )

    async with api_nba_client_for(handler) as client:
        with pytest.raises(ApiNbaQuotaError, match="Daily limit"):
            await client.get_teams()


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [401, 403])
async def test_authentication_errors_do_not_expose_key(status: int) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"message": "bad key"})

    async with api_nba_client_for(handler) as client:
        with pytest.raises(ApiNbaAuthenticationError) as caught:
            await client.get_teams()

    assert "secret" not in str(caught.value)


@pytest.mark.asyncio
async def test_http_429_is_retried_once() -> None:
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "0"},
                json={"message": "slow down"},
            )
        return httpx.Response(
            200,
            json={"errors": [], "response": [{"id": 1}]},
        )

    async with api_nba_client_for(handler) as client:
        assert await client.get_teams() == [{"id": 1}]

    assert attempts == 2


@pytest.mark.asyncio
async def test_http_200_rate_limit_error_is_retried_once() -> None:
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(
                200,
                headers={"Retry-After": "0"},
                json={
                    "errors": {
                        "rateLimit": "Too many requests. "
                        "Your rate limit is 10 requests per minute."
                    },
                    "response": [],
                },
            )
        return httpx.Response(
            200,
            json={"errors": [], "response": [{"id": 1}]},
        )

    async with api_nba_client_for(handler) as client:
        assert await client.get_teams() == [{"id": 1}]

    assert attempts == 2


@pytest.mark.asyncio
async def test_rate_limit_without_retry_after_waits_for_minute_window() -> None:
    attempts = 0
    retry_delays: list[float] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(
                200,
                json={
                    "errors": {
                        "rateLimit": "Too many requests. "
                        "Your rate limit is 10 requests per minute."
                    },
                    "response": [],
                },
            )
        return httpx.Response(
            200,
            json={"errors": [], "response": [{"id": 1}]},
        )

    async def retry_sleep(delay: float) -> None:
        retry_delays.append(delay)

    async with api_nba_client_for(
        handler,
        retry_sleep=retry_sleep,
        rate_limit_retry_seconds=60.0,
    ) as client:
        assert await client.get_teams() == [{"id": 1}]

    assert retry_delays == [60.0]


@pytest.mark.asyncio
async def test_repeated_http_429_maps_to_quota_error() -> None:
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            429,
            headers={"Retry-After": "0"},
            json={"message": "slow down"},
        )

    async with api_nba_client_for(handler) as client:
        with pytest.raises(ApiNbaQuotaError, match="quota"):
            await client.get_teams()

    assert attempts == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        {"errors": [], "response": {}},
        {"errors": [], "response": [None]},
    ],
)
async def test_malformed_envelope_is_rejected(payload: object) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with api_nba_client_for(handler) as client:
        with pytest.raises(ApiNbaError, match="response"):
            await client.get_teams()


@pytest.mark.asyncio
async def test_invalid_json_is_rejected() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not-json")

    async with api_nba_client_for(handler) as client:
        with pytest.raises(ApiNbaError, match="expected JSON"):
            await client.get_teams()


@pytest.mark.asyncio
async def test_transport_error_does_not_expose_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("failed secret", request=request)

    async with api_nba_client_for(handler) as client:
        with pytest.raises(ApiNbaError) as caught:
            await client.get_teams()

    assert "secret" not in str(caught.value)
