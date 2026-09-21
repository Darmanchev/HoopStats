from unittest.mock import AsyncMock

import pytest

from app.services import sync as sync_module


class EmptyScalars:
    def all(self) -> list[object]:
        return []


class EmptyResult:
    def scalars(self) -> EmptyScalars:
        return EmptyScalars()


class EmptyTeamSession:
    def __init__(self) -> None:
        self.committed = False

    async def execute(self, _statement: object) -> EmptyResult:
        return EmptyResult()

    async def commit(self) -> None:
        self.committed = True


@pytest.mark.asyncio
async def test_team_stats_sync_invalidates_combined_teams_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invalidate = AsyncMock()
    monkeypatch.setattr(
        sync_module,
        "invalidate_teams_cache",
        invalidate,
        raising=False,
    )
    db = EmptyTeamSession()

    await sync_module.sync_team_stats(db)  # type: ignore[arg-type]

    assert db.committed is True
    invalidate.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_teams_sync_invalidates_combined_teams_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invalidate = AsyncMock()
    upsert_teams = AsyncMock(return_value=0)
    monkeypatch.setattr(sync_module, "invalidate_teams_cache", invalidate)
    monkeypatch.setattr(sync_module.teams_repo, "upsert_teams", upsert_teams)
    monkeypatch.setattr(
        sync_module.nba_client,
        "fetch_teams",
        lambda: [{"id": 1, "abbreviation": "BOS"}],
    )
    monkeypatch.setattr(
        sync_module.nba_client,
        "fetch_standings",
        lambda _season: {1: "4-1"},
    )

    await sync_module.sync_teams(EmptyTeamSession())  # type: ignore[arg-type]

    invalidate.assert_awaited_once_with()
