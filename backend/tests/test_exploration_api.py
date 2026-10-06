from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.database import get_db, Base
from app.models import Game, Team, Player, PlayerGameStat
from app.routers import games, analytics, players


def game(id, date="2025-01-01", **kw):
    return Game(id=id, team1="BOS", team2="LAL", date=date, time="", venue="", season="2024-25", season_type="regular", status="final", home_abbr="LAL", score1=100, score2=90, **kw)


async def client_for(db, *routers):
    app = FastAPI()
    for router in routers:
        app.include_router(router)
    app.state.redis = AsyncMock()
    app.state.redis.get.return_value = None
    app.state.redis.set.return_value = True
    async def override():
        yield db
    app.dependency_overrides[get_db] = override
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_schedule_filters_before_pagination_and_exposes_months(db_session):
    db_session.add_all([Team(abbr="BOS", name="Celtics", city="Boston", record="0-0"), Team(abbr="LAL", name="Lakers", city="Los Angeles", record="0-0")])
    await db_session.flush()
    db_session.add_all([game("a"), game("b"), game("c", "2025-02-01")])
    await db_session.commit()
    async with await client_for(db_session, games.router) as client:
        response = await client.get("/games/?date_from=2025-01-01&date_to=2025-01-31&team=BOS&limit=1&skip=1")
        assert response.status_code == 200
        assert response.json()["total"] == 2
        assert response.json()["items"][0]["id"] == "b"
        assert (await client.get("/games/months?season=2024-25")).json() == ["2025-01", "2025-02"]
        assert (await client.get("/games/?team=NYK")).json()["total"] == 0
        assert (await client.get("/games/?season=2025-27")).status_code == 422
        detail = (await client.get("/games/a")).json()
        assert detail["awayTeam"]["abbr"] == "BOS"
        assert detail["homeTeam"]["abbr"] == "LAL"


@pytest.mark.asyncio
async def test_historical_elo_excludes_preseason_future_and_missing_seasons(db_session):
    db_session.add_all([game("old"), game("future", "2026-01-01")])
    future = await db_session.get(Game, "future")
    # pending inserts get flushed by get
    future.season = "2025-26"
    preseason = game("pre")
    preseason.season_type = "preseason"
    preseason.score1, preseason.score2 = 1, 150
    db_session.add(preseason)
    await db_session.commit()
    async with await client_for(db_session, analytics.router) as client:
        historical = (await client.get("/analytics/elo?season=2024-25")).json()
        assert historical[0]["teamAbbr"] == "BOS"
        assert (await client.get("/analytics/elo?season=2023-24")).json() == []


@pytest.mark.asyncio
async def test_player_favorites_filter_before_paging(db_session):
    for i in range(3):
        db_session.add(Player(name=f"Player {i}", team_abbr="BOS", position="G"))
    await db_session.commit()
    rows = (await db_session.execute(select(Player).order_by(Player.id))).scalars().all()
    async with await client_for(db_session, players.router) as client:
        response = await client.get(f"/players/?ids={rows[-1].id}&limit=1")
        assert [row["id"] for row in response.json()] == [rows[-1].id]


@pytest.mark.asyncio
async def test_search_is_grouped_and_escapes_wildcards(db_session):
    from app.routers import search
    db_session.add_all([Team(abbr="BOS", name="Celtics", city="Boston", record="0-0"), Team(abbr="LAL", name="Lakers", city="LA", record="0-0"), Player(name="Boston Player", team_abbr="BOS", position="G"), game("g")])
    await db_session.commit()
    async with await client_for(db_session, search.router) as client:
        result = (await client.get("/search?q=Boston")).json()
        assert len(result["players"]) == 1
        assert result["teams"][0]["url"] == "/teams/BOS"
        assert result["games"][0]["url"] == "/match/g"
        assert (await client.get("/search?q=%25%25")).json() == {"players":[],"teams":[],"games":[]}


@pytest.mark.asyncio
async def test_logs_resolve_identity_and_paginate_completed_games(db_session):
    from app.routers import player_games
    connection = await db_session.connection()
    await connection.run_sync(lambda conn: PlayerGameStat.__table__.create(conn, checkfirst=True))
    player = Player(name="Known Player", nba_id=123, team_abbr="BOS", position="G")
    unknown = Player(name="Unresolved Example Person", team_abbr="BOS", position="G")
    db_session.add_all([player, unknown, game("a"), game("b", "2025-02-01")])
    await db_session.flush()
    for id in ["a", "b"]:
        db_session.add(PlayerGameStat(game_id=id, nba_id=123, name=player.name, team_abbr="BOS", points=20))
    await db_session.commit()
    async with await client_for(db_session, player_games.router) as client:
        result = (await client.get(f"/players/{player.id}/games?season=2024-25&limit=1")).json()
        assert result["total"] == 2
        assert result["items"][0]["gameId"] == "b"
        assert result["items"][0]["opponent"] == "LAL"
        assert result["items"][0]["homeAway"] == "Away"
        assert result["coverage"]["importedGames"] == 2
        unresolved = (await client.get(f"/players/{unknown.id}/games")).json()
        assert unresolved["coverage"]["identityResolved"] is False
        assert (await client.get("/players/999/games")).status_code == 404


@pytest.mark.asyncio
async def test_analytics_season_options_include_game_only_imports(db_session):
    playoffs = game("only")
    playoffs.season_type = "playoffs"
    db_session.add(playoffs)
    await db_session.commit()
    async with await client_for(db_session, analytics.router) as client:
        result = (await client.get("/analytics/dashboard")).json()
        assert "2024-25" in result["seasons"]
