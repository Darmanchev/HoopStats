from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.config import Settings
from app.database import get_db
from app.models.game import Game
from app.models.player import Player
from app.models.player_season_stat import PlayerSeasonStat
from app.models.team import Team
from app.routers.analytics import router
from app.services import live_box_scores
from app.services.live_box_scores import match_official_game
from scripts import seed
from app.services import sync_status


def test_current_season_is_configurable_and_validated():
    assert Settings(current_season="2026-27").current_season == "2026-27"
    with pytest.raises(ValidationError):
        Settings(current_season="2026-28")


@pytest.mark.asyncio
async def test_failed_source_update_preserves_last_success(monkeypatch):
    stored = {}
    redis = AsyncMock()
    async def read(key, name):
        return stored.get(name)
    async def write(key, name, value):
        stored[name] = value
    redis.hget.side_effect = read
    redis.hset.side_effect = write
    monkeypatch.setattr(sync_status.Redis, "from_url", lambda *args, **kwargs: redis)
    import json
    await sync_status.record_sync_status("sync_games", "success", 3)
    success = json.loads(stored["sync_games"])
    await sync_status.record_sync_status("sync_games", "failed")
    failed = json.loads(stored["sync_games"])
    assert failed["state"] == "failed"
    assert failed["last_success"] == success["last_success"]
    assert failed["count"] == 3


def test_official_game_match_uses_eastern_date_and_never_guesses():
    game = Game(id="bdl:123", team1="BOS", team2="LAL", date="2026-10-22",
                start_time=datetime(2026, 10, 22, 1, tzinfo=timezone.utc))
    row = {"game_id": "0022600012", "away_abbr": "BOS", "home_abbr": "LAL", "date": "2026-10-21", "status": "live"}
    assert match_official_game(game, [row]) == "0022600012"
    assert match_official_game(game, [row, {**row, "game_id": "other"}]) is None
    assert match_official_game(game, [{**row, "date": "2026-10-22"}]) is None
    assert match_official_game(game, [{**row, "away_abbr": "LAL", "home_abbr": "BOS"}]) is None


@pytest.mark.asyncio
async def test_box_score_uses_official_id_but_saves_local_id(db_session, monkeypatch):
    today = datetime.now(timezone.utc).date().isoformat()
    game = Game(id="bdl:123", team1="BOS", team2="LAL", date=today, time="", venue="", season="2026-27", status="scheduled")
    db_session.add_all([Team(abbr="BOS", name="Celtics", city="Boston", record="0-0"), Team(abbr="LAL", name="Lakers", city="LA", record="0-0")])
    await db_session.flush()
    db_session.add(game)
    await db_session.commit()
    row = {"game_id": "0022600012", "away_abbr": "BOS", "home_abbr": "LAL", "date": today, "status": "live", "away_score": 30, "home_score": 20}
    monkeypatch.setattr(live_box_scores.nba, "fetch_live_scoreboard", lambda: [row])
    requested = []
    def boxscore(official_id):
        requested.append(official_id)
        return [{"game_id": official_id, "nba_id": 1, "team_abbr": "BOS"}]
    monkeypatch.setattr(live_box_scores.nba, "fetch_live_boxscore", boxscore)
    save = AsyncMock(return_value=1)
    monkeypatch.setattr(live_box_scores, "upsert_player_game_stats", save)
    monkeypatch.setattr(live_box_scores, "invalidate_live_caches", AsyncMock())
    assert await live_box_scores.sync_box_scores(db_session) == 1
    assert requested == ["0022600012"]
    assert save.await_args.args[1] == "bdl:123"
    assert save.await_args.args[2][0]["game_id"] == "bdl:123"
    assert game.is_today is True
    assert game.status == "live"


@pytest.mark.asyncio
async def test_seed_returns_failure_and_continues_with_counts(monkeypatch, capsys):
    monkeypatch.setattr(seed, "record_sync_status", AsyncMock())
    db = AsyncMock()
    bad = AsyncMock(side_effect=RuntimeError("Provider unavailable"))
    good = AsyncMock(return_value=30)
    assert await seed.run_import_steps(db, [("bad", bad), ("good", good)]) == 1
    good.assert_awaited_once_with(db)
    db.rollback.assert_awaited_once()
    output = capsys.readouterr().out
    assert "30 records" in output
    assert "1 succeeded, 1 failed" in output


@pytest.mark.asyncio
async def test_leaders_use_selected_season_instead_of_shared_player_stats(db_session):
    db_session.add(Team(abbr="BOS", name="Celtics", city="Boston", record="0-0"))
    player = Player(name="Stephen Curry", team_abbr="BOS", position="G", games_played=0,
                    pts=999, reb=0, ast=0, stl=0, blk=0, fg_pct=0, fg3_pct=0, ft_pct=0, mins=0, recent_games=0)
    db_session.add(player)
    await db_session.flush()
    for season, points in [("2023-24", 10), ("2024-25", 25)]:
        db_session.add(PlayerSeasonStat(player_id=player.id, season=season, primary_team_abbr="BOS", position="SG",
            games_played=79, pts=points, reb=4, ast=6, stl=0, blk=0, fg_pct=.5, fg3_pct=.4, ft_pct=.9, mins=30, recent_games=10))
    await db_session.commit()
    app = FastAPI()
    app.include_router(router)
    async def database():
        yield db_session
    app.dependency_overrides[get_db] = database
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        newest = (await client.get("/analytics/leaders")).json()["pts"][0]
        assert newest["pts"] == 25
        assert newest["season"] == "2024-25"
        old = (await client.get("/analytics/leaders?season=2023-24")).json()["pts"][0]
        assert old["pts"] == 10
        assert (await client.get("/analytics/leaders?season=2026-27")).json()["pts"] == []
        assert (await client.get("/analytics/leaders?season=2026-28")).status_code == 422
        dashboard = (await client.get("/analytics/dashboard")).json()
        assert dashboard["season"] == "2024-25"
        assert dashboard["playersAvailable"] is True
        assert dashboard["teamsAvailable"] is False
        assert dashboard["teams"] == []
