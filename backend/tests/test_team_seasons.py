import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.models.game import Game
from app.models.team import Team
from app.routers.teams import router
from app.services.team_seasons import list_team_seasons, season_teams


async def seed_games(db):
    db.add_all([
        Team(abbr="BOS", name="Celtics", city="Boston", record="99-0", conference="East"),
        Team(abbr="LAL", name="Lakers", city="Los Angeles", record="99-0", conference="West"),
    ])
    await db.flush()
    def game(id, season, date, score1, score2, **kwargs):
        return Game(id=id, season=season, date=date, team1="BOS", team2="LAL",
                    score1=score1, score2=score2, time="", venue="",
                    status=kwargs.get("status", "final"), season_type=kwargs.get("season_type", "regular"))
    db.add_all([
        game("a", "2024-25", "2025-01-01", 100, 90),
        game("b", "2024-25", "2025-01-02", 90, 110),
        game("c", "2024-25", "2025-01-03", 120, 110),
        game("playoff", "2024-25", "2025-05-01", 10, 100, season_type="playoffs"),
        game("preseason", "2024-25", "2024-10-03", 129, 105, season_type="preseason"),
        game("new-preseason", "2026-27", "2026-10-03", 129, 105, season_type="preseason"),
        game("live", "2024-25", "2025-01-04", 10, 100, status="live"),
        game("missing", "2024-25", "2025-01-04", None, None),
        game("other", "2023-24", "2024-01-01", 90, 100),
        game("future", "2026-27", "2026-10-01", None, None, status="scheduled"),
    ])
    await db.commit()


@pytest.mark.asyncio
async def test_season_records_and_form_ignore_other_seasons_and_playoffs(db_session):
    await seed_games(db_session)
    assert await list_team_seasons(db_session) == ["2024-25", "2023-24"]
    teams = {team.abbr: team for team in await season_teams(db_session, "2024-25")}
    assert teams["BOS"].record == "2-1"
    assert teams["LAL"].record == "1-2"
    assert teams["BOS"].stats.form == ["W", "L", "W"]
    assert teams["BOS"].stats.last_scores == [120, 90, 100]
    assert teams["LAL"].stats.last_scores == [110, 110, 90]
    assert teams["BOS"].streak == "W1"
    assert teams["BOS"].last_ten == "2-1"
    old = {team.abbr: team for team in await season_teams(db_session, "2023-24")}
    assert old["BOS"].record == "0-1"


@pytest.mark.asyncio
async def test_team_season_routes_and_validation(db_session):
    await seed_games(db_session)
    app = FastAPI()
    app.include_router(router)
    async def database():
        yield db_session
    app.dependency_overrides[get_db] = database
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/teams/seasons")).json() == ["2024-25", "2023-24"]
        result = await client.get("/teams/?season=2024-25")
        assert result.status_code == 200
        assert result.json()[0]["record"] == "2-1"
        stats = await client.get("/teams/BOS/stats?season=2023-24")
        assert stats.json()["form"] == ["L"]
        detail = await client.get("/teams/BOS?season=2023-24")
        assert detail.status_code == 200
        assert detail.json()["record"] == "0-1"
        assert (await client.get("/teams/?season=2024-27")).status_code == 422
        assert (await client.get("/teams/?season=2022-23")).status_code == 404
        assert (await client.get("/teams/XXX/stats?season=2024-25")).status_code == 404
