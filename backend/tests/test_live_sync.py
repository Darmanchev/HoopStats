from unittest.mock import AsyncMock
from contextlib import asynccontextmanager

import pytest
from sqlalchemy.dialects import postgresql

from app.models.game import Game
from app.services import sync as sync_module
from app.services.repositories import games as games_repo
from app.services.repositories import player_game_stats as player_stats_repo


LIVE_GAME = {
    "game_id": "0022500002",
    "away_abbr": "BOS",
    "home_abbr": "LAL",
    "date": "2026-09-21",
    "start_time": "2026-09-21T22:00:00Z",
    "status": "live",
    "status_text": "Q3 04:12",
    "period": 3,
    "clock": "PT04M12.00S",
    "away_score": 78,
    "home_score": 74,
    "venue": "Crypto.com Arena",
}

PLAYER = {
    "game_id": "0022500002",
    "nba_id": 2544,
    "name": "LeBron James",
    "team_abbr": "LAL",
    "points": 22,
    "rebounds": 7,
    "assists": 8,
    "steals": 2,
    "blocks": 1,
    "minutes": 32.5,
}


@asynccontextmanager
async def nested_transaction():
    yield


class ScalarResult:
    def __init__(self, value: object) -> None:
        self.value = value

    def scalar_one_or_none(self) -> object:
        return self.value


class ExistingGameSession:
    def __init__(self, game: Game) -> None:
        self.game = game

    async def execute(self, _statement: object) -> ScalarResult:
        return ScalarResult(self.game)

    def add(self, _value: object) -> None:
        raise AssertionError("existing game must be updated, not inserted")


class RecordingSession:
    def __init__(self) -> None:
        self.statements: list[object] = []

    async def execute(self, statement: object) -> None:
        self.statements.append(statement)


@pytest.mark.asyncio
async def test_live_game_updates_scores_before_final() -> None:
    game = Game(
        id=LIVE_GAME["game_id"],
        team1="BOS",
        team2="LAL",
        date="2026-09-21",
        time="7:30 PM ET",
        venue="Crypto.com Arena",
        is_today=True,
        status="scheduled",
        score1=None,
        score2=None,
    )

    affected = await games_repo.upsert_live_games(
        ExistingGameSession(game),  # type: ignore[arg-type]
        [LIVE_GAME],  # type: ignore[list-item]
    )

    assert affected == [LIVE_GAME["game_id"]]
    assert (game.status, game.score1, game.score2, game.period) == (
        "live",
        78,
        74,
        3,
    )


@pytest.mark.asyncio
async def test_reset_today_only_updates_today_flag() -> None:
    session = RecordingSession()

    await games_repo.reset_today_flag(session)  # type: ignore[arg-type]

    statement = session.statements[0]
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )
    assert sql == "UPDATE games SET is_today=false"


@pytest.mark.asyncio
async def test_player_stats_upsert_updates_unique_game_player_row() -> None:
    session = RecordingSession()

    count = await player_stats_repo.upsert_player_game_stats(
        session,  # type: ignore[arg-type]
        LIVE_GAME["game_id"],
        [PLAYER],  # type: ignore[list-item]
    )

    assert count == 1
    sql = str(session.statements[0].compile(dialect=postgresql.dialect()))
    assert "ON CONFLICT (game_id, nba_id) DO UPDATE" in sql
    assert "points = excluded.points" in sql


@pytest.mark.asyncio
async def test_sync_games_continues_after_one_boxscore_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    second_game = {**LIVE_GAME, "game_id": "0022500003"}
    monkeypatch.setattr(
        sync_module.nba_client,
        "fetch_live_scoreboard",
        lambda: [LIVE_GAME, second_game],
    )

    def fetch_boxscore(game_id: str) -> list[dict]:
        if game_id == LIVE_GAME["game_id"]:
            raise RuntimeError("upstream unavailable")
        return [{**PLAYER, "game_id": game_id}]

    monkeypatch.setattr(
        sync_module.nba_client,
        "fetch_live_boxscore",
        fetch_boxscore,
        raising=False,
    )
    upsert_games = AsyncMock(
        return_value=[LIVE_GAME["game_id"], second_game["game_id"]]
    )
    upsert_players = AsyncMock(return_value=1)
    invalidate = AsyncMock()
    reset_today = AsyncMock()
    monkeypatch.setattr(sync_module.games_repo, "upsert_live_games", upsert_games)
    monkeypatch.setattr(sync_module.games_repo, "reset_today_flag", reset_today)
    monkeypatch.setattr(
        sync_module,
        "player_stats_repo",
        type("PlayerStatsRepo", (), {"upsert_player_game_stats": upsert_players}),
        raising=False,
    )
    monkeypatch.setattr(
        sync_module,
        "invalidate_live_caches",
        invalidate,
        raising=False,
    )

    class Session:
        commit = AsyncMock()
        flush = AsyncMock()

        def begin_nested(self):
            return nested_transaction()

    db = Session()
    await sync_module.sync_games(db)  # type: ignore[arg-type]

    assert upsert_players.await_count == 1
    assert upsert_players.await_args.args[1] == second_game["game_id"]
    db.commit.assert_awaited_once_with()
    invalidate.assert_awaited_once_with(
        [LIVE_GAME["game_id"], second_game["game_id"]]
    )


@pytest.mark.asyncio
async def test_sync_games_isolates_database_boxscore_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    second_game = {**LIVE_GAME, "game_id": "0022500003"}
    monkeypatch.setattr(
        sync_module.nba_client,
        "fetch_live_scoreboard",
        lambda: [LIVE_GAME, second_game],
    )
    monkeypatch.setattr(
        sync_module.nba_client,
        "fetch_live_boxscore",
        lambda game_id: [{**PLAYER, "game_id": game_id}],
    )
    monkeypatch.setattr(
        sync_module.games_repo,
        "reset_today_flag",
        AsyncMock(),
    )
    monkeypatch.setattr(
        sync_module.games_repo,
        "upsert_live_games",
        AsyncMock(return_value=[LIVE_GAME["game_id"], second_game["game_id"]]),
    )
    upsert_players = AsyncMock(side_effect=[RuntimeError("constraint"), 1])
    monkeypatch.setattr(
        sync_module.player_stats_repo,
        "upsert_player_game_stats",
        upsert_players,
    )
    monkeypatch.setattr(sync_module, "invalidate_live_caches", AsyncMock())
    monkeypatch.setattr(sync_module, "invalidate_elo_cache", AsyncMock())

    class Session:
        def __init__(self) -> None:
            self.flush = AsyncMock()
            self.commit = AsyncMock()
            self.savepoints = 0

        def begin_nested(self):
            self.savepoints += 1
            return nested_transaction()

    db = Session()
    await sync_module.sync_games(db)  # type: ignore[arg-type]

    db.flush.assert_awaited_once_with()
    assert db.savepoints == 2
    assert upsert_players.await_count == 2
    db.commit.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_successful_empty_scoreboard_clears_stale_today_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sync_module.nba_client,
        "fetch_live_scoreboard",
        lambda: [],
    )
    reset_today = AsyncMock()
    invalidate = AsyncMock()
    monkeypatch.setattr(sync_module.games_repo, "reset_today_flag", reset_today)
    monkeypatch.setattr(
        sync_module,
        "invalidate_live_caches",
        invalidate,
        raising=False,
    )

    class Session:
        commit = AsyncMock()

    db = Session()
    await sync_module.sync_games(db)  # type: ignore[arg-type]

    reset_today.assert_awaited_once_with(db)
    db.commit.assert_awaited_once_with()
    invalidate.assert_awaited_once_with([])
