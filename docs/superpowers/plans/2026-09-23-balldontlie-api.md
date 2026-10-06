# BALLDONTLIE Free-Tier Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the teams, basic player profiles, and games ingestion paths with a rate-limited BALLDONTLIE free-tier integration while preserving the existing database-backed FastAPI contract.

**Architecture:** An asynchronous provider client owns authentication, pagination, retries, and process-wide request pacing. Pure normalizers translate provider dictionaries into typed application records, repositories idempotently persist those records with provider-specific identifiers, and the existing synchronization functions orchestrate the flow without exposing BALLDONTLIE to request traffic.

**Tech Stack:** Python 3.13, FastAPI, httpx, SQLAlchemy 2, Alembic, PostgreSQL, pytest, pytest-asyncio, Docker Compose

**Spec:** `docs/superpowers/specs/2026-09-23-balldontlie-api-design.md`

## Global Constraints

- Use only the free BALLDONTLIE teams, players, and games endpoints.
- Never exceed five requests per minute intentionally; default request spacing is exactly 12 seconds.
- Send the API key only through the `Authorization` request header and never log it.
- Keep public `/teams`, `/players`, and `/games` routes database-backed.
- Preserve existing official NBA identifiers and unrelated database records.
- Do not require a real API key or network connection in automated tests.
- Preserve the user's existing uncommitted changes in `backend/app/scheduler.py` and `backend/tests/test_scheduler.py`.

## Review Focus

- A second cursor page that repeats the prior cursor must fail instead of looping forever; Task 1 adds a repeated-cursor test.
- A malformed non-empty games response must not reset all `is_today` flags; Task 5 adds a transaction-order test.
- An existing player with the same name on another team must not be merged; Task 4 tests the name-and-team fallback together.
- A live response with one missing or negative score must preserve the stored score pair; Task 4 retains and adapts the incomplete-score regression test.
- A missing API key must leave persisted data unchanged and must not leak the secret in logs or errors; Tasks 1 and 5 test configuration failure before repository calls.

---

### Task 1: Configuration and Rate-Limited Provider Transport

**Files:**
- Create: `backend/app/services/clients/balldontlie.py`
- Create: `backend/tests/test_balldontlie_client.py`
- Modify: `backend/app/config.py`

**Interfaces:**
- Consumes: existing `httpx>=0.28,<0.29` dependency and Pydantic settings.
- Produces: `BallDontLieClient`, `RequestLimiter`, `BallDontLieError`, `BallDontLieConfigurationError`, `BallDontLieAuthenticationError`, `BallDontLieRateLimitError`, and async methods `get_teams()`, `get_players()`, `get_games(**filters)` returning `list[dict[str, Any]]`.

- [ ] **Step 1: Write failing configuration and authentication tests**

```python
def test_client_rejects_missing_api_key() -> None:
    with pytest.raises(BallDontLieConfigurationError, match="API key"):
        BallDontLieClient(api_key="", base_url="https://example.test/v1")


@pytest.mark.asyncio
async def test_teams_request_uses_authorization_header() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "secret-key"
        return httpx.Response(200, json={"data": []})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = BallDontLieClient(
            api_key="secret-key",
            base_url="https://example.test/v1",
            http_client=http_client,
            limiter=RequestLimiter(0),
        )
        assert await client.get_teams() == []
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `uv run pytest backend/tests/test_balldontlie_client.py -v`

Expected: collection fails because `app.services.clients.balldontlie` does not exist.

- [ ] **Step 3: Add exact BALLDONTLIE settings**

Add to `Settings` in `backend/app/config.py`:

```python
balldontlie_api_key: str = ""
balldontlie_base_url: str = "https://api.balldontlie.io/v1"
balldontlie_request_interval_seconds: float = 12.0
```

- [ ] **Step 4: Implement the minimal client and error hierarchy**

Create the transport with these signatures:

```python
class BallDontLieError(RuntimeError):
    pass


class BallDontLieConfigurationError(BallDontLieError):
    pass


class BallDontLieAuthenticationError(BallDontLieError):
    pass


class BallDontLieRateLimitError(BallDontLieError):
    pass


