import pytest

from app.models.injury import Injury
from app.services.repositories.injuries import replace_all_injuries


class FakeScalars:
    def __init__(self, values: list[Injury]) -> None:
        self.values = values

    def all(self) -> list[Injury]:
        return self.values


class FakeResult:
    def __init__(self, values: list[Injury]) -> None:
        self.values = values

    def scalars(self) -> FakeScalars:
        return FakeScalars(self.values)


class FakeSession:
    def __init__(self, *, fail_commit: bool = False) -> None:
        self.fail_commit = fail_commit
        self.added: list[Injury] = []
        self.deleted: list[Injury] = []
        self.commit_calls = 0
        self.rollback_calls = 0

    async def execute(self, _statement: object) -> FakeResult:
        return FakeResult(
            [
                Injury(
                    id=1,
                    team_abbr="BOS",
                    player_name="Old Player",
                    position="F",
                    injury="Old injury",
                    status="Out",
                )
            ]
        )

    async def delete(self, injury: Injury) -> None:
        self.deleted.append(injury)

    def add(self, injury: Injury) -> None:
        self.added.append(injury)

    async def commit(self) -> None:
        self.commit_calls += 1
        if self.fail_commit:
            raise RuntimeError("database write failed")

    async def rollback(self) -> None:
        self.rollback_calls += 1


INJURY_PAYLOAD = [
    {
        "displayName": "Boston Celtics",
        "injuries": [
            {
                "athlete": {
                    "displayName": "Example Player",
                    "position": {"abbreviation": "F"},
                },
                "details": {
                    "type": "Ankle",
                    "detail": "sprain",
                },
                "status": "Questionable",
            }
        ],
    }
]


@pytest.mark.asyncio
async def test_replace_all_injuries_commits_once() -> None:
    db = FakeSession()

    count = await replace_all_injuries(db, INJURY_PAYLOAD)

    assert count == 1
    assert len(db.added) == 1
    assert db.commit_calls == 1


@pytest.mark.asyncio
async def test_replace_all_injuries_rolls_back_failed_transaction() -> None:
    db = FakeSession(fail_commit=True)

    with pytest.raises(RuntimeError, match="database write failed"):
        await replace_all_injuries(db, INJURY_PAYLOAD)

    assert db.rollback_calls == 1
