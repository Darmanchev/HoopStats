# Match Detail API Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal automated backend test foundation and ensure `GET /games/{id}` returns the complete match-detail contract, including prediction and nested team fields.

**Architecture:** Test the real FastAPI router and response serialization through an in-process HTTP client. Replace only the database boundary with a small deterministic fake so the tests do not need PostgreSQL, Redis, or external NBA services. Fix the contract at the route declaration by using the schema that the handler already constructs.

**Tech Stack:** Python 3.13, FastAPI, Pydantic 2, SQLAlchemy 2, HTTPX ASGI transport, pytest, pytest-asyncio, uv.

**Spec:** Bounded design approved in chat on 2026-09-12; no separate design document is required.

## Global Constraints

- Follow red-green-refactor: observe the contract tests fail before changing production code.
- Do not connect to PostgreSQL, Redis, NBA, or ESPN from these tests.
- Assert the consumer-visible JSON response rather than implementation details.
- Keep the production change limited to the match-detail response model.
- Preserve all unrelated working-tree changes and stage only files listed in this plan.

## File Structure

- Modify `pyproject.toml`: declare backend test dependencies and pytest discovery settings.
- Modify `uv.lock`: lock the new development dependencies using uv.
- Create `backend/tests/test_games_api.py`: exercise the real games router through HTTP with an isolated database fake.
- Modify `backend/app/routers/games.py:106`: expose the full `UpcomingGameSchema` response contract.

---

### Task 1: Test and repair the match-detail response contract

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Create: `backend/tests/test_games_api.py`
- Modify: `backend/app/routers/games.py:106`

**Interfaces:**
- Consumes: `GET /games/{id}`, `get_db`, `Game`, `Team`, and `UpcomingGameSchema`.
- Produces: a match-detail response containing `isToday`, `win1`, `prediction`, `homeTeam`, and `awayTeam`; a reusable backend pytest command through `uv run pytest`.

- [ ] **Step 1: Add the test dependencies**

Run from the repository root:

```bash
uv add --dev pytest pytest-asyncio
```

Expected result: `pyproject.toml` gains a development dependency group and `uv.lock` is updated.

- [ ] **Step 2: Configure pytest discovery**

Add this section to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = ["backend"]
testpaths = ["backend/tests"]
```

This keeps imports consistent with the backend container, where `app` is the top-level package.

- [ ] **Step 3: Write the failing API contract tests**

Create `backend/tests/test_games_api.py`:

```python
from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.models.game import Game
from app.models.team import Team
from app.routers import games


class FakeResult:
    def __init__(self, game: Game | None) -> None:
        self.game = game

    def scalar_one_or_none(self) -> Game | None:
        return self.game


class FakeSession:
    def __init__(self, game: Game | None) -> None:
        self.game = game

    async def execute(self, _statement: object) -> FakeResult:
        return FakeResult(self.game)


def make_game(
    *,
    win1: float | None = 61.2,
    prediction: str | None = "Boston has the stronger recent form.",
) -> Game:
    game = Game(
        id="0022600001",
        team1="BOS",
        team2="LAL",
        date="2026-10-20",
        time="7:30 PM ET",
        venue="TD Garden",
        is_today=False,
        season_type="regular",
        season="2026-27",
        win1=win1,
        prediction=prediction,
        score1=None,
        score2=None,
    )
    game.home_team = Team(
        abbr="BOS",
        nba_id=1610612738,
        name="Celtics",
        city="Boston",
        record="4-1",
    )
    game.away_team = Team(
        abbr="LAL",
        nba_id=1610612747,
        name="Lakers",
        city="Los Angeles",
        record="3-2",
    )
    return game


def make_app(game: Game | None) -> FastAPI:
    app = FastAPI()
    app.include_router(games.router)

    async def override_get_db() -> AsyncIterator[FakeSession]:
        yield FakeSession(game)

    app.dependency_overrides[get_db] = override_get_db
    return app


async def request_game(game: Game | None, game_id: str = "0022600001"):
    app = make_app(game)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(f"/games/{game_id}")


@pytest.mark.asyncio
async def test_match_detail_returns_prediction_and_team_details() -> None:
    response = await request_game(make_game())

    assert response.status_code == 200
    assert response.json() == {
        "id": "0022600001",
        "team1": "BOS",
        "team2": "LAL",
        "date": "2026-10-20",
        "time": "7:30 PM ET",
        "venue": "TD Garden",
        "seasonType": "regular",
        "season": "2026-27",
        "isToday": False,
        "win1": 61.2,
        "prediction": "Boston has the stronger recent form.",
        "homeTeam": {
            "abbr": "BOS",
            "name": "Celtics",
            "city": "Boston",
            "record": "4-1",
        },
        "awayTeam": {
            "abbr": "LAL",
            "name": "Lakers",
            "city": "Los Angeles",
            "record": "3-2",
        },
    }


@pytest.mark.asyncio
async def test_match_detail_preserves_null_prediction_fields() -> None:
    response = await request_game(make_game(win1=None, prediction=None))

    assert response.status_code == 200
    assert response.json()["win1"] is None
    assert response.json()["prediction"] is None


@pytest.mark.asyncio
async def test_match_detail_returns_404_when_game_does_not_exist() -> None:
    response = await request_game(None, "missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "Game not found"}
```

- [ ] **Step 4: Run the tests and verify the contract failure**

Run:

```bash
uv run pytest backend/tests/test_games_api.py -v
```

Expected result before the production fix:

- `test_match_detail_returns_prediction_and_team_details` fails because the JSON omits `isToday`, `win1`, `prediction`, `homeTeam`, and `awayTeam`.
- `test_match_detail_preserves_null_prediction_fields` fails because `win1` and `prediction` are absent.
- The 404 characterization test passes.

If the failure is an import, fixture, or setup error instead, correct the test harness and rerun until the tests fail specifically on the missing response fields.

- [ ] **Step 5: Apply the minimal production fix**

In `backend/app/routers/games.py`, remove the now-unused `GameBase` import:

```python
from ..schemas.game import PastGameSchema, UpcomingGameSchema
```

Then change the route declaration:

```python
@router.get("/{id}", response_model=UpcomingGameSchema)
```

Keep the existing handler body unchanged. It already constructs `UpcomingGameSchema`; the incorrect `GameBase` declaration is what causes FastAPI to filter out the additional fields.

- [ ] **Step 6: Run the focused tests and verify green**

Run:

```bash
uv run pytest backend/tests/test_games_api.py -v
```

Expected result: all three tests pass.

- [ ] **Step 7: Run the complete backend test command**

Run:

```bash
uv run pytest -q
```

Expected result: all discovered backend tests pass with no warnings or errors.

- [ ] **Step 8: Verify the frontend still accepts the API contract**

Run:

```bash
cd frontend
npm run lint
npm run build -- --outDir /tmp/hoopstats-frontend-build --emptyOutDir
```

Expected result: both commands exit successfully. Building into `/tmp` avoids modifying the repository's tracked `frontend/dist` files.

- [ ] **Step 9: Review the exact change set**

Run from the repository root:

```bash
git diff --check
git diff -- pyproject.toml uv.lock backend/tests/test_games_api.py backend/app/routers/games.py
```

Expected result: no whitespace errors, no unrelated files in the displayed diff, and the production behavior change remains limited to the response-model correction.

- [ ] **Step 10: Commit only the scoped files when requested**

```bash
git add pyproject.toml uv.lock backend/tests/test_games_api.py backend/app/routers/games.py
git commit -m "test: cover match detail API contract"
```

Do not stage the user's unrelated working-tree changes.
