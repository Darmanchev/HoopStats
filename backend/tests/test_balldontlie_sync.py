from datetime import date
from unittest.mock import AsyncMock, call

import pytest

from app.services import sync as sync_module
from app.services.clients.balldontlie import (
    BallDontLieConfigurationError,
    BallDontLieError,
)


RAW_TEAM = {
    "id": 10,
    "abbreviation": "GSW",
    "city": "Golden State",
    "name": "Warriors",
    "conference": "West",
}

RAW_PLAYER = {
    "id": 115,
    "first_name": "Stephen",
    "last_name": "Curry",
    "position": "G",
    "jersey_number": "30",
    "team": {"abbreviation": "GSW"},
}

RAW_GAME = {
    "id": 15907925,
    "date": "2026-09-23",
    "season": 2026,
    "status": "3rd Qtr",
    "status_state": "in_progress",
    "period": 3,
    "time": "4:12",
    "postseason": False,
    "postponed": False,
    "home_team_score": 74,
    "visitor_team_score": 78,
    "datetime": "2026-09-23T22:00:00.000Z",
    "home_team": {
        "id": 14,
        "conference": "West",
        "city": "Los Angeles",
        "name": "Lakers",
        "abbreviation": "LAL",
    },
    "visitor_team": {
        "id": 2,
        "conference": "East",
        "city": "Boston",
        "name": "Celtics",
        "abbreviation": "BOS",
    },
}


class FakeClient:
    def __init__(
        self,
        *,
        teams: list[dict] | None = None,
        players: list[dict] | None = None,
        games: list[dict] | None = None,
    ) -> None:
        self.get_teams = AsyncMock(return_value=teams or [])
        self.get_players = AsyncMock(return_value=players or [])
        self.get_games = AsyncMock(return_value=games or [])

    async def __aenter__(self) -> "FakeClient":
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None


class TeamAbbrScalars:
    def __init__(self, abbreviations: list[str]) -> None:
        self.abbreviations = abbreviations

    def all(self) -> list[str]:
        return self.abbreviations


class TeamAbbrResult:
    def __init__(self, abbreviations: list[str]) -> None:
        self.abbreviations = abbreviations

    def scalars(self) -> TeamAbbrScalars:
        return TeamAbbrScalars(self.abbreviations)


class FakeSession:
    def __init__(self, team_abbrs: list[str] | None = None) -> None:
        self.team_abbrs = team_abbrs or []
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    async def execute(self, _statement: object) -> TeamAbbrResult:
        return TeamAbbrResult(self.team_abbrs)