class RequestLimiter:
    def __init__(
        self,
        interval_seconds: float,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.interval_seconds = max(0.0, interval_seconds)
        self._clock = clock
        self._sleep = sleep
        self._last_request_at: float | None = None
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        async with self._lock:
            now = self._clock()
            if self._last_request_at is not None:
                delay = self.interval_seconds - (now - self._last_request_at)
                if delay > 0:
                    await self._sleep(delay)
            self._last_request_at = self._clock()


class BallDontLieClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        http_client: httpx.AsyncClient | None = None,
        limiter: RequestLimiter | None = None,
    ) -> None:
        if not api_key.strip():
            raise BallDontLieConfigurationError("BALLDONTLIE API key is required")
        self._owns_http_client = http_client is None
        self._http = http_client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": api_key},
            timeout=30.0,
        )
        self._limiter = limiter or shared_limiter

    async def __aenter__(self) -> "BallDontLieClient":
        return self

    async def __aexit__(self, *_args: object) -> None:
        if self._owns_http_client:
            await self._http.aclose()

    async def get_teams(self) -> list[dict[str, Any]]:
        return await self._get_paginated("/teams")

    async def get_players(self) -> list[dict[str, Any]]:
        return await self._get_paginated("/players")

    async def get_games(
        self,
        *,
        dates: Sequence[str] = (),
        seasons: Sequence[int] = (),
        season_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        params = [("dates[]", value) for value in dates]
        params += [("seasons[]", str(value)) for value in seasons]
        if season_type is not None:
            params.append(("season_type", season_type))
        if start_date is not None:
            params.append(("start_date", start_date))
        if end_date is not None:
            params.append(("end_date", end_date))
        return await self._get_paginated("/games", params)
```

Use an owned `httpx.AsyncClient` only when none is injected. Provide `async __aenter__` and `async __aexit__` so production callers close owned connections without closing injected test clients.

- [ ] **Step 5: Verify authentication tests are GREEN**

Run: `uv run pytest backend/tests/test_balldontlie_client.py -v`

Expected: the initial configuration and header tests pass.

- [ ] **Step 6: Add failing pagination, parameter, pacing, retry, and response-validation tests**

Add tests using `httpx.MockTransport` for these exact behaviors:

```python
@pytest.mark.asyncio
async def test_games_serializes_array_filters_and_follows_cursor() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(
                200,
                json={"data": [{"id": 1}], "meta": {"next_cursor": 99}},
            )
        return httpx.Response(200, json={"data": [{"id": 2}], "meta": {}})

    result = await make_client(handler).get_games(
        dates=["2026-09-23"],
        seasons=[2025],
    )

    assert result == [{"id": 1}, {"id": 2}]
    assert requests[0].url.params.get_list("dates[]") == ["2026-09-23"]
    assert requests[0].url.params.get_list("seasons[]") == ["2025"]
    assert requests[1].url.params["cursor"] == "99"


@pytest.mark.asyncio
async def test_repeated_cursor_is_rejected() -> None:
    client = make_client(
        lambda _request: httpx.Response(
            200,
            json={"data": [{"id": 1}], "meta": {"next_cursor": 99}},
        )
    )
    with pytest.raises(BallDontLieError, match="cursor"):
        await client.get_players()
```

Also add:

- a fake clock test proving request start times are `[0.0, 12.0, 24.0]`;
- a `429` then `200` test proving exactly one retry;
- a repeated `429` test raising `BallDontLieRateLimitError`;
- a `401` test raising `BallDontLieAuthenticationError`;
- parameterized malformed envelopes for missing/non-list `data` and non-object `meta`.

- [ ] **Step 7: Run new tests and verify RED for unimplemented behavior**

Run: `uv run pytest backend/tests/test_balldontlie_client.py -v`

Expected: pagination, pacing, retry, or validation assertions fail for the documented reason.

- [ ] **Step 8: Implement pagination, shared pacing, and bounded retry**

Use `per_page=100`, track every cursor in a `set`, and reject a repeated cursor. Before every attempt call the limiter. On the first `429`, parse `Retry-After` as a float, clamp it to `0..60`, sleep, then retry through the limiter. Never include the API key in exception text.

Production clients use one module-level limiter:

```python
shared_limiter = RequestLimiter(settings.balldontlie_request_interval_seconds)


def create_client() -> BallDontLieClient:
    return BallDontLieClient(
        api_key=settings.balldontlie_api_key,
        base_url=settings.balldontlie_base_url,
        limiter=shared_limiter,
    )
```

- [ ] **Step 9: Verify the client task**

Run: `uv run pytest backend/tests/test_balldontlie_client.py -v`

Expected: all tests pass with no real sleeps or network access.

- [ ] **Step 10: Commit the transport task**

```bash
git add backend/app/config.py backend/app/services/clients/balldontlie.py backend/tests/test_balldontlie_client.py
git commit -m "feat: add rate-limited balldontlie client"
```

### Task 2: Pure BALLDONTLIE Normalization

**Files:**
- Create: `backend/app/services/clients/balldontlie_normalizers.py`
- Create: `backend/tests/test_balldontlie_normalizers.py`
- Modify: `backend/app/services/clients/types.py`

**Interfaces:**
- Consumes: raw dictionaries returned by `BallDontLieClient`.
- Produces: `TeamProfileData`, `PlayerProfileData`, `GameData`, `normalize_teams(raw)`, `normalize_players(raw, valid_team_abbrs)`, `normalize_games(raw)`.

- [ ] **Step 1: Define failing team and player normalization tests**

```python
def test_normalize_team_profile() -> None:
    result = normalize_teams([{
        "id": 2,
        "abbreviation": "BOS",
        "city": "Boston",
        "name": "Celtics",
        "conference": "East",
    }])
    assert result == [{
        "balldontlie_id": 2,
        "abbr": "BOS",
        "city": "Boston",
        "name": "Celtics",
        "conference": "East",
    }]


def test_normalize_player_keeps_only_recognized_team() -> None:
    raw = [{
        "id": 115,
        "first_name": " Stephen ",
        "last_name": "Curry",
        "position": "G",
        "jersey_number": "30",
        "team": {"abbreviation": "GSW"},
    }]
    assert normalize_players(raw, {"GSW"}) == [{
        "balldontlie_id": 115,
        "name": "Stephen Curry",
        "team_abbr": "GSW",
        "position": "G",
        "jersey_number": "30",
    }]
    assert normalize_players(raw, {"BOS"}) == []
```

- [ ] **Step 2: Run focused tests and verify RED**

Run: `uv run pytest backend/tests/test_balldontlie_normalizers.py -v`

Expected: module import fails.

- [ ] **Step 3: Define typed records and implement team/player normalization**

Add exact `TypedDict` contracts:

```python
class TeamProfileData(TypedDict):
    balldontlie_id: int
    abbr: str
    city: str
    name: str
    conference: Literal["East", "West"]


class PlayerProfileData(TypedDict):
    balldontlie_id: int
    name: str
    team_abbr: str
    position: str
    jersey_number: str | None


class GameData(TypedDict):
    game_id: str
    away_abbr: str
    home_abbr: str
    date: str
    start_time: str
    status: Literal["scheduled", "live", "final"]
    status_text: str
    period: int | None
    clock: str | None
    away_score: int | None
    home_score: int | None
    venue: str
    season: str
    season_type: Literal["regular", "playoffs"]
```

Reject invalid IDs, abbreviations, names, conferences, or teams record-by-record. If a non-empty input yields no valid records, raise `ValueError` naming the record type.

- [ ] **Step 4: Verify team/player normalization is GREEN**

Run: `uv run pytest backend/tests/test_balldontlie_normalizers.py -v`

Expected: team/player tests pass.

- [ ] **Step 5: Add failing scheduled, live, final, unsupported-state, and invalid-score game tests**

Use one base fixture with visitor `BOS`, home `LAL`, `season=2025`, and `datetime="2026-01-05T23:00:00.000Z"`. Assert:

```python
assert normalize_games([scheduled])[0] == {
    "game_id": "bdl:15907925",
    "away_abbr": "BOS",
    "home_abbr": "LAL",
    "date": "2026-01-05",
    "start_time": "2026-01-05T23:00:00.000Z",
    "status": "scheduled",
    "status_text": "7:00 pm ET",
    "period": None,
    "clock": None,
    "away_score": None,
    "home_score": None,
    "venue": "",
    "season": "2025-26",
    "season_type": "regular",
}
```

Assert `in_progress` maps to `live`, `final` maps to `final`, `postseason=true` maps to `playoffs`, unsupported lifecycle states are skipped when another valid game exists, and a wholly invalid non-empty list raises `ValueError`. Parameterize `None` and `-1` for either live/final score and require rejection.

- [ ] **Step 6: Run game normalization tests and verify RED**

Run: `uv run pytest backend/tests/test_balldontlie_normalizers.py -v`

Expected: game mapping tests fail because `normalize_games` is absent or incomplete.

- [ ] **Step 7: Implement game normalization**

Use `status_state` as the only lifecycle classifier:

```python
STATUS_MAP = {
    "scheduled": "scheduled",
    "in_progress": "live",
    "final": "final",
}


def season_label(start_year: int) -> str:
    return f"{start_year}-{str(start_year + 1)[-2:]}"
```

For live/final games require both scores to be non-negative integers. For scheduled games force both scores to `None`. Normalize blank period/time fields to `None` and preserve the provider's human-readable `status` as `status_text`.

- [ ] **Step 8: Verify and commit normalization**

Run: `uv run pytest backend/tests/test_balldontlie_normalizers.py -v`

Expected: all normalization tests pass.

```bash
git add backend/app/services/clients/types.py backend/app/services/clients/balldontlie_normalizers.py backend/tests/test_balldontlie_normalizers.py
git commit -m "feat: normalize balldontlie nba data"
```

### Task 3: Provider Identifier Migration and Public Schemas

**Files:**
- Create: `backend/alembic/versions/20260923_add_balldontlie_ids.py`
- Modify: `backend/app/models/team.py`
- Modify: `backend/app/models/player.py`
- Modify: `backend/app/schemas/player.py`
- Create: `backend/tests/test_balldontlie_models.py`
- Modify: `backend/tests/test_games_api.py`
- Modify: `backend/tests/test_teams_api.py`

**Interfaces:**
- Consumes: `balldontlie_id` integers from normalized profiles.
- Produces: nullable unique `Team.balldontlie_id`, nullable unique `Player.balldontlie_id`, nullable `Player.nba_id`, and player API fields `nbaId: int | null`, `balldontlieId: int | null`.

- [ ] **Step 1: Write failing model metadata and schema tests**

```python
def test_provider_ids_are_separate_from_official_nba_ids() -> None:
    team = Team(
        abbr="BOS",
        nba_id=1610612738,
        balldontlie_id=2,
        name="Celtics",
        city="Boston",
        record="0-0",
    )
    player = Player(
        nba_id=None,
        balldontlie_id=115,
        name="Stephen Curry",
        team_abbr="GSW",
        position="G",
    )
    assert team.nba_id == 1610612738
    assert team.balldontlie_id == 2
    assert PlayerSchema.model_validate(player).model_dump(by_alias=True)["nbaId"] is None
    assert PlayerSchema.model_validate(player).model_dump(by_alias=True)["balldontlieId"] == 115
```

Add assertions that both model columns are unique and nullable and that `players.nba_id` is nullable in SQLAlchemy metadata.

- [ ] **Step 2: Run model tests and verify RED**

Run: `uv run pytest backend/tests/test_balldontlie_models.py -v`

Expected: constructors or schema validation reject unknown/missing fields.

- [ ] **Step 3: Add model and schema fields**

Use:

```python
balldontlie_id: Mapped[int | None] = mapped_column(
    Integer,
    unique=True,
    nullable=True,
)
```

Change `Player.nba_id` and both player schema declarations to `int | None`. Add `balldontlie_id: int | None = None` to `PlayerSchema` and `PlayerDetailSchema`. Do not remove compatibility statistics fields.

- [ ] **Step 4: Create the reversible Alembic migration**

Set `revision = "20260923_balldontlie_ids"` and `down_revision = "20260922_game_start_time"`. Upgrade actions:

```python
op.add_column("teams", sa.Column("balldontlie_id", sa.Integer(), nullable=True))
op.create_unique_constraint(
    "uq_teams_balldontlie_id",
    "teams",
    ["balldontlie_id"],
)
op.add_column("players", sa.Column("balldontlie_id", sa.Integer(), nullable=True))
op.create_unique_constraint(
    "uq_players_balldontlie_id",
    "players",
    ["balldontlie_id"],
)
op.alter_column(
    "players",
    "nba_id",
    existing_type=sa.Integer(),
    nullable=True,
)
```

Downgrade drops the constraints/columns and restores `players.nba_id` to non-null only when every row already has an official ID. Use this exact precondition before altering the column; do not invent or delete identifiers:

```python
connection = op.get_bind()
missing_official_id = connection.execute(
    sa.text("SELECT 1 FROM players WHERE nba_id IS NULL LIMIT 1")
).first()
if missing_official_id is not None:
    raise RuntimeError(
        "Cannot downgrade while players without official NBA IDs exist"
    )
```

- [ ] **Step 5: Update existing API fixtures for explicit provider defaults**

Where tests instantiate `Team` or `Player`, pass `balldontlie_id=None` only if SQLAlchemy construction needs it. Update exact player response expectations to include `balldontlieId`; team and game response shapes remain unchanged.

- [ ] **Step 6: Verify models, API contracts, and migration graph**

Run: `uv run pytest backend/tests/test_balldontlie_models.py backend/tests/test_games_api.py backend/tests/test_teams_api.py -v`

Run: `cd backend && ../.venv/bin/alembic heads`

Expected: tests pass and the only head is `20260923_balldontlie_ids`.

- [ ] **Step 7: Commit persistence schema changes**

```bash
git add backend/alembic/versions/20260923_add_balldontlie_ids.py backend/app/models/team.py backend/app/models/player.py backend/app/schemas/player.py backend/tests/test_balldontlie_models.py backend/tests/test_games_api.py backend/tests/test_teams_api.py
git commit -m "feat: store balldontlie provider identifiers"
```

### Task 4: Idempotent Team, Player, and Game Repositories

**Files:**
- Modify: `backend/app/services/repositories/teams.py`
- Modify: `backend/app/services/repositories/players.py`
- Modify: `backend/app/services/repositories/games.py`
- Create: `backend/tests/test_balldontlie_repositories.py`
- Modify: `backend/tests/test_live_sync.py`

**Interfaces:**
- Consumes: `TeamProfileData`, `PlayerProfileData`, and `GameData` from Task 2.
- Produces: `upsert_teams(db, profiles) -> int`, `upsert_players(db, profiles) -> tuple[int, int]`, and `upsert_games(db, games, *, today: str | None = None) -> list[str]`. Repository functions flush/update data but do not commit; synchronization owns transaction boundaries.

- [ ] **Step 1: Write failing team preservation test**

Create a fake session returning an existing `Team` and assert:

```python
count = await teams_repo.upsert_teams(session, [{
    "balldontlie_id": 2,
    "abbr": "BOS",
    "city": "Boston",
    "name": "Celtics",
    "conference": "East",
}])

assert count == 0
assert team.nba_id == 1610612738
assert team.balldontlie_id == 2
assert team.record == "52-20"
assert team.last_ten == "8-2"
```

Also test a new team receives `record="0-0"` and null standings-only fields.

- [ ] **Step 2: Verify team tests are RED, then implement and verify GREEN**

Run: `uv run pytest backend/tests/test_balldontlie_repositories.py -k team -v`

Expected before implementation: signature/data-key failure. Implement abbreviation lookup, update only provider-owned fields, remove repository commits, rerun and expect PASS.

- [ ] **Step 3: Write failing player idempotency and safe fallback tests**

Cover three cases:

```python
# Exact provider ID updates the same row without touching stats or nba_id.
assert existing.pts == 29.4
assert existing.nba_id == 201939

# First provider sync may attach to one exact normalized name + team match.
assert matched.balldontlie_id == 115

# Same name on a different team inserts a new row instead of merging.
assert session.added[0].team_abbr == "BOS"
```

New rows use `nba_id=None`, real name/team/position/jersey, and zero/default compatibility statistics.

- [ ] **Step 4: Verify player tests are RED, implement, then verify GREEN**

Run: `uv run pytest backend/tests/test_balldontlie_repositories.py -k player -v`

Expected before implementation: old header/row interface fails. Replace it with typed profile upserts and rerun for PASS.

- [ ] **Step 5: Adapt the existing game repository tests to `GameData`**

Change fixture game IDs to `bdl:15907925`, add `season` and `season_type`, and replace separate live/schedule/historical upsert calls with:

```python
affected = await games_repo.upsert_games(
    session,
    [LIVE_GAME],
    today="2026-09-23",
)
```

Keep the regression assertion that an incomplete score pair never erases stored scores. Add assertions that scheduled games clear no final scores, final games reconcile partial scores, provider season fields update, and `is_today` is set only when `today` matches.

- [ ] **Step 6: Run game tests and verify RED**

Run: `uv run pytest backend/tests/test_live_sync.py backend/tests/test_balldontlie_repositories.py -k game -v`

Expected: `upsert_games` does not exist.

- [ ] **Step 7: Implement one normalized game upsert path**

Use `select(Game).where(Game.id == game_id)` for idempotency. For inserts map all normalized fields. For updates always refresh teams, date, status text, lifecycle, period, clock, start time, season, and season type; update scores only when both normalized scores are not `None`. When `today` is supplied set `is_today = (date == today)`; otherwise preserve it for existing rows and default new rows to `False`.

Delete obsolete NBA-CDN-specific parsing from `upsert_schedule_games` and row-pair logic from `upsert_historical_games`; all three flows will use `upsert_games`.

- [ ] **Step 8: Verify and commit repository changes**

Run: `uv run pytest backend/tests/test_balldontlie_repositories.py backend/tests/test_live_sync.py -v`

Expected: repository and adapted game regressions pass.

```bash
git add backend/app/services/repositories/teams.py backend/app/services/repositories/players.py backend/app/services/repositories/games.py backend/tests/test_balldontlie_repositories.py backend/tests/test_live_sync.py
git commit -m "feat: persist normalized balldontlie data"
```

### Task 5: BALLDONTLIE Synchronization Flows

**Files:**
- Modify: `backend/app/services/sync.py`
- Modify: `backend/tests/test_live_sync.py`
- Modify: `backend/tests/test_sync_cache.py`
- Create: `backend/tests/test_balldontlie_sync.py`

**Interfaces:**
- Consumes: `create_client`, normalizers, and repository interfaces from Tasks 1, 2, and 4.
- Produces: existing public service functions `sync_teams`, `sync_players`, `sync_games`, `sync_schedule`, and `sync_historical_games`, now fully asynchronous and backed by BALLDONTLIE free endpoints.

- [ ] **Step 1: Write failing teams and players orchestration tests**

Monkeypatch `sync_module.create_balldontlie_client` with an async context manager fake. Assert:

```python
await sync_module.sync_teams(db)
client.get_teams.assert_awaited_once_with()
teams_repo.upsert_teams.assert_awaited_once_with(db, normalized_teams)
db.commit.assert_awaited_once_with()
invalidate_teams_cache.assert_awaited_once_with()
```

For players, make the fake client return one valid and one teamless profile. Make the fake DB return known team abbreviations and assert only the recognized profile reaches `players_repo.upsert_players`.

- [ ] **Step 2: Run teams/players sync tests and verify RED**

Run: `uv run pytest backend/tests/test_balldontlie_sync.py -k 'teams or players' -v`

Expected: old `nba_client` calls occur or the new factory is missing.

- [ ] **Step 3: Implement teams and players syncs**

Use:

```python
async with create_balldontlie_client() as client:
    raw = await client.get_teams()
profiles = normalize_teams(raw)
count_new = await teams_repo.upsert_teams(db, profiles)
await db.commit()
```

For players, query `select(Team.abbr)` first, normalize with that abbreviation set, upsert, and commit. Catch `BallDontLieError`, log only its safe message, roll back, and return without cache invalidation.

- [ ] **Step 4: Verify teams/players sync tests are GREEN**

Run: `uv run pytest backend/tests/test_balldontlie_sync.py -k 'teams or players' -v`

Expected: tests pass.

- [ ] **Step 5: Write failing current-day game safety tests**

Test exact filter and order:

```python
await sync_module.sync_games(db, today=date(2026, 9, 23))
client.get_games.assert_awaited_once_with(dates=["2026-09-23"])
assert reset_today.await_count == 1
upsert_games.assert_awaited_once_with(
    db,
    normalized_games,
    today="2026-09-23",
)
```

Add a malformed non-empty response test where `normalize_games` raises. Assert `reset_today`, `upsert_games`, `commit`, and cache invalidation are never called. Add missing-key/provider-error tests with the same no-write assertions.

- [ ] **Step 6: Run live-game sync tests and verify RED**

Run: `uv run pytest backend/tests/test_balldontlie_sync.py -k games -v`

Expected: old synchronous scoreboard/box-score flow fails the assertions.

- [ ] **Step 7: Implement current-day games without box-score calls**

Allow an optional date parameter for deterministic tests:

```python
async def sync_games(
    db: AsyncSession,
    *,
    today: date | None = None,
) -> None:
    sync_date = today or datetime.now(timezone.utc).date()
```

Fetch and normalize before `reset_today_flag`. After a valid empty response, reset, commit, and invalidate the empty live cache. After valid games, upsert, commit, and invalidate live and Elo caches. Remove player box-score calls because the endpoint is paid.

- [ ] **Step 8: Add failing schedule and historical filter tests**

Assert schedule calls:

```python
client.get_games.assert_awaited_once_with(
    start_date="2026-09-23",
    end_date="2026-10-23",
)
```

Assert `sync_historical_games(db, season="2025-26")` makes exactly:

```python
call(seasons=[2025], season_type="regular")
call(seasons=[2025], season_type="playoffs")
```

and rejects malformed labels such as `2025`, `25-26`, or `2025-28` before a client call.

- [ ] **Step 9: Implement schedule and historical flows**

Add a strict helper:

```python
def season_start_year(season: str) -> int:
    match = re.fullmatch(r"(\d{4})-(\d{2})", season)
    if match is None:
        raise ValueError(f"Invalid NBA season: {season}")
    start = int(match.group(1))
    if int(match.group(2)) != (start + 1) % 100:
        raise ValueError(f"Invalid NBA season: {season}")
    return start
```

The schedule accepts an injectable start date and computes a 30-day inclusive end. Historical sync combines both normalized result lists, calls `upsert_games` once, commits once, and invalidates Elo once.

- [ ] **Step 10: Verify synchronization and existing cache behavior**

Run: `uv run pytest backend/tests/test_balldontlie_sync.py backend/tests/test_live_sync.py backend/tests/test_sync_cache.py -v`

Expected: all tests pass; no test references `nba_client` for teams, players, schedules, or games.

- [ ] **Step 11: Commit synchronization changes**

```bash
git add backend/app/services/sync.py backend/tests/test_balldontlie_sync.py backend/tests/test_live_sync.py backend/tests/test_sync_cache.py
git commit -m "feat: sync free nba data from balldontlie"
```

### Task 6: Deployment Configuration and Documentation

**Files:**
- Modify: `.env.example`
- Modify: `compose.yaml`
- Modify: `compose.prod.yaml`
- Modify: `README.md`
- Modify: `backend/app/services/clients/__init__.py`
- Modify: `backend/scripts/backfill_positions.py`

**Interfaces:**
- Consumes: `BALLDONTLIE_API_KEY` from deployment secrets.
- Produces: documented local/production configuration and accurate operational instructions.

- [ ] **Step 1: Add the environment variable to all backend processes**

Replace the unused template entry with:

```dotenv
BALLDONTLIE_API_KEY=
```

Add this mapping to every API, scheduler, and seed/migration service that invokes application sync code:

```yaml
BALLDONTLIE_API_KEY: ${BALLDONTLIE_API_KEY:-}
```

Do not place an actual key in Compose or `.env.example`.

- [ ] **Step 2: Update operational documentation**

Document:

- account/key creation through BALLDONTLIE;
- free endpoint scope: teams, player profiles, games;
- five requests per minute and expected multi-minute player/history imports;
- unsupported free-tier fields remain null, zero, preserved, or sourced separately as described in the design;
- `BALLDONTLIE_API_KEY` is required for seed and scheduler syncs;
- existing route URLs do not change.

Update `backend/scripts/backfill_positions.py` comments so they no longer claim `sync_players` uses `LeagueDashPlayerStats`. Update the clients package docstring to name BALLDONTLIE and ESPN accurately.

- [ ] **Step 3: Check configuration references**

Run: `rg -n "NBA_API_KEY|BALLDONTLIE_API_KEY|nba_api_key|balldontlie_api_key" .env.example compose.yaml compose.prod.yaml README.md backend/app backend/scripts`

Expected: no runtime configuration claims `NBA_API_KEY` is used; every required container receives `BALLDONTLIE_API_KEY`; the secret value is absent.

- [ ] **Step 4: Run formatting/static checks available in the repository**

Run: `uv run ruff check backend`

If `ruff` is unavailable in the locked environment, record that fact and run `python -m compileall -q backend/app backend/scripts` instead. Fix only issues introduced by this branch.

- [ ] **Step 5: Run the complete backend suite**

Run: `uv run pytest`

Expected: all tests pass. Report any pre-existing failure by exact test name; do not omit it.

- [ ] **Step 6: Run the frontend production build**

Run: `npm run build`

Working directory: `frontend`

Expected: TypeScript compilation and Vite build exit successfully.

- [ ] **Step 7: Inspect final diff for scope and secrets**

Run:

```bash
git diff --check
git status --short
git diff --stat main...HEAD
git diff main...HEAD -- . ':!docs/superpowers'
```

Confirm no API key, unrelated refactor, generated frontend output, `.env`, or user-owned scheduler change is included.

- [ ] **Step 8: Commit documentation and configuration**

```bash
git add .env.example compose.yaml compose.prod.yaml README.md backend/app/services/clients/__init__.py backend/scripts/backfill_positions.py
git commit -m "docs: configure balldontlie data sync"
```

### Task 7: Final Verification and Branch Review

**Files:**
- Review only: every file changed by Tasks 1-6

**Interfaces:**
- Consumes: completed implementation and all automated checks.
- Produces: verified `balldontile-api` branch ready for user review.

- [ ] **Step 1: Run fresh backend verification**

Run: `uv run pytest`

Expected: zero failures.

- [ ] **Step 2: Run fresh migration and frontend verification**

Run: `cd backend && ../.venv/bin/alembic heads`

Expected: one head, `20260923_balldontlie_ids`.

Run: `npm run build`

Working directory: `frontend`

Expected: exit code 0.

- [ ] **Step 3: Review requirement coverage**

Confirm from code and tests:

- teams use `/teams`;
- profiles use `/players` and expose name/team/position;
- live, scheduled, and historical games use `/games`;
- all pagination uses one 12-second process-wide pacer;
- unsupported paid endpoints are absent;
- database-backed routes remain unchanged;
- official identifiers and unavailable stored statistics are preserved;
- user-owned scheduler changes are not part of implementation commits.

- [ ] **Step 4: Run final secret and diff checks**

Run: `git diff --check main...HEAD`

Run: `git grep -n "BALLDONTLIE_API_KEY=" -- ':!*.example' ':!docs/**'`

Expected: clean whitespace check and no committed key assignment.

- [ ] **Step 5: Report branch status with evidence**

Report the exact test count, migration head, frontend build result, commits created, configuration required, and any limitations from the free tier. Do not claim success unless the fresh commands in Steps 1, 2, and 4 passed.
