# Dynamic Live Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace every hard-coded dashboard value with durable HoopStats data, synchronized and refreshed every five minutes.

**Architecture:** The scheduler normalizes NBA scoreboard and box-score responses, stores durable state in PostgreSQL, and invalidates short-lived Redis API caches after commits. The React dashboard reads only HoopStats endpoints through one polling hook, preserves stale data during partial failures, and renders truthful empty states when live data is unavailable.

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy async, Alembic, PostgreSQL 17, Redis 7.4, APScheduler, React 19, TypeScript 6, Vite 8, Vitest, React Testing Library, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-09-21-dynamic-live-dashboard-design.md`

## Global Constraints

- Live synchronization defaults to exactly five minutes through `LIVE_SYNC_MINUTES=5`.
- Dashboard polling defaults to exactly 300,000 milliseconds through `VITE_DASHBOARD_REFRESH_MS=300000`.
- Browsers call only HoopStats endpoints; no browser-to-NBA fallback is permitted.
- Redis is an optimization: read or write failures must fall back to PostgreSQL or preserve a successful database response.
- Existing upcoming-game consumers remain compatible; new live fields are optional outside `/games/today`.
- Do not backfill old-season player box scores in this feature.
- Run only one scheduler container.

## Review Focus

- A malformed or partial upstream game/player entry is skipped and logged without aborting valid entries; covered in Task 2 parsing tests.
- Resetting `is_today` does not remove the last durable scores for a game that crosses midnight; covered in Task 3 repository tests.
- A Redis outage still returns database data with HTTP 200; covered in Task 4 cache-failure tests.
- Days with no games or missing box scores return empty collections rather than errors or sample data; covered in Tasks 4 and 8.
- A partial frontend refresh failure keeps prior successful data and cleans up the five-minute timer on unmount; covered in Task 7 hook tests.

---

### Task 1: Persist Live Game, Standing, and Player Box-Score State

**Files:**
- Create: `backend/app/models/player_game_stat.py`
- Create: `backend/alembic/versions/20260921_live_dashboard_add_live_dashboard_data.py`
- Create: `backend/tests/test_live_models.py`
- Modify: `backend/app/models/game.py`
- Modify: `backend/app/models/team.py`
- Modify: `backend/app/models/__init__.py`

**Interfaces:**
- Produces: `Game.status`, `Game.status_text`, `Game.period`, `Game.clock`.
- Produces: `Team.conference`, `Team.conference_rank`, `Team.last_ten`, `Team.streak`.
- Produces: `PlayerGameStat(game_id, nba_id, name, team_abbr, points, rebounds, assists, steals, blocks, minutes, updated_at)`.

- [ ] **Step 1: Write failing model-contract tests**

```python
# backend/tests/test_live_models.py
from sqlalchemy import UniqueConstraint

from app.models.game import Game
from app.models.player_game_stat import PlayerGameStat
from app.models.team import Team


def test_game_exposes_live_state_columns() -> None:
    assert {"status", "status_text", "period", "clock"} <= set(Game.__table__.columns.keys())


def test_team_exposes_standing_columns() -> None:
    assert {"conference", "conference_rank", "last_ten", "streak"} <= set(Team.__table__.columns.keys())


def test_player_game_stat_is_unique_per_game_and_player() -> None:
    constraints = [
        c for c in PlayerGameStat.__table__.constraints
        if isinstance(c, UniqueConstraint)
    ]
    assert any({column.name for column in c.columns} == {"game_id", "nba_id"} for c in constraints)
