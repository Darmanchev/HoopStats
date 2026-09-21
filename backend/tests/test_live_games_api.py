from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from redis.exceptions import RedisError

from app.database import get_db
from app.models.game import Game
from app.models.team import Team
from app.routers import games


class FakeResult:
    def __init__(self, value: object) -> None:
        self.value = value

    def scalar_one_or_none(self) -> object:
        return self.value

    def scalars(self) -> "FakeResult":
        return self

    def all(self) -> object:
        return self.value


class FakeSession:
    def __init__(self, results: list[object]) -> None:
        self.results = iter(results)

    async def execute(self, _statement: object) -> FakeResult:
        return FakeResult(next(self.results))


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def set(self, key: str, value: str, ex: int) -> None:
        self.values[key] = value


class FailingRedis(FakeRedis):
    async def get(self, key: str) -> str | None:
        raise RedisError(f"cannot read {key}")

    async def set(self, key: str, value: str, ex: int) -> None:
        raise RedisError(f"cannot write {key}")


def make_live_game() -> Game:
    game = Game(
        id="0022500002",
        team1="BOS",
        team2="LAL",
        date="2026-09-21",
        time="Q3 04:12",
        venue="Crypto.com Arena",
        is_today=True,
        season_type="regular",
        season="2026-27",
        status="live",
        status_text="Q3 04:12",
        period=3,
        clock="PT04M12.00S",
        score1=78,
        score2=74,
    )
    game.home_team = Team(
        abbr="BOS",
        nba_id=1610612738,
        name="Celtics",
        city="Boston",
        record="4-1",
    )
    game.away_team = Team(
        abbr="LAL",
        nba_id=1610612747,
        name="Lakers",
        city="Los Angeles",
        record="3-2",
    )
    return game


def make_app(results: list[object], redis: FakeRedis | None = None) -> FastAPI:
    app = FastAPI()
    app.state.redis = redis or FakeRedis()
    app.include_router(games.router)

    async def override_get_db() -> AsyncIterator[FakeSession]:
        yield FakeSession(results)

    app.dependency_overrides[get_db] = override_get_db
    return app


async def get(app: FastAPI, path: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


@pytest.mark.asyncio
async def test_today_returns_live_state() -> None:
    response = await get(make_app([[make_live_game()]]), "/games/today")

    assert response.status_code == 200
    game = response.json()[0]
    assert {
        "status": game["status"],
        "statusText": game["statusText"],
        "period": game["period"],
        "clock": game["clock"],
        "score1": game["score1"],
        "score2": game["score2"],
    } == {
        "status": "live",
        "statusText": "Q3 04:12",
        "period": 3,
        "clock": "PT04M12.00S",
        "score1": 78,
        "score2": 74,
    }


@pytest.mark.asyncio
async def test_boxscore_returns_empty_list_when_no_rows_exist() -> None:
    response = await get(
        make_app([make_live_game(), []]),
        "/games/0022500002/boxscore",
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_boxscore_returns_404_when_game_does_not_exist() -> None:
    response = await get(make_app([None]), "/games/missing/boxscore")

    assert response.status_code == 404
    assert response.json() == {"detail": "Game not found"}


@pytest.mark.asyncio
async def test_today_falls_back_to_database_when_redis_fails() -> None:
    response = await get(
        make_app([[make_live_game()]], FailingRedis()),
        "/games/today",
    )

    assert response.status_code == 200
    assert response.json()[0]["status"] == "live"
