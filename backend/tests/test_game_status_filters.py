from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.dialects import postgresql

from app.models.game import Game
from app.routers import analytics, games
from app.services import predictions


def compiled(statement: object) -> str:
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


class EmptyResult:
    def scalars(self):
        return self

    def all(self):
        return []


class RecordingSession:
    def __init__(self) -> None:
        self.statements: list[object] = []

    async def execute(self, statement: object) -> EmptyResult:
        self.statements.append(statement)
        return EmptyResult()


@pytest.mark.asyncio
async def test_upcoming_and_past_queries_filter_by_game_status() -> None:
    upcoming_db = RecordingSession()
    past_db = RecordingSession()

    await games.get_upcoming(upcoming_db)  # type: ignore[arg-type]
    await games.get_past(
        skip=0,
        limit=100,
        season=None,
        season_type=None,
        db=past_db,  # type: ignore[arg-type]
    )

    assert "games.status = 'scheduled'" in compiled(upcoming_db.statements[0])
    assert "games.status = 'final'" in compiled(past_db.statements[0])
    assert "games.start_time" in compiled(upcoming_db.statements[0])


class FakeRedis:
    async def get(self, _key: str):
        return None

    async def set(self, _key: str, _value: object, **kwargs):
        return True

    async def eval(self, *_args: object):
        return 1


@pytest.mark.asyncio
async def test_elo_query_uses_only_final_games(monkeypatch: pytest.MonkeyPatch) -> None:
    db = RecordingSession()
    monkeypatch.setattr("app.ml.features.build_state", lambda _played: SimpleNamespace(elo={}))
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(redis=FakeRedis())))

    await analytics.get_elo(request, db)  # type: ignore[arg-type]

    assert "games.status = 'final'" in compiled(db.statements[0])


@pytest.mark.asyncio
async def test_predictions_ignore_live_games(monkeypatch: pytest.MonkeyPatch) -> None:
    final = Game(id="final", team1="BOS", team2="LAL", date="2026-09-20", time="", venue="", status="final", score1=100, score2=90)
    live = Game(id="live", team1="NYK", team2="BKN", date="2026-09-21", time="", venue="", status="live", score1=50, score2=48)
    scheduled = Game(id="next", team1="DEN", team2="PHX", date="2026-09-22", time="", venue="", status="scheduled", score1=None, score2=None)

    class Result:
        def scalars(self):
            return self

        def all(self):
            return [final, live, scheduled]

    class Session:
        commit = AsyncMock()

        async def execute(self, _statement: object):
            return Result()

    captured: list[dict] = []
    monkeypatch.setattr(predictions, "build_state", lambda played: captured.extend(played) or object())
    monkeypatch.setattr(predictions, "predict_game", lambda *_args: (55.0, "DEN"))

    await predictions.sync_predictions(Session())  # type: ignore[arg-type]

    assert [game["id"] for game in captured] == ["final"]
    assert scheduled.prediction == "DEN"
    assert live.prediction is None
