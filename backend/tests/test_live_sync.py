import pytest
from sqlalchemy.dialects import postgresql

from app.models.game import Game
from app.services.repositories import games as games_repo
from app.services.repositories import player_game_stats as player_stats_repo


LIVE_GAME = {
    "game_id": "bdl:15907925",
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
    "venue": "",
    "season": "2025-26",
    "season_type": "regular",
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

    affected = await games_repo.upsert_games(
        ExistingGameSession(game),  # type: ignore[arg-type]
        [LIVE_GAME],  # type: ignore[list-item]
        today="2026-09-21",
    )

    assert affected == [LIVE_GAME["game_id"]]
    assert (game.status, game.score1, game.score2, game.period) == (
        "live",
        78,
        74,
        3,
    )


@pytest.mark.asyncio
async def test_incomplete_live_score_does_not_erase_stored_scores() -> None:
    game = Game(
        id=LIVE_GAME["game_id"],
        team1="BOS",
        team2="LAL",
        date="2026-09-21",
        time="Q3",
        venue="Crypto.com Arena",
        is_today=True,
        status="live",
        score1=78,
        score2=74,
    )
    incomplete = {**LIVE_GAME, "away_score": None}

    await games_repo.upsert_games(
        ExistingGameSession(game),  # type: ignore[arg-type]
        [incomplete],  # type: ignore[list-item]
        today="2026-09-21",
    )

    assert (game.score1, game.score2) == (78, 74)


@pytest.mark.asyncio
async def test_final_game_reconciles_partial_live_score() -> None:
    game = Game(
        id=LIVE_GAME["game_id"],
        team1="BOS",
        team2="LAL",
        date="2026-09-21",
        time="Q3",
        venue="",
        status="live",
        score1=70,
        score2=65,
    )

    final = {
        **LIVE_GAME,
        "status": "final",
        "status_text": "Final",
        "period": 4,
        "clock": None,
        "away_score": 110,
        "home_score": 104,
        "season": "2025-26",
        "season_type": "playoffs",
    }

    await games_repo.upsert_games(
        ExistingGameSession(game),  # type: ignore[arg-type]
        [final],  # type: ignore[list-item]
    )

    assert game.status == "final"
    assert (game.score1, game.score2) == (110, 104)
    assert game.season == "2025-26"
    assert game.season_type == "playoffs"


@pytest.mark.asyncio
async def test_scheduled_update_preserves_stored_scores_and_sets_today() -> None:
    game = Game(
        id=LIVE_GAME["game_id"],
        team1="BOS",
        team2="LAL",
        date="2026-09-20",
        time="Final",
        venue="",
        is_today=False,
        status="final",
        score1=110,
        score2=104,
    )
    scheduled = {
        **LIVE_GAME,
        "status": "scheduled",
        "status_text": "7:30 PM ET",
        "period": None,
        "clock": None,
        "away_score": None,
        "home_score": None,
    }

    await games_repo.upsert_games(
        ExistingGameSession(game),  # type: ignore[arg-type]
        [scheduled],  # type: ignore[list-item]
        today="2026-09-21",
    )

    assert game.is_today is True
    assert (game.score1, game.score2) == (110, 104)


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
