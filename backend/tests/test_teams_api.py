import json
from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from redis.exceptions import RedisError

from app.database import get_db
from app.models.team import Team
from app.models.team_stats import TeamStats
from app.routers import teams


class FakeResult:
    def __init__(self, value: object) -> None:
        self.value = value

    def scalar_one_or_none(self):
        return self.value

    def scalar_one(self):
        return self.value

    def scalars(self):
        return self

    def all(self):
        return self.value


class FakeSession:
    def __init__(self, results: list[object]) -> None:
        self.results = iter(results)

    async def execute(self, _statement: object) -> FakeResult:
        return FakeResult(next(self.results))


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.set_calls: list[tuple[str, str, int | None]] = []

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.values[key] = value
        self.set_calls.append((key, value, ex))


class FailingRedis(FakeRedis):
    async def get(self, key: str) -> str | None:
        raise RedisError(f"cannot read {key}")

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        raise RedisError(f"cannot write {key}")


def make_app(team: Team, players_count: int) -> FastAPI:
    app = FastAPI()
    app.include_router(teams.router)

    async def override_get_db() -> AsyncIterator[FakeSession]:
        yield FakeSession([team, players_count])

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.mark.asyncio
async def test_team_detail_uses_database_player_count() -> None:
    team = Team(
        abbr="BOS",
        nba_id=1610612738,
        name="Celtics",
        city="Boston",
        record="4-1",
        conference="East",
        conference_rank=1,
        last_ten="4-1",
        streak="W2",
    )
    app = make_app(team, players_count=17)
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/teams/BOS")

    assert response.status_code == 200
    assert response.json()["playersCount"] == 17


@pytest.mark.asyncio
async def test_team_list_includes_stats_and_caches_combined_response() -> None:
    team = Team(
        abbr="BOS",
        nba_id=1610612738,
        name="Celtics",
        city="Boston",
        record="4-1",
        conference="East",
        conference_rank=1,
        last_ten="4-1",
        streak="W2",
    )
    team.stats = TeamStats(
        team_abbr="BOS",
        form=["W", "W", "L"],
        last_scores=[118, 110, 102],
    )
    redis = FakeRedis()
    app = FastAPI()
    app.state.redis = redis
    app.include_router(teams.router)

    async def override_get_db() -> AsyncIterator[FakeSession]:
        yield FakeSession([[team]])

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/teams/")

    assert response.status_code == 200
    assert response.json() == [
        {
            "abbr": "BOS",
            "name": "Celtics",
            "city": "Boston",
            "record": "4-1",
            "conference": "East",
            "conferenceRank": 1,
            "lastTen": "4-1",
            "streak": "W2",
            "stats": {
                "teamAbbr": "BOS",
                "form": ["W", "W", "L"],
                "lastScores": [118, 110, 102],
            },
        }
    ]
    assert len(redis.set_calls) == 1
    key, cached_payload, ttl = redis.set_calls[0]
    assert key == "api:teams:v1"
    assert json.loads(cached_payload) == response.json()
    assert ttl == 300


@pytest.mark.asyncio
async def test_team_list_uses_cached_response_without_querying_database() -> None:
    cached_teams = [
        {
            "abbr": "BOS",
            "name": "Celtics",
            "city": "Boston",
            "record": "4-1",
            "conference": "East",
            "conferenceRank": 1,
            "lastTen": "4-1",
            "streak": "W2",
            "stats": {
                "teamAbbr": "BOS",
                "form": ["W"],
                "lastScores": [118],
            },
        }
    ]
    redis = FakeRedis()
    redis.values["api:teams:v1"] = json.dumps(cached_teams)
    app = FastAPI()
    app.state.redis = redis
    app.include_router(teams.router)

    class UnexpectedDatabaseSession:
        async def execute(self, _statement: object) -> FakeResult:
            raise AssertionError("database must not be queried on a cache hit")

    async def override_get_db() -> AsyncIterator[UnexpectedDatabaseSession]:
        yield UnexpectedDatabaseSession()

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/teams/")

    assert response.status_code == 200
    assert response.json() == cached_teams
    assert redis.set_calls == []


@pytest.mark.asyncio
async def test_team_list_falls_back_to_database_when_redis_fails() -> None:
    team = Team(
        abbr="BOS",
        nba_id=1610612738,
        name="Celtics",
        city="Boston",
        record="4-1",
        conference="East",
        conference_rank=1,
        last_ten="4-1",
        streak="W2",
    )
    team.stats = None
    app = FastAPI()
    app.state.redis = FailingRedis()
    app.include_router(teams.router)

    async def override_get_db() -> AsyncIterator[FakeSession]:
        yield FakeSession([[team]])

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/teams/")

    assert response.status_code == 200
    assert response.json()[0]["conference"] == "East"