```

- [ ] **Step 2: Run the tests and confirm the missing model fails collection**

Run: `.venv/bin/pytest backend/tests/test_live_models.py -q`

Expected: FAIL because `app.models.player_game_stat` and the new columns do not exist.

- [ ] **Step 3: Add the SQLAlchemy fields and player-game model**

```python
# backend/app/models/player_game_stat.py
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class PlayerGameStat(Base):
    __tablename__ = "player_game_stats"
    __table_args__ = (UniqueConstraint("game_id", "nba_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[str] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True)
    nba_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(100))
    team_abbr: Mapped[str] = mapped_column(String(5), index=True)
    points: Mapped[int] = mapped_column(Integer, default=0)
    rebounds: Mapped[int] = mapped_column(Integer, default=0)
    assists: Mapped[int] = mapped_column(Integer, default=0)
    steals: Mapped[int] = mapped_column(Integer, default=0)
    blocks: Mapped[int] = mapped_column(Integer, default=0)
    minutes: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

Add nullable standing fields to `Team`, add live fields with `status="scheduled"` to `Game`, and export `PlayerGameStat` from `backend/app/models/__init__.py`.

- [ ] **Step 4: Generate and edit the migration**

Run: `docker compose -p hoopstats-dev --env-file .env exec backend alembic revision --autogenerate --rev-id 20260921_live_dashboard -m "add live dashboard data"`

Ensure the migration adds every field above, creates `player_game_stats`, sets existing scored games to `final`, and leaves unscored games as `scheduled`:

```python
op.execute("UPDATE games SET status = 'final' WHERE score1 IS NOT NULL")
```

- [ ] **Step 5: Run model tests and apply the migration**

Run: `.venv/bin/pytest backend/tests/test_live_models.py -q`

Expected: 3 passed.

Run: `docker compose -p hoopstats-dev --env-file .env exec backend alembic upgrade head`

Expected: migration completes without an error.

- [ ] **Step 6: Commit the durable model**

```bash
git add backend/app/models backend/alembic/versions backend/tests/test_live_models.py
git commit -m "feat: persist live dashboard data"
```

### Task 2: Normalize NBA Scoreboard, Standings, and Box Scores

**Files:**
- Create: `backend/app/services/clients/types.py`
- Create: `backend/tests/fixtures/live_scoreboard.json`
- Create: `backend/tests/fixtures/live_boxscore.json`
- Create: `backend/tests/test_nba_live_client.py`
- Modify: `backend/app/services/clients/nba.py`

**Interfaces:**
- Produces: `LiveGameData` and `LivePlayerStatData` typed dictionaries.
- Produces: `fetch_live_scoreboard() -> list[LiveGameData]`.
- Produces: `fetch_live_boxscore(game_id: str) -> list[LivePlayerStatData]`.
- Produces: `fetch_standings(season: str) -> dict[int, StandingData]`.

- [ ] **Step 1: Add minimal raw-response fixtures and failing normalization tests**

Fixtures must contain one scheduled game, one live game, one malformed entry, and two box-score players. Test the normalized public contract:

```python
def test_parse_scoreboard_skips_invalid_games_and_normalizes_live_state() -> None:
    games = nba_client.parse_live_scoreboard(load_fixture("live_scoreboard.json"))
    assert games[1] == {
        "game_id": "0022500002",
        "away_abbr": "BOS",
        "home_abbr": "LAL",
        "date": "2026-09-21",
        "status": "live",
        "status_text": "Q3 04:12",
        "period": 3,
        "clock": "PT04M12.00S",
        "away_score": 78,
        "home_score": 74,
        "venue": "Crypto.com Arena",
    }
    assert len(games) == 2


def test_parse_boxscore_returns_both_teams_players() -> None:
    players = nba_client.parse_live_boxscore(load_fixture("live_boxscore.json"))
    assert players[0]["game_id"] == "0022500002"
    assert players[0]["nba_id"] == 2544
    assert players[0]["points"] == 22
    assert players[0]["rebounds"] == 7
    assert players[0]["assists"] == 8
```

- [ ] **Step 2: Run tests and confirm parser functions are missing**

Run: `.venv/bin/pytest backend/tests/test_nba_live_client.py -q`

Expected: FAIL with missing `parse_live_scoreboard` and `parse_live_boxscore`.

- [ ] **Step 3: Define normalized types and pure parsers**

```python
# backend/app/services/clients/types.py
class LiveGameData(TypedDict):
    game_id: str
    away_abbr: str
    home_abbr: str
    date: str
    status: Literal["scheduled", "live", "final"]
    status_text: str
    period: int | None
    clock: str | None
    away_score: int | None
    home_score: int | None
    venue: str


class LivePlayerStatData(TypedDict):
    game_id: str
    nba_id: int
    name: str
    team_abbr: str
    points: int
    rebounds: int
    assists: int
    steals: int
    blocks: int
    minutes: float
```

Map NBA `gameStatus` values `1`, `2`, and `3` to `scheduled`, `live`, and `final`. Parse ISO-8601 minutes defensively and skip entries without game IDs or team abbreviations.

- [ ] **Step 4: Wrap the upstream endpoints behind normalized functions**

Use `scoreboard.ScoreBoard(...).get_dict()` and `boxscore.BoxScore(game_id=game_id, headers=NBA_HEADERS).get_dict()`. Both wrappers return parser output rather than raw NBA structures.

Update standings normalization to return:

```python
StandingData(
    record=f"{wins}-{losses}",
    conference="East" if conference.lower().startswith("east") else "West",
    conference_rank=int(row.get("PlayoffRank") or 0),
    last_ten=str(row.get("L10") or ""),
    streak=str(row.get("strCurrentStreak") or ""),
)
```

- [ ] **Step 5: Run client tests**

Run: `.venv/bin/pytest backend/tests/test_nba_live_client.py -q`

Expected: all client parsing tests pass without network access.

- [ ] **Step 6: Commit normalized upstream clients**

```bash
git add backend/app/services/clients backend/tests/fixtures backend/tests/test_nba_live_client.py
git commit -m "feat: normalize NBA live dashboard data"
```

### Task 3: Upsert Live Games, Standings, and Player Statistics

**Files:**
- Create: `backend/app/services/repositories/player_game_stats.py`
- Create: `backend/tests/test_live_sync.py`
- Modify: `backend/app/services/repositories/games.py`
- Modify: `backend/app/services/repositories/teams.py`
- Modify: `backend/app/services/repositories/__init__.py`
- Modify: `backend/app/services/sync.py`

**Interfaces:**
- Consumes: `LiveGameData`, `LivePlayerStatData`, and `StandingData` from Task 2.
- Produces: `upsert_live_games(db, games) -> list[str]` returning affected game IDs.
- Produces: `upsert_player_game_stats(db, game_id, rows) -> int`.
- Produces: `sync_games(db) -> None` that isolates individual box-score failures.

- [ ] **Step 1: Write failing repository tests**

Test these exact behaviors with fake async sessions or the repository test pattern already used in the project:

```python
async def test_live_game_updates_scores_before_final() -> None:
    game = existing_game(status="scheduled", score1=None, score2=None)
    await upsert_live_games(session_for(game), [live_payload(away_score=78, home_score=74)])
    assert (game.status, game.score1, game.score2, game.period) == ("live", 78, 74, 3)


async def test_reset_today_flag_preserves_scores_and_status() -> None:
    game = existing_game(is_today=True, status="final", score1=110, score2=105)
    await reset_today_flag(session_for(game))
    assert (game.score1, game.score2, game.status) == (110, 105, "final")


async def test_player_stats_upsert_does_not_duplicate_player() -> None:
    await upsert_player_game_stats(db, GAME_ID, [player_payload(points=20)])
    await upsert_player_game_stats(db, GAME_ID, [player_payload(points=24)])
    assert await count_rows(db, GAME_ID) == 1
    assert await player_points(db, GAME_ID, NBA_ID) == 24
```

- [ ] **Step 2: Run repository tests and confirm live updates fail**

Run: `.venv/bin/pytest backend/tests/test_live_sync.py -q`

Expected: FAIL because live scores and player-stat upserts are not implemented.

- [ ] **Step 3: Implement repository upserts**

Update every mutable game field for all three statuses, not only final games:

```python
game.status = payload["status"]
game.status_text = payload["status_text"]
game.period = payload["period"]
game.clock = payload["clock"]
game.score1 = payload["away_score"]
game.score2 = payload["home_score"]
game.is_today = True
```

Use PostgreSQL `insert(PlayerGameStat).on_conflict_do_update(...)` keyed by `game_id` and `nba_id` for player rows. Update the team repository to persist every field in `StandingData`.

- [ ] **Step 4: Make `sync_games` fetch box scores per eligible game**

```python
affected_ids = await games_repo.upsert_live_games(db, games_data)
for game in games_data:
    if game["status"] not in {"live", "final"}:
        continue
    try:
        players = await asyncio.to_thread(nba_client.fetch_live_boxscore, game["game_id"])
        await player_stats_repo.upsert_player_game_stats(db, game["game_id"], players)
    except Exception:
        logger.exception("Box score sync failed for game %s", game["game_id"])
await db.commit()
await invalidate_live_caches(affected_ids)
```

Keep the last durable state when the scoreboard request itself fails.

- [ ] **Step 5: Run sync and existing repository tests**

Run: `.venv/bin/pytest backend/tests/test_live_sync.py backend/tests/test_injuries_repository.py -q`

Expected: all selected tests pass.

- [ ] **Step 6: Commit synchronization behavior**

```bash
git add backend/app/services backend/tests/test_live_sync.py
git commit -m "feat: synchronize live games and box scores"
```

### Task 4: Expose Redis-Cached Live Game APIs

**Files:**
- Create: `backend/app/schemas/player_game_stat.py`
- Create: `backend/tests/test_live_games_api.py`
- Modify: `backend/app/cache.py`
- Modify: `backend/app/config.py`
- Modify: `backend/app/routers/games.py`
- Modify: `backend/app/schemas/game.py`
- Modify: `backend/app/schemas/__init__.py`
- Modify: `.env.example`

**Interfaces:**
- Consumes: durable entities from Tasks 1 and 3.
- Produces: `LiveGameSchema`, `GameDetailSchema`, and `PlayerGameStatSchema`.
- Produces: `GET /games/today` and `GET /games/{id}/boxscore`.
- Produces: safe JSON cache helpers `get_cached_json`, `set_cached_json`, and `invalidate_live_caches`.

- [ ] **Step 1: Write failing API and cache-fallback tests**

```python
async def test_today_returns_live_state() -> None:
    response = await client.get("/games/today")
    assert response.json()[0] | {
        "status": "live",
        "statusText": "Q3 04:12",
        "period": 3,
        "clock": "PT04M12.00S",
        "score1": 78,
        "score2": 74,
    } == response.json()[0]


async def test_boxscore_returns_empty_list_when_no_rows_exist() -> None:
    response = await client.get("/games/0022500002/boxscore")
    assert response.status_code == 200
    assert response.json() == []


async def test_today_falls_back_to_database_when_redis_get_fails() -> None:
    app.state.redis = FailingRedis()
    response = await client.get("/games/today")
    assert response.status_code == 200
    assert response.json()[0]["status"] == "live"
```

- [ ] **Step 2: Run the API tests and verify missing schema/route failures**

Run: `.venv/bin/pytest backend/tests/test_live_games_api.py -q`

Expected: FAIL because live fields, box-score route, and fail-open caching are missing.

- [ ] **Step 3: Add response schemas**

```python
class LiveGameSchema(GameBase):
    is_today: bool
    status: Literal["scheduled", "live", "final"]
    status_text: str
    period: int | None = None
    clock: str | None = None
    score1: int | None = None
    score2: int | None = None
    win1: float | None = None
    prediction: str | None = None


class PlayerGameStatSchema(CamelModel):
    nba_id: int
    name: str
    team_abbr: str
    points: int
    rebounds: int
    assists: int
    steals: int
    blocks: int
    minutes: float
```

- [ ] **Step 4: Implement safe cache helpers**

Use keys `api:games:today:v1` and `api:game:{game_id}:boxscore:v1`, default TTL `300`, and catch `RedisError` on get, set, and delete. `get_cached_json` returns `None` when Redis is unavailable or JSON is corrupt.

- [ ] **Step 5: Implement routes from PostgreSQL with cache-aside behavior**

Place `/today` and `/{id}/boxscore` before `/{id}`. Validate that the game exists before returning an empty box score. Order player rows by `points DESC`, then `name ASC`. Extend `/{id}` to return optional live fields without removing existing fields.

- [ ] **Step 6: Run API and full backend tests**

Run: `.venv/bin/pytest backend/tests/test_live_games_api.py -q`

Expected: all live API tests pass.

Run: `.venv/bin/pytest -q`

Expected: the complete backend suite passes.

- [ ] **Step 7: Commit API contracts and caching**

```bash
git add backend/app/cache.py backend/app/config.py backend/app/routers/games.py backend/app/schemas backend/tests/test_live_games_api.py .env.example
git commit -m "feat: expose cached live game APIs"
```

### Task 5: Configure Five-Minute Live Synchronization

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/scheduler.py`
- Modify: `backend/tests/test_scheduler.py`
- Modify: `.env.example`
- Modify: `compose.yaml`
- Modify: `compose.prod.yaml`

**Interfaces:**
- Produces: `settings.live_sync_minutes: int = 5`.
- Produces: scheduler job `live-games` with a five-minute interval.

- [ ] **Step 1: Change the scheduler test first**

```python
def test_live_job_runs_every_five_minutes() -> None:
    scheduler = AsyncIOScheduler(timezone="UTC")
    configure_scheduler(scheduler, now=NOW)
    job = scheduler.get_job("live-games")
    assert job is not None
    assert job.trigger.interval == timedelta(minutes=5)
```

- [ ] **Step 2: Run the scheduler test and observe the 15-minute failure**

Run: `.venv/bin/pytest backend/tests/test_scheduler.py::test_live_job_runs_every_five_minutes -q`

Expected: FAIL because the current interval is 15 minutes.

- [ ] **Step 3: Make the interval configurable**

```python
# config.py
live_sync_minutes: int = 5

# scheduler.py
IntervalTrigger(minutes=settings.live_sync_minutes)
```

Expose `LIVE_SYNC_MINUTES=${LIVE_SYNC_MINUTES:-5}` to the scheduler in both Compose files and document `LIVE_SYNC_MINUTES=5` in `.env.example`.

- [ ] **Step 4: Run scheduler and Compose validation**

Run: `.venv/bin/pytest backend/tests/test_scheduler.py -q`

Expected: scheduler tests pass.

Run: `docker compose -p hoopstats-dev --env-file .env config --quiet`

Expected: exit code 0.

- [ ] **Step 5: Commit five-minute configuration**

```bash
git add backend/app/config.py backend/app/scheduler.py backend/tests/test_scheduler.py .env.example compose.yaml compose.prod.yaml
git commit -m "feat: refresh live data every five minutes"
```

### Task 6: Add Frontend Dashboard Types, Request Cache, and Tests

**Files:**
- Create: `frontend/src/lib/requestCache.ts`
- Create: `frontend/src/lib/requestCache.test.ts`
- Create: `frontend/src/test/setup.ts`
- Create: `frontend/vitest.config.ts`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Modify: `frontend/tsconfig.app.json`

**Interfaces:**
- Produces: `LiveGame`, `PlayerGameStat`, and standing fields on `Team`.
- Produces: `cachedRequest<T>(key, ttlMs, loader) -> Promise<T>`.
- Produces: `getTodayGames()` and `getBoxScore(gameId)`.

- [ ] **Step 1: Install test dependencies and add the test command**

Run: `npm install --save-dev vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event`

Add scripts:

```json
"test": "vitest run",
"test:watch": "vitest"
```

- [ ] **Step 2: Write failing request-cache tests**

```typescript
it("reuses one in-flight request for the same key", async () => {
  const loader = vi.fn().mockResolvedValue(["BOS"]);
  const first = cachedRequest("teams", 30_000, loader);
  const second = cachedRequest("teams", 30_000, loader);
  expect(first).toBe(second);
  await first;
  expect(loader).toHaveBeenCalledTimes(1);
});

it("removes a rejected request so the next call retries", async () => {
  const loader = vi.fn()
    .mockRejectedValueOnce(new Error("offline"))
    .mockResolvedValueOnce(["BOS"]);
  await expect(cachedRequest("teams", 30_000, loader)).rejects.toThrow("offline");
  await expect(cachedRequest("teams", 30_000, loader)).resolves.toEqual(["BOS"]);
});
```

- [ ] **Step 3: Run the cache tests and confirm the missing module failure**

Run: `npm test -- src/lib/requestCache.test.ts`

Expected: FAIL because `requestCache.ts` does not exist.

- [ ] **Step 4: Implement the request cache and API types**

```typescript
const entries = new Map<string, { expiresAt: number; promise: Promise<unknown> }>();

export function cachedRequest<T>(key: string, ttlMs: number, loader: () => Promise<T>): Promise<T> {
  const cached = entries.get(key);
  if (cached && cached.expiresAt > Date.now()) return cached.promise as Promise<T>;
  const promise = loader().catch((error) => {
    entries.delete(key);
    throw error;
  });
  entries.set(key, { expiresAt: Date.now() + ttlMs, promise });
  return promise;
}
```

Define `LiveGame` with optional scores plus required live status fields, define `PlayerGameStat`, add team standing fields, and use `cachedRequest` in team, upcoming, today, leader, and box-score API functions.

- [ ] **Step 5: Run frontend unit tests and TypeScript build**

Run: `npm test -- src/lib/requestCache.test.ts`

Expected: request-cache tests pass.

Run: `npm run build`

Expected: TypeScript and Vite build pass.

- [ ] **Step 6: Commit frontend data contracts**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vitest.config.ts frontend/tsconfig.app.json frontend/src/test frontend/src/types frontend/src/lib
git commit -m "test: add dashboard frontend data layer"
```

### Task 7: Build the Five-Minute Dashboard Data Hook

**Files:**
- Create: `frontend/src/hooks/useDashboard.ts`
- Create: `frontend/src/hooks/useDashboard.test.tsx`

**Interfaces:**
- Consumes: cached API functions from Task 6.
- Produces: `useDashboard()` with teams, upcoming, today, leaders, featuredGame, boxScore, initialLoading, refreshing, errors, and lastUpdated.

- [ ] **Step 1: Write hook tests with fake timers and mocked API functions**

```tsx
it("loads immediately and refreshes after five minutes", async () => {
  vi.useFakeTimers();
  const { result } = renderHook(() => useDashboard());
  await act(async () => vi.runOnlyPendingTimersAsync());
  expect(getTodayGames).toHaveBeenCalledTimes(1);
  await act(async () => vi.advanceTimersByTimeAsync(300_000));
  expect(getTodayGames).toHaveBeenCalledTimes(2);
});

it("keeps previous teams when only the teams refresh fails", async () => {
  mockFirstSuccessfulRefresh();
  const { result } = renderHook(() => useDashboard());
  await waitFor(() => expect(result.current.teams.BOS).toBeDefined());
  getTeams.mockRejectedValueOnce(new Error("offline"));
  await act(async () => result.current.refresh());
  expect(result.current.teams.BOS).toBeDefined();
  expect(result.current.errors.teams).toBe("offline");
});

it("clears the refresh timer when unmounted", () => {
  const clearIntervalSpy = vi.spyOn(window, "clearInterval");
  const { unmount } = renderHook(() => useDashboard());
  unmount();
  expect(clearIntervalSpy).toHaveBeenCalled();
});
```

- [ ] **Step 2: Run hook tests and confirm the hook is missing**

Run: `npm test -- src/hooks/useDashboard.test.tsx`

Expected: FAIL because `useDashboard` does not exist.

- [ ] **Step 3: Implement selection and refresh behavior**

Use `Promise.allSettled` so each successful resource updates independently. Keep prior state for rejected resources. Select the featured game in this order: live, scheduled today, upcoming, most recent final today. Fetch its box score only when its status is live or final. Use `Number(import.meta.env.VITE_DASHBOARD_REFRESH_MS ?? 300_000)` for the interval.

Return a stable `refresh` callback so tests and a future manual-refresh button can invoke the same flow.

- [ ] **Step 4: Run hook tests**

Run: `npm test -- src/hooks/useDashboard.test.tsx`

Expected: all hook tests pass, including partial failure and cleanup.

- [ ] **Step 5: Commit dashboard state management**

```bash
git add frontend/src/hooks/useDashboard.ts frontend/src/hooks/useDashboard.test.tsx
git commit -m "feat: add resilient dashboard data hook"
```

### Task 8: Replace Static Dashboard Widgets

**Files:**
- Create: `frontend/src/components/dashboard/DashboardWidgets.test.tsx`
- Modify: `frontend/src/components/dashboard/UpcomingGamesWidget.tsx`
- Modify: `frontend/src/components/dashboard/FeaturedGameWidget.tsx`
- Modify: `frontend/src/components/dashboard/TopPlayerWidget.tsx`
- Modify: `frontend/src/components/dashboard/StandingsWidget.tsx`
- Modify: `frontend/src/components/dashboard/TeamEfficiencyChart.tsx`
- Modify: `frontend/src/components/dashboard/LiveGameStatsWidget.tsx`

**Interfaces:**
- Consumes: typed dashboard data from Tasks 6 and 7.
- Produces: pure widgets with data and callback props; no widget performs its own fetch.

- [ ] **Step 1: Write failing widget behavior tests**

```tsx
it("featured scheduled game never displays a fake score", () => {
  render(<FeaturedGameWidget game={scheduledGame} team1={bos} team2={lal} onOpen={vi.fn()} />);
  expect(screen.getByText("7:30 PM ET")).toBeInTheDocument();
  expect(screen.queryByText("112 - 108")).not.toBeInTheDocument();
});

it("featured live game displays current score and clock", () => {
  render(<FeaturedGameWidget game={liveGame} team1={bos} team2={lal} onOpen={vi.fn()} />);
  expect(screen.getByText("78 - 74")).toBeInTheDocument();
  expect(screen.getByText(/Q3/)).toBeInTheDocument();
});

it("live stats renders a truthful empty state", () => {
  render(<LiveGameStatsWidget game={null} players={[]} />);
  expect(screen.getByText("No live box score available")).toBeInTheDocument();
});

it("preview invokes navigation with the game id", async () => {
  const onPreview = vi.fn();
  render(<UpcomingGamesWidget games={[scheduledGame]} teams={teams} onPreview={onPreview} />);
  await userEvent.click(screen.getByRole("button", { name: "Preview" }));
  expect(onPreview).toHaveBeenCalledWith(scheduledGame.id);
});
```

Add assertions for real top-player values, East/West standings filtering, and efficiency average calculated from `lastScores`.

- [ ] **Step 2: Run widget tests and confirm hard-coded behavior fails**

Run: `npm test -- src/components/dashboard/DashboardWidgets.test.tsx`

Expected: FAIL because current widgets have static content and missing props.

- [ ] **Step 3: Convert upcoming, featured, and top-player widgets**

Upcoming accepts `onPreview(gameId)`. Featured branches on `game.status`: live renders scores and clock; scheduled renders time, venue, and prediction; final renders the final score. Top Player accepts `Player | null`, uses `nbaId` for the headshot URL, and invokes `onOpen(player.id)`.

- [ ] **Step 4: Convert standings and efficiency widgets**

Standings derives `GP`, `W`, `L`, and percentage from `record`, sorts by `conferenceRank` then percentage, and exposes an accessible East/West toggle. Efficiency accepts teams, selected abbreviation, and `onSelect`; it renders `SparkLine` with reversed `lastScores` and computes the average from that same array.

- [ ] **Step 5: Convert live player stats widget**

Render up to six rows ordered by points, using `nbaId` in the NBA headshot URL. Display team, points, rebounds, and assists. Render `No live box score available` when either no selected game or no player rows exist.

- [ ] **Step 6: Run widget tests, lint, and build**

Run: `npm test -- src/components/dashboard/DashboardWidgets.test.tsx`

Expected: widget tests pass.

Run: `npm run lint`

Expected: no ESLint errors.

Run: `npm run build`

Expected: production build completes.

- [ ] **Step 7: Commit dynamic widgets**

```bash
git add frontend/src/components/dashboard
git commit -m "feat: replace static dashboard widgets"
```

### Task 9: Integrate Dashboard, Navigation, and Refresh Status

**Files:**
- Create: `frontend/src/pages/Dashboard.test.tsx`
- Modify: `frontend/src/pages/Dashboard.tsx`
- Modify: `.env.example`

**Interfaces:**
- Consumes: `useDashboard` and all pure widgets.
- Produces: complete dynamic dashboard route with working navigation and refresh status.

- [ ] **Step 1: Write failing page integration tests**

```tsx
it("navigates dashboard actions to existing routes", async () => {
  renderDashboardWithRouter(mockDashboardData);
  await userEvent.click(screen.getByRole("button", { name: "Preview" }));
  expect(screen.getByTestId("location")).toHaveTextContent("/match/0022500001");
  await userEvent.click(screen.getByRole("button", { name: "View Profile" }));
  expect(screen.getByTestId("location")).toHaveTextContent("/players/2544");
});

it("keeps widgets visible and shows a warning during refresh failure", () => {
  renderDashboard({ ...mockDashboardData, errors: { today: "offline" } });
  expect(screen.getByText("Upcoming Games")).toBeInTheDocument();
  expect(screen.getByText(/some data could not be refreshed/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the page tests and confirm integration is missing**

Run: `npm test -- src/pages/Dashboard.test.tsx`

Expected: FAIL because Dashboard still uses `useGames`, `useTeams`, and static widget signatures.

- [ ] **Step 3: Replace page-level data wiring**

Use `useDashboard`, route actions through `useNavigate`, keep existing responsive grid structure, display `Last updated` and `Updating…`, and pass resource-specific errors or empty values into widgets. Add `VITE_DASHBOARD_REFRESH_MS=300000` to the frontend environment example used by the project.

- [ ] **Step 4: Run complete frontend verification**

Run: `npm test`

Expected: all frontend tests pass.

Run: `npm run lint`

Expected: no ESLint errors.

Run: `npm run build`

Expected: Vite production build completes.

- [ ] **Step 5: Commit dashboard integration**

```bash
git add frontend/src/pages/Dashboard.tsx frontend/src/pages/Dashboard.test.tsx .env.example
git commit -m "feat: integrate dynamic live dashboard"
```

### Task 10: Full-System Verification and Local Runtime Smoke Test

**Files:**
- Modify only files required by failures discovered during verification.

**Interfaces:**
- Consumes: all previous tasks.
- Produces: migrated, running, test-verified local system.

- [ ] **Step 1: Run clean static verification**

Run: `git diff --check`

Expected: no whitespace errors.

Run: `.venv/bin/pytest -q`

Expected: complete backend suite passes.

Run from `frontend`: `npm test`

Run from `frontend`: `npm run lint`

Run from `frontend`: `npm run build`

Expected: each command exits successfully.

- [ ] **Step 2: Validate both Compose configurations**

Run: `docker compose -p hoopstats-dev --env-file .env config --quiet`

Run: `docker compose -f compose.prod.yaml --env-file .env.example config --quiet`

Expected: both commands exit with code 0. If production requires deployment-only secrets, provide non-secret temporary values explicitly for validation rather than editing committed defaults.

- [ ] **Step 3: Rebuild and migrate local containers**

Run: `docker compose -p hoopstats-dev --env-file .env up -d --build backend frontend scheduler`

Expected: backend becomes healthy, frontend and scheduler become running, and Alembic reaches head.

- [ ] **Step 4: Smoke-test runtime APIs from inside the backend container**

Run a Python standard-library request for `/games/today`, `/games/upcoming`, `/analytics/leaders`, `/teams/`, and one existing `/games/{id}/boxscore`. Assert every response is HTTP 200 and that live objects contain `status`, `statusText`, `score1`, and `score2` keys. An empty today list or box-score list is valid when no NBA game is active.

- [ ] **Step 5: Verify Redis and scheduler behavior**

After one `/games/today` request, assert `EXISTS api:games:today:v1` returns `1` and its TTL is between `1` and `300`. Inspect scheduler logs and assert the next `live-games` run is scheduled five minutes after the previous run.

- [ ] **Step 6: Review the branch diff against the specification**

Confirm every success criterion in `docs/superpowers/specs/2026-09-21-dynamic-live-dashboard-design.md` has a corresponding implementation and verification result. Report any upstream API unavailability separately from application failures.
