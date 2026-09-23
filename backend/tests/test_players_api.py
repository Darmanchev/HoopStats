from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.models.player import Player
from app.models.team import Team
from app.routers import players


class FakeResult:
    def __init__(self, player: Player | None) -> None:
        self.player = player

    def scalar_one_or_none(self) -> Player | None:
        return self.player


class FakeSession:
    def __init__(self, player: Player | None) -> None:
        self.player = player

    async def execute(self, _statement: object) -> FakeResult:
        return FakeResult(self.player)


@pytest.mark.asyncio
async def test_player_detail_exposes_provider_id_without_official_id() -> None:
    player = Player(
        id=1,
        nba_id=None,
        balldontlie_id=115,
        name="Stephen Curry",
        team_abbr="GSW",
        position="G",
        jersey_number="30",
        games_played=0,
        pts=0.0,
        reb=0.0,
        ast=0.0,
        stl=0.0,
        blk=0.0,
        fg_pct=0.0,
        fg3_pct=0.0,
        ft_pct=0.0,
        mins=0.0,
        recent_games=0,
    )
    player.team = Team(
        abbr="GSW",
        nba_id=1610612744,
        balldontlie_id=10,
        name="Warriors",
        city="Golden State",
        record="0-0",
    )
    app = FastAPI()
    app.include_router(players.router)

    async def override_get_db() -> AsyncIterator[FakeSession]:
        yield FakeSession(player)

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/players/1")

    assert response.status_code == 200
    assert response.json()["nbaId"] is None
    assert response.json()["balldontlieId"] == 115
