import pytest

from app import scheduler as scheduler_module


class FakeSessionContext:
    async def __aenter__(self) -> object:
        return object()

    async def __aexit__(self, *_args: object) -> None:
        return None


@pytest.mark.asyncio
async def test_run_sync_refreshes_schedule_before_predictions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    expected_order = [
        "teams",
        "games",
        "schedule",
        "team_stats",
        "players",
        "injuries",
        "predictions",
    ]

    def make_sync(name: str):
        async def sync(_db: object) -> None:
            calls.append(name)

        return sync

    monkeypatch.setattr(
        scheduler_module,
        "SessionLocal",
        lambda: FakeSessionContext(),
    )
    for name in expected_order:
        monkeypatch.setattr(
            scheduler_module,
            f"sync_{name}",
            make_sync(name),
            raising=False,
        )

    await scheduler_module.run_sync()

    assert calls == expected_order
