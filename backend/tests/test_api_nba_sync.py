from unittest.mock import AsyncMock, Mock

import pytest

from app.services import player_seasons
from app.services.clients.api_nba import ApiNbaError


NORMALIZED_30_TEAMS = [
    {"api_nba_id": index, "abbr": f"T{index:02d}"}
    for index in range(1, 31)
]
RAW_30_TEAMS = [
    {
        "id": team["api_nba_id"],
        "code": team["abbr"],
        "nbaFranchise": True,
        "allStar": False,
    }
    for team in NORMALIZED_30_TEAMS
]


class FakeScalars:
    def all(self) -> list[str]:
        return [team["abbr"] for team in NORMALIZED_30_TEAMS]


class FakeResult:
    def scalars(self) -> FakeScalars:
        return FakeScalars()


class FakeSession:
    def __init__(self) -> None:
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    async def execute(self, _statement: object) -> FakeResult:
        return FakeResult()


class FakeApiNbaClient:
    def __init__(self, *, teams: list[dict], fail_team: int | None = None) -> None:
        self.get_teams = AsyncMock(return_value=teams)
        self.get_players = AsyncMock(side_effect=self._players)
        self.get_player_statistics = AsyncMock(side_effect=self._stats)
        self.fail_team = fail_team

    async def __aenter__(self) -> "FakeApiNbaClient":
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def _players(self, *, team_id: int, season: int) -> list[dict]:
        assert season == 2025
        if team_id == self.fail_team:
            raise ApiNbaError("provider unavailable")
        return [{
            "id": team_id * 100,
            "firstname": "Test",
            "lastname": str(team_id),
            "leagues": {"standard": {"pos": "G"}},
        }]

    async def _stats(self, *, team_id: int, season: int) -> list[dict]:
        assert season == 2025
        return []


@pytest.mark.asyncio
async def test_sync_player_season_fetches_each_team_and_commits_once(
    monkeypatch,
) -> None:
    client = FakeApiNbaClient(teams=RAW_30_TEAMS)
    db = FakeSession()
    upsert = AsyncMock(return_value=(450, 450))
    aggregate = Mock(return_value=([], []))
    monkeypatch.setattr(player_seasons, "create_api_nba_client", lambda: client)
    monkeypatch.setattr(
        player_seasons,
        "normalize_api_nba_teams",
        lambda raw, valid: NORMALIZED_30_TEAMS,
    )
    monkeypatch.setattr(player_seasons, "aggregate_player_season", aggregate)
    monkeypatch.setattr(
        player_seasons.player_seasons_repo,
        "upsert_player_season",
        upsert,
    )

    result = await player_seasons.sync_player_season(db, "2025-26")

    assert result == (450, 450)
    assert client.get_teams.await_count == 1
    assert client.get_players.await_count == 30
    assert client.get_player_statistics.await_count == 30
    assert client.get_players.await_args_list[0].kwargs == {
        "team_id": 1,
        "season": 2025,
    }
    aggregate.assert_called_once()
    upsert.assert_awaited_once()
    db.commit.assert_awaited_once_with()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_provider_failure_rolls_back_without_repository_write(
    monkeypatch,
) -> None:
    client = FakeApiNbaClient(teams=RAW_30_TEAMS, fail_team=17)
    db = FakeSession()
    upsert = AsyncMock()
    monkeypatch.setattr(player_seasons, "create_api_nba_client", lambda: client)
    monkeypatch.setattr(
        player_seasons,
        "normalize_api_nba_teams",
        lambda raw, valid: NORMALIZED_30_TEAMS,
    )
    monkeypatch.setattr(
        player_seasons.player_seasons_repo,
        "upsert_player_season",
        upsert,
    )

    with pytest.raises(ApiNbaError, match="provider unavailable"):
        await player_seasons.sync_player_season(db, "2025-26")

    upsert.assert_not_awaited()
    db.commit.assert_not_awaited()
    db.rollback.assert_awaited_once_with()
    assert client.get_players.await_count == 17
    assert client.get_player_statistics.await_count == 16


@pytest.mark.asyncio
async def test_incomplete_team_directory_rolls_back_before_roster_calls(
    monkeypatch,
) -> None:
    client = FakeApiNbaClient(teams=RAW_30_TEAMS[:29])
    db = FakeSession()
    upsert = AsyncMock()
    monkeypatch.setattr(player_seasons, "create_api_nba_client", lambda: client)
    monkeypatch.setattr(
        player_seasons,
        "normalize_api_nba_teams",
        lambda raw, valid: NORMALIZED_30_TEAMS[:29],
    )
    monkeypatch.setattr(
        player_seasons.player_seasons_repo,
        "upsert_player_season",
        upsert,
    )

    with pytest.raises(ValueError, match="Expected 30"):
        await player_seasons.sync_player_season(db, "2025-26")

    client.get_players.assert_not_awaited()
    upsert.assert_not_awaited()
    db.rollback.assert_awaited_once_with()
