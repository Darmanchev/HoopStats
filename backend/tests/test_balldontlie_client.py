from collections.abc import Callable
from contextlib import asynccontextmanager

import httpx
import pytest

from app.services.clients.balldontlie import (
    BallDontLieClient,
    BallDontLieAuthenticationError,
    BallDontLieConfigurationError,
    BallDontLieError,
    BallDontLieRateLimitError,
    RequestLimiter,
)


@asynccontextmanager
async def client_for(
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    limiter: RequestLimiter | None = None,
):
    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        yield BallDontLieClient(
            api_key="secret-key",
            base_url="https://example.test/v1",
            http_client=http_client,
            limiter=limiter or RequestLimiter(0),
        )


def test_client_rejects_missing_api_key() -> None:
    with pytest.raises(BallDontLieConfigurationError, match="API key"):
        BallDontLieClient(api_key="", base_url="https://example.test/v1")


@pytest.mark.asyncio
async def test_teams_request_uses_authorization_header() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "secret-key"
        return httpx.Response(200, json={"data": []})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = BallDontLieClient(
            api_key="secret-key",
            base_url="https://example.test/v1",
            http_client=http_client,
            limiter=RequestLimiter(0),
        )
        assert await client.get_teams() == []


@pytest.mark.asyncio
async def test_games_serializes_array_filters_and_follows_cursor() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(
                200,
                json={"data": [{"id": 1}], "meta": {"next_cursor": 99}},
            )
        return httpx.Response(
            200,
            json={"data": [{"id": 2}], "meta": {}},
        )

    async with client_for(handler) as client:
        result = await client.get_games(
            dates=["2026-09-23"],
            seasons=[2025],
        )

    assert result == [{"id": 1}, {"id": 2}]
    assert requests[0].url.params.get_list("dates[]") == ["2026-09-23"]
    assert requests[0].url.params.get_list("seasons[]") == ["2025"]
    assert requests[1].url.params["cursor"] == "99"


@pytest.mark.asyncio
async def test_repeated_cursor_is_rejected() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"data": [{"id": 1}], "meta": {"next_cursor": 99}},
        )

    async with client_for(handler) as client:
        with pytest.raises(BallDontLieError, match="cursor"):
            await client.get_players()


@pytest.mark.asyncio
async def test_request_limiter_spaces_request_starts() -> None:
    current_time = 0.0
    request_times: list[float] = []

    def clock() -> float:
        return current_time

    async def sleep(delay: float) -> None:
        nonlocal current_time
        current_time += delay

    def handler(_request: httpx.Request) -> httpx.Response:
        request_times.append(clock())
        return httpx.Response(200, json={"data": []})

    limiter = RequestLimiter(12.0, clock=clock, sleep=sleep)
    async with client_for(handler, limiter=limiter) as client:
        await client.get_teams()
        await client.get_teams()
        await client.get_teams()

    assert request_times == [0.0, 12.0, 24.0]


@pytest.mark.asyncio
async def test_rate_limit_response_is_retried_once() -> None:
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "0"},
                json={"error": "rate limited"},
            )
        return httpx.Response(200, json={"data": [{"id": 1}]})

    async with client_for(handler) as client:
        assert await client.get_teams() == [{"id": 1}]

    assert attempts == 2


@pytest.mark.asyncio
async def test_second_rate_limit_response_raises_provider_error() -> None:
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(429, json={"error": "rate limited"})

    async with client_for(handler) as client:
        with pytest.raises(BallDontLieRateLimitError, match="rate limit"):
            await client.get_teams()

    assert attempts == 2


@pytest.mark.asyncio
async def test_unauthorized_response_raises_authentication_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid_api_key"})

    async with client_for(handler) as client:
        with pytest.raises(BallDontLieAuthenticationError, match="rejected"):
            await client.get_teams()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"data": {}},
        {"data": [], "meta": []},
    ],
)
async def test_malformed_list_envelope_is_rejected(payload: object) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with client_for(handler) as client:
        with pytest.raises(BallDontLieError, match="response"):
            await client.get_teams()
