from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

import httpx
import pytest

from app.services.clients.api_nba import (
    ApiNbaAuthenticationError,
    ApiNbaClient,
    ApiNbaConfigurationError,
    ApiNbaError,
    ApiNbaQuotaError,
)


@asynccontextmanager
async def api_nba_client_for(
    handler: Callable[[httpx.Request], httpx.Response],
) -> AsyncIterator[ApiNbaClient]:
    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        yield ApiNbaClient(
            api_key="secret",
            base_url="https://example.test",
            http_client=http_client,
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
async def test_http_429_maps_to_quota_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"message": "slow down"})

    async with api_nba_client_for(handler) as client:
        with pytest.raises(ApiNbaQuotaError, match="quota"):
            await client.get_teams()


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