@pytest.mark.asyncio
async def test_sync_teams_uses_balldontlie_profiles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = FakeClient(teams=[RAW_TEAM])
    db = FakeSession()
    upsert = AsyncMock(return_value=1)
    invalidate = AsyncMock()
    monkeypatch.setattr(
        sync_module,
        "create_balldontlie_client",
        lambda: client,
        raising=False,
    )
    monkeypatch.setattr(sync_module.teams_repo, "upsert_teams", upsert)
    monkeypatch.setattr(sync_module, "invalidate_teams_cache", invalidate)

    await sync_module.sync_teams(db)  # type: ignore[arg-type]

    client.get_teams.assert_awaited_once_with()
    upsert.assert_awaited_once_with(db, [{
        "balldontlie_id": 10,
        "abbr": "GSW",
        "city": "Golden State",
        "name": "Warriors",
        "conference": "West",
    }])
    db.commit.assert_awaited_once_with()
    invalidate.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_sync_games_fetches_date_before_resetting_today_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = FakeClient(games=[RAW_GAME])
    db = FakeSession()
    reset_today = AsyncMock()
    upsert = AsyncMock(return_value=["bdl:15907925"])
    invalidate_live = AsyncMock()
    invalidate_elo = AsyncMock()
    monkeypatch.setattr(
        sync_module,
        "create_balldontlie_client",
        lambda: client,
    )
    monkeypatch.setattr(sync_module.games_repo, "reset_today_flag", reset_today)
    monkeypatch.setattr(sync_module.games_repo, "upsert_games", upsert)
    monkeypatch.setattr(sync_module, "invalidate_live_caches", invalidate_live)
    monkeypatch.setattr(sync_module, "invalidate_elo_cache", invalidate_elo)

    await sync_module.sync_games(
        db,  # type: ignore[arg-type]
        today=date(2026, 9, 23),
    )

    client.get_games.assert_awaited_once_with(dates=["2026-09-23"])
    reset_today.assert_awaited_once_with(db)
    upsert.assert_awaited_once_with(
        db,
        [{
            "game_id": "bdl:15907925",
            "away_abbr": "BOS",
            "home_abbr": "LAL",
            "date": "2026-09-23",
            "start_time": "2026-09-23T22:00:00.000Z",
            "status": "live",
            "status_text": "3rd Qtr",
            "period": 3,
            "clock": "4:12",
            "away_score": 78,
            "home_score": 74,
            "venue": "",
            "season": "2026-27",
            "season_type": "regular",
        }],
        today="2026-09-23",
    )
    db.commit.assert_awaited_once_with()
    invalidate_live.assert_awaited_once_with(["bdl:15907925"])
    invalidate_elo.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_invalid_games_response_causes_no_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = FakeClient(games=[{"unexpected": "shape"}])
    db = FakeSession()
    reset_today = AsyncMock()
    upsert = AsyncMock()
    invalidate_live = AsyncMock()
    monkeypatch.setattr(
        sync_module,
        "create_balldontlie_client",
        lambda: client,
    )
    monkeypatch.setattr(sync_module.games_repo, "reset_today_flag", reset_today)
    monkeypatch.setattr(sync_module.games_repo, "upsert_games", upsert)
    monkeypatch.setattr(sync_module, "invalidate_live_caches", invalidate_live)

    await sync_module.sync_games(
        db,  # type: ignore[arg-type]
        today=date(2026, 9, 23),
    )

    reset_today.assert_not_awaited()
    upsert.assert_not_awaited()
    db.commit.assert_not_awaited()
    invalidate_live.assert_not_awaited()
    db.rollback.assert_awaited_once_with()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "provider_error",
    [
        BallDontLieConfigurationError("BALLDONTLIE API key is required"),
        BallDontLieError("provider unavailable"),
    ],
)
async def test_games_provider_error_causes_no_writes(
    monkeypatch: pytest.MonkeyPatch,
    provider_error: BallDontLieError,
) -> None:
    client = FakeClient()
    client.get_games.side_effect = provider_error
    db = FakeSession()
    reset_today = AsyncMock()
    upsert = AsyncMock()
    invalidate_live = AsyncMock()
    monkeypatch.setattr(
        sync_module,
        "create_balldontlie_client",
        lambda: client,
    )
    monkeypatch.setattr(sync_module.games_repo, "reset_today_flag", reset_today)
    monkeypatch.setattr(sync_module.games_repo, "upsert_games", upsert)
    monkeypatch.setattr(sync_module, "invalidate_live_caches", invalidate_live)

    await sync_module.sync_games(
        db,  # type: ignore[arg-type]
        today=date(2026, 9, 23),
    )

    reset_today.assert_not_awaited()
    upsert.assert_not_awaited()
    db.commit.assert_not_awaited()
    invalidate_live.assert_not_awaited()
    db.rollback.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_sync_players_keeps_profiles_for_known_teams(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unknown_team_player = {
        **RAW_PLAYER,
        "id": 999,
        "team": {"abbreviation": "UNK"},
    }
    client = FakeClient(players=[RAW_PLAYER, unknown_team_player])
    db = FakeSession(["GSW"])
    upsert = AsyncMock(return_value=(1, 0))
    monkeypatch.setattr(
        sync_module,
        "create_balldontlie_client",
        lambda: client,
        raising=False,
    )
    monkeypatch.setattr(sync_module.players_repo, "upsert_players", upsert)

    await sync_module.sync_players(db)  # type: ignore[arg-type]

    client.get_players.assert_awaited_once_with()
    upsert.assert_awaited_once_with(db, [{
        "balldontlie_id": 115,
        "name": "Stephen Curry",
        "team_abbr": "GSW",
        "position": "G",
        "jersey_number": "30",
    }])
    db.commit.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_sync_schedule_fetches_thirty_day_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = FakeClient(games=[RAW_GAME])
    db = FakeSession()
    upsert = AsyncMock(return_value=["bdl:15907925"])
    events: list[object] = []

    async def commit() -> None:
        events.append("commit")

    async def invalidate_live(game_ids: list[str]) -> None:
        events.append(("invalidate_live", game_ids))

    async def invalidate_elo() -> None:
        events.append("invalidate_elo")

    db.commit.side_effect = commit
    monkeypatch.setattr(
        sync_module,
        "create_balldontlie_client",
        lambda: client,
    )
    monkeypatch.setattr(sync_module.games_repo, "upsert_games", upsert)
    monkeypatch.setattr(sync_module, "invalidate_live_caches", invalidate_live)
    monkeypatch.setattr(sync_module, "invalidate_elo_cache", invalidate_elo)

    await sync_module.sync_schedule(
        db,  # type: ignore[arg-type]
        start_date=date(2026, 9, 23),
    )

    client.get_games.assert_awaited_once_with(
        start_date="2026-09-23",
        end_date="2026-10-23",
    )
    upsert.assert_awaited_once()
    assert upsert.await_args.kwargs == {"today": "2026-09-23"}
    db.commit.assert_awaited_once_with()
    assert events == [
        "commit",
        ("invalidate_live", ["bdl:15907925"]),
        "invalidate_elo",
    ]


@pytest.mark.asyncio
async def test_historical_sync_fetches_regular_and_playoff_games(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    regular = {
        **RAW_GAME,
        "id": 1,
        "status": "Final",
        "status_state": "final",
        "visitor_team_score": 110,
        "home_team_score": 104,
    }
    playoffs = {
        **regular,
        "id": 2,
        "postseason": True,
    }
    client = FakeClient()
    client.get_games.side_effect = [[regular], [playoffs]]
    db = FakeSession()
    upsert = AsyncMock(return_value=["bdl:1", "bdl:2"])
    invalidate_elo = AsyncMock()
    monkeypatch.setattr(
        sync_module,
        "create_balldontlie_client",
        lambda: client,
    )
    monkeypatch.setattr(sync_module.games_repo, "upsert_games", upsert)
    monkeypatch.setattr(sync_module, "invalidate_elo_cache", invalidate_elo)

    await sync_module.sync_historical_games(db, season="2025-26")  # type: ignore[arg-type]

    assert client.get_games.await_args_list == [
        call(seasons=[2025], season_type="regular"),
        call(seasons=[2025], season_type="playoffs"),
    ]
    upsert.assert_awaited_once()
    games = upsert.await_args.args[1]
    assert [game["game_id"] for game in games] == ["bdl:1", "bdl:2"]
    db.commit.assert_awaited_once_with()
    invalidate_elo.assert_awaited_once_with()


@pytest.mark.asyncio
@pytest.mark.parametrize("season", ["2025", "25-26", "2025-28"])
async def test_historical_sync_rejects_invalid_season_before_request(
    monkeypatch: pytest.MonkeyPatch,
    season: str,
) -> None:
    client = FakeClient()
    db = FakeSession()
    monkeypatch.setattr(
        sync_module,
        "create_balldontlie_client",
        lambda: client,
    )

    with pytest.raises(ValueError, match="Invalid NBA season"):
        await sync_module.sync_historical_games(db, season=season)  # type: ignore[arg-type]

    client.get_games.assert_not_awaited()
