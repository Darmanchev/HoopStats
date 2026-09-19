from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.models.game import Game
from app.models.team import Team
from app.routers import games


class FakeResult:
    def __init__(self, game: Game | None) -> None:
        self.game = game

    def scalar_one_or_none(self) -> Game | None:
        return self.game


class FakeSession:
    def __init__(self, game: Game | None) -> None:
        self.game = game

    async def execute(self, _statement: object) -> FakeResult:
        return FakeResult(self.game)


def make_game(
    *,
    win1: float | None = 61.2,
    prediction: str | None = "Boston has the stronger recent form.",
) -> Game:
    game = Game(
        id="0022600001",
        team1="BOS",
        team2="LAL",
        date="2026-10-20",
        time="7:30 PM ET",
        venue="TD Garden",
        is_today=False,
        season_type="regular",
        season="2026-27",
        win1=win1,
        prediction=prediction,
        score1=None,
        score2=None,
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


def make_app(game: Game | None) -> FastAPI:
    app = FastAPI()
    app.include_router(games.router)

    async def override_get_db() -> AsyncIterator[FakeSession]:
        yield FakeSession(game)

    app.dependency_overrides[get_db] = override_get_db
    return app


async def request_game(
    game: Game | None,
    game_id: str = "0022600001",
):
    app = make_app(game)
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        return await client.get(f"/games/{game_id}")


@pytest.mark.asyncio
async def test_match_detail_returns_prediction_and_team_details() -> None:
    response = await request_game(make_game())

    assert response.status_code == 200
    assert response.json() == {
        "id": "0022600001",
        "team1": "BOS",
        "team2": "LAL",
        "date": "2026-10-20",
        "time": "7:30 PM ET",
        "venue": "TD Garden",
        "seasonType": "regular",
        "season": "2026-27",
        "isToday": False,
        "win1": 61.2,
        "prediction": "Boston has the stronger recent form.",
        "homeTeam": {
            "abbr": "BOS",
            "name": "Celtics",
            "city": "Boston",
            "record": "4-1",
        },
        "awayTeam": {
            "abbr": "LAL",
            "name": "Lakers",
            "city": "Los Angeles",
            "record": "3-2",
        },
    }


@pytest.mark.asyncio
async def test_match_detail_preserves_null_prediction_fields() -> None:
    response = await request_game(make_game(win1=None, prediction=None))

    assert response.status_code == 200
    assert response.json()["win1"] is None
    assert response.json()["prediction"] is None


@pytest.mark.asyncio
async def test_match_detail_returns_404_when_game_does_not_exist() -> None:
    response = await request_game(None, "missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "Game not found"}
