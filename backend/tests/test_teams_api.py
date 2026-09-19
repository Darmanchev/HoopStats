from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.models.team import Team
from app.routers import teams


class FakeResult:
    def __init__(self, value: object) -> None:
        self.value = value

    def scalar_one_or_none(self):
        return self.value

    def scalar_one(self):
        return self.value


class FakeSession:
    def __init__(self, results: list[object]) -> None:
        self.results = iter(results)

    async def execute(self, _statement: object) -> FakeResult:
        return FakeResult(next(self.results))


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
