# API-NBA Player Seasons MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Import API-NBA 2025-26 rosters and player statistics into PostgreSQL and let users select an imported season on the existing Players pages.

**Architecture:** Keep BALLDONTLIE as the team/game provider and add an isolated API-NBA adapter for player-season data. A manual atomic sync fetches one team directory plus roster and game-stat rows for each of 30 teams, aggregates one row per player and season, and exposes it through optional season filters on the existing player routes. The frontend reads imported player seasons from the backend and carries the selected season through list and detail navigation.

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy 2, Alembic, HTTPX, PostgreSQL, pytest, React 19, TypeScript, Vite, Vitest.

**Spec:** `docs/superpowers/specs/2026-09-25-api-nba-player-seasons-design.md`

## Global Constraints

- Use API-NBA from API-Sports at `https://v2.nba.api-sports.io`; do not use generic API-Basketball.
- Authenticate only with `x-apisports-key`, configured through `API_NBA_KEY`; never log or commit the key.
- Retain BALLDONTLIE for teams, games, schedules, and live scores.
- Import only explicitly requested seasons; the initial supported season is `2025-26`, represented as `2025` upstream.
- Keep the existing `/players/` and `/players/{player_id}` paths and preserve their behavior when `season` is omitted.
- A season refresh is atomic: no provider or validation failure may partially replace stored season data.
- Keep a full 30-team import at or below 61 API-NBA requests.
- Store provider identifiers separately from official NBA and BALLDONTLIE identifiers.

## Review Focus

- API-Sports may return HTTP 200 with a non-empty `errors` object; Task 1 tests and rejects it as a provider failure.
- The same player/game row can be encountered more than once; Task 1 deduplicates on `(api_nba_player_id, game_id)` before aggregation.
- Shooting attempts may be zero; Task 1 verifies percentages remain `0.0` without division errors.
- Traded players may have statistics for multiple teams; Task 1 verifies combined averages and deterministic primary-team selection.
- No player seasons may be imported yet; Task 5 verifies the Players page shows an actionable empty state without making an unscoped player request.

---

## File Structure

### New files

- `backend/app/services/clients/api_nba.py` — authenticated API-NBA transport and response-envelope validation.
- `backend/app/services/clients/api_nba_normalizers.py` — pure profile/stat normalization and season aggregation.
- `backend/app/models/player_season_stat.py` — persisted player-season aggregate.
- `backend/app/services/repositories/player_seasons.py` — atomic player/profile/season upserts and season listing.
- `backend/app/services/player_seasons.py` — orchestration of the 61-request import.
- `backend/scripts/seed_player_season.py` — manual one-season import command.
- `backend/alembic/versions/20260925_add_api_nba_player_seasons.py` — provider IDs and season table migration.
- `backend/tests/test_api_nba_client.py` — transport contract tests.
- `backend/tests/test_api_nba_normalizers.py` — aggregation tests.
- `backend/tests/test_api_nba_repositories.py` — persistence tests.
- `backend/tests/test_api_nba_sync.py` — orchestration and rollback tests.
- `frontend/src/hooks/usePlayerSeasons.ts` — imported-season loading state.
- `frontend/src/pages/Players.test.tsx` — season-selection behavior tests.

### Modified files

- `backend/app/config.py`, `.env.example`, `compose.yaml`, `compose.prod.yaml` — API-NBA configuration propagation.
- `backend/app/models/team.py`, `backend/app/models/player.py`, `backend/app/models/__init__.py` — provider IDs and season relationship.
- `backend/app/services/clients/types.py` — normalized API-NBA types.
- `backend/app/services/__init__.py`, `Makefile` — manual sync entry points.
- `backend/app/routers/players.py`, `backend/app/schemas/player.py`, `backend/tests/test_players_api.py` — season-aware API.
- `frontend/src/lib/api.ts`, `frontend/src/hooks/usePlayers.ts`, `frontend/src/hooks/usePlayerDetail.ts`, `frontend/src/pages/Players.tsx`, `frontend/src/pages/PlayerDetail.tsx`, `frontend/src/types/index.ts` — season selector and propagation.
- `README.md` — configuration and import instructions.

---

### Task 1: API-NBA Client and Pure Aggregation

**Files:**
- Create: `backend/app/services/clients/api_nba.py`
- Create: `backend/app/services/clients/api_nba_normalizers.py`
- Create: `backend/tests/test_api_nba_client.py`
- Create: `backend/tests/test_api_nba_normalizers.py`
- Modify: `backend/app/services/clients/types.py`
- Modify: `backend/app/config.py`

**Interfaces:**
- Consumes: `settings.api_nba_key: str`, `settings.api_nba_base_url: str`.
- Produces: `ApiNbaClient.get_teams()`, `get_players(team_id: int, season: int)`, `get_player_statistics(team_id: int, season: int)` returning validated `list[dict[str, Any]]`.
- Produces: `normalize_api_nba_teams(raw, valid_abbrs) -> list[ApiNbaTeamData]` and `aggregate_player_season(season, team_map, roster_pages, stat_pages) -> tuple[list[ApiNbaPlayerProfileData], list[PlayerSeasonData]]`.

- [ ] **Step 1: Add failing client tests**

Create tests using `httpx.MockTransport` that assert the exact header and query parameters and reject both HTTP errors and API-Sports' HTTP-200 error envelope:

```python
@pytest.mark.asyncio
async def test_players_request_uses_key_team_and_season() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-apisports-key"] == "secret"
        assert request.url.path == "/players"
        assert dict(request.url.params) == {"team": "10", "season": "2025"}
        return httpx.Response(200, json={"errors": [], "response": []})

    async with api_nba_client_for(handler) as client:
        assert await client.get_players(team_id=10, season=2025) == []


@pytest.mark.asyncio
async def test_http_200_provider_error_is_rejected() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"errors": {"requests": "Daily limit reached"}, "response": []},
        )

    async with api_nba_client_for(handler) as client:
        with pytest.raises(ApiNbaQuotaError, match="Daily limit"):
            await client.get_teams()
```

- [ ] **Step 2: Run client tests and verify RED**

Run: `uv run pytest backend/tests/test_api_nba_client.py -v`

Expected: collection fails because `app.services.clients.api_nba` does not exist.

- [ ] **Step 3: Implement configuration and client**

Add settings:

```python
api_nba_key: str = ""
api_nba_base_url: str = "https://v2.nba.api-sports.io"
```

Implement these public types and methods:

```python
class ApiNbaError(RuntimeError):
    """Base error safe to expose in synchronization logs."""


class ApiNbaConfigurationError(ApiNbaError):
    """Required API-NBA configuration is missing."""


class ApiNbaAuthenticationError(ApiNbaError):
    """API-NBA rejected the configured key."""


class ApiNbaQuotaError(ApiNbaError):
    """API-NBA rejected a request because its quota was exhausted."""

class ApiNbaClient:
    def __init__(self, *, api_key: str, base_url: str,
                 http_client: httpx.AsyncClient | None = None) -> None:
        if not api_key.strip():
            raise ApiNbaConfigurationError("API-NBA key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._owns_http_client = http_client is None
        self._http = http_client or httpx.AsyncClient(timeout=60.0)

    async def __aenter__(self) -> "ApiNbaClient":
        return self

    async def __aexit__(self, *_args: object) -> None:
        if self._owns_http_client:
            await self._http.aclose()

    async def _get(
        self,
        path: str,
        params: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        try:
            response = await self._http.get(
                f"{self._base_url}{path}",
                params=params,
                headers={"x-apisports-key": self._api_key},
            )
        except httpx.HTTPError as exc:
            raise ApiNbaError(
                f"API-NBA request failed: {type(exc).__name__}"
            ) from exc
        if response.status_code in {401, 403}:
            raise ApiNbaAuthenticationError("API-NBA rejected the configured key")
        if response.status_code == 429:
            raise ApiNbaQuotaError("API-NBA request quota is exhausted")
        if response.is_error:
            raise ApiNbaError(
                f"API-NBA request failed with HTTP status {response.status_code}"
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise ApiNbaError("Invalid API-NBA response: expected JSON") from exc
        if not isinstance(payload, dict):
            raise ApiNbaError("Invalid API-NBA response: expected an object")
        errors = payload.get("errors")
        if errors:
            message = str(errors)
            if any(word in message.lower() for word in ("limit", "quota", "request")):
                raise ApiNbaQuotaError(f"API-NBA quota error: {message}")
            raise ApiNbaError(f"API-NBA provider error: {message}")
        records = payload.get("response")
        if not isinstance(records, list) or not all(
            isinstance(record, dict) for record in records
        ):
            raise ApiNbaError("Invalid API-NBA response envelope")
        return records

    async def get_teams(self) -> list[dict[str, Any]]:
        return await self._get("/teams")

    async def get_players(self, *, team_id: int, season: int) -> list[dict[str, Any]]:
        return await self._get(
            "/players", {"team": str(team_id), "season": str(season)}
        )

    async def get_player_statistics(
        self, *, team_id: int, season: int
    ) -> list[dict[str, Any]]:
        return await self._get(
            "/players/statistics",
            {"team": str(team_id), "season": str(season)},
        )


def create_client() -> ApiNbaClient:
    return ApiNbaClient(
        api_key=settings.api_nba_key,
        base_url=settings.api_nba_base_url,
    )
```

`_get` must require a dict payload, require `response` to be a list, treat non-empty `errors` as an error, map 401/403 to authentication errors, and map 429 or an error message containing `limit`, `quota`, or `request` to `ApiNbaQuotaError`. Error messages must not contain the key.

- [ ] **Step 4: Run client tests and verify GREEN**

Run: `uv run pytest backend/tests/test_api_nba_client.py -v`

Expected: all tests pass.

- [ ] **Step 5: Add failing normalizer and aggregation tests**

Use representative API-NBA v2 fixtures. Pin the review-focus behaviors:

```python
RAW_PLAYER = {
    "id": 417,
    "firstname": "Stephen",
    "lastname": "Curry",
    "leagues": {"standard": {"jersey": 30, "active": True, "pos": "G"}},
}


def stat(game_id: int, team_id: int, *, attempts: bool = True) -> dict:
    return {
        "player": {"id": 417, "firstname": "Stephen", "lastname": "Curry"},
        "team": {"id": team_id},
        "game": {"id": game_id},
        "points": 20,
        "totReb": 4,
        "assists": 6,
        "steals": 1,
        "blocks": 0,
        "min": "30:00",
        "fgm": 5 if attempts else 0,
        "fga": 10 if attempts else 0,
        "tpm": 2 if attempts else 0,
        "tpa": 5 if attempts else 0,
        "ftm": 4 if attempts else 0,
        "fta": 5 if attempts else 0,
        "comment": None,
    }


atl_game_1 = stat(1001, 1)
atl_game_2 = stat(1002, 1)
bos_game = stat(1003, 2)
zero_attempt_game = stat(1004, 1, attempts=False)


def test_aggregate_combines_trade_stints_and_selects_primary_team() -> None:
    profiles, seasons = aggregate_player_season(
        "2025-26",
        {1: "ATL", 2: "BOS"},
        {1: [RAW_PLAYER], 2: [RAW_PLAYER]},
        {1: [atl_game_1, atl_game_2], 2: [bos_game]},
    )
    assert len(profiles) == 1
    assert seasons == [{
        "api_nba_id": 417,
        "season": "2025-26",
        "primary_team_abbr": "ATL",
        "games_played": 3,
        "pts": 20.0,
        "reb": 4.0,
        "ast": 6.0,
        "stl": 1.0,
        "blk": 0.0,
        "fg_pct": 0.5,
        "fg3_pct": 0.4,
        "ft_pct": 0.8,
        "mins": 30.0,
        "recent_games": 3,
    }]


def test_aggregate_deduplicates_player_game_and_handles_zero_attempts() -> None:
    duplicated = {1: [zero_attempt_game, zero_attempt_game]}
    _, seasons = aggregate_player_season(
        "2025-26", {1: "ATL"}, {1: [RAW_PLAYER]}, duplicated
    )
    assert seasons[0]["games_played"] == 1
    assert seasons[0]["fg_pct"] == 0.0
    assert seasons[0]["fg3_pct"] == 0.0
    assert seasons[0]["ft_pct"] == 0.0
```

Also test invalid team codes, missing positive player/game IDs, DNP rows with `min=None`, `MM:SS` minute parsing, and the strict `YYYY-YY` season conversion.

- [ ] **Step 6: Run normalizer tests and verify RED**

Run: `uv run pytest backend/tests/test_api_nba_normalizers.py -v`

Expected: collection fails because the normalizer module does not exist.

- [ ] **Step 7: Add normalized types and implement aggregation**

Add types with these exact fields:

```python
class ApiNbaTeamData(TypedDict):
    api_nba_id: int
    abbr: str

class ApiNbaPlayerProfileData(TypedDict):
    api_nba_id: int
    name: str
    position: str
    jersey_number: str | None

class PlayerSeasonData(TypedDict):
    api_nba_id: int
    season: str
    primary_team_abbr: str
    games_played: int
    pts: float
    reb: float
    ast: float
    stl: float
    blk: float
    fg_pct: float
    fg3_pct: float
    ft_pct: float
    mins: float
    recent_games: int
```

Implement `season_start_year()` with the same strict rollover validation used by game synchronization. Deduplicate stat rows by `(player_id, game_id)`, sum makes/attempts before calculating percentages, round per-game averages to one decimal and percentages to three decimals, and choose the primary team using `max(team_counts, key=lambda item: (item[1], item[0]))` with the code ordering made explicit in the test.

- [ ] **Step 8: Run Task 1 tests**

Run: `uv run pytest backend/tests/test_api_nba_client.py backend/tests/test_api_nba_normalizers.py -v`

Expected: all tests pass.

- [ ] **Step 9: Commit Task 1**

```bash
git add backend/app/config.py backend/app/services/clients/types.py backend/app/services/clients/api_nba.py backend/app/services/clients/api_nba_normalizers.py backend/tests/test_api_nba_client.py backend/tests/test_api_nba_normalizers.py
git commit -m "feat: add api-nba player data adapter"
```

---

### Task 2: Provider IDs, Season Model, and Repository

**Files:**
- Create: `backend/app/models/player_season_stat.py`
- Create: `backend/app/services/repositories/player_seasons.py`
- Create: `backend/alembic/versions/20260925_add_api_nba_player_seasons.py`
- Create: `backend/tests/test_api_nba_repositories.py`
- Modify: `backend/app/models/team.py`
- Modify: `backend/app/models/player.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/tests/conftest.py`
- Modify: `pyproject.toml`
- Modify: `uv.lock`

**Interfaces:**
- Consumes: `ApiNbaTeamData`, `ApiNbaPlayerProfileData`, and `PlayerSeasonData` from Task 1.
- Produces: `PlayerSeasonStat`, `upsert_player_season(db, *, season, teams, profiles, rows) -> tuple[int, int]`, and `list_player_seasons(db) -> list[str]`.

- [ ] **Step 1: Add the async repository-test fixture and failing tests**

Add `aiosqlite>=0.21,<1` to the dev dependency group, run `uv lock`, and add reusable fixtures to `backend/tests/conftest.py`:

```python
@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def players_client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    app = FastAPI()
    app.include_router(players.router)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
```

Import all model modules before `Base.metadata.create_all`. Test that models expose separate provider IDs, an existing `nba_id` or `balldontlie_id` is preserved, a repeated import updates rather than duplicates `(player_id, season)`, stale rows for the same imported season are removed, and another season remains untouched:

```python
API_PLAYER: ApiNbaPlayerProfileData = {
    "api_nba_id": 417,
    "name": "Stephen Curry",
    "position": "G",
    "jersey_number": "30",
}
UPDATED_2025_ROW: PlayerSeasonData = {
    "api_nba_id": 417,
    "season": "2025-26",
    "primary_team_abbr": "GSW",
    "games_played": 79,
    "pts": 25.4,
    "reb": 4.5,
    "ast": 6.1,
    "stl": 1.0,
    "blk": 0.4,
    "fg_pct": 0.47,
    "fg3_pct": 0.41,
    "ft_pct": 0.92,
    "mins": 33.2,
    "recent_games": 10,
}


@pytest.mark.asyncio
async def test_upsert_replaces_only_requested_season(db_session) -> None:
    team = Team(
        abbr="GSW", nba_id=1610612744, balldontlie_id=10,
        api_nba_id=None, name="Warriors", city="Golden State", record="0-0",
    )
    player = Player(
        nba_id=201939, balldontlie_id=115, api_nba_id=None,
        name="Stephen Curry", team_abbr="GSW", position="G",
        jersey_number="30", games_played=0, pts=0, reb=0, ast=0,
        stl=0, blk=0, fg_pct=0, fg3_pct=0, ft_pct=0, mins=0,
        recent_games=0,
    )
    db_session.add_all([team, player])
    await db_session.flush()
    db_session.add_all([
        PlayerSeasonStat(
            player_id=player.id, season="2024-25", primary_team_abbr="GSW",
            games_played=70, pts=24.0, reb=4.0, ast=6.0, stl=1.0,
            blk=0.4, fg_pct=0.45, fg3_pct=0.40, ft_pct=0.9,
            mins=32.0, recent_games=10,
        ),
        PlayerSeasonStat(
            player_id=player.id, season="2025-26", primary_team_abbr="GSW",
            games_played=1, pts=1.0, reb=1.0, ast=1.0, stl=0.0,
            blk=0.0, fg_pct=0.1, fg3_pct=0.1, ft_pct=0.1,
            mins=1.0, recent_games=1,
        ),
    ])
    await db_session.commit()

    inserted, updated = await upsert_player_season(
        db_session,
        season="2025-26",
        teams=[{"api_nba_id": 10, "abbr": "GSW"}],
        profiles=[API_PLAYER],
        rows=[UPDATED_2025_ROW],
    )
    await db_session.commit()
    assert (inserted, updated) == (0, 1)
    seasons = (
        await db_session.execute(
            select(PlayerSeasonStat).order_by(PlayerSeasonStat.season)
        )
    ).scalars().all()
    assert [row.season for row in seasons] == ["2024-25", "2025-26"]
    assert seasons[1].pts == 25.4
    await db_session.refresh(player)
    assert player.nba_id == 201939
    assert player.balldontlie_id == 115
```

- [ ] **Step 2: Run repository tests and verify RED**

Run: `uv run pytest backend/tests/test_api_nba_repositories.py -v`

Expected: collection fails because the model and repository do not exist.

- [ ] **Step 3: Implement the SQLAlchemy model**

Create a model with an explicit uniqueness constraint and indexed season:

```python
class PlayerSeasonStat(Base):
    __tablename__ = "player_season_stats"
    __table_args__ = (
        UniqueConstraint("player_id", "season", name="uq_player_season_stats_player_season"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), index=True
    )
    season: Mapped[str] = mapped_column(String(7), index=True)
    primary_team_abbr: Mapped[str] = mapped_column(ForeignKey("teams.abbr"), index=True)
    games_played: Mapped[int] = mapped_column(Integer)
    pts: Mapped[float] = mapped_column(Float)
    reb: Mapped[float] = mapped_column(Float)
    ast: Mapped[float] = mapped_column(Float)
    stl: Mapped[float] = mapped_column(Float)
    blk: Mapped[float] = mapped_column(Float)
    fg_pct: Mapped[float] = mapped_column(Float)
    fg3_pct: Mapped[float] = mapped_column(Float)
    ft_pct: Mapped[float] = mapped_column(Float)
    mins: Mapped[float] = mapped_column(Float)
    recent_games: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

Add nullable unique `api_nba_id` columns to `Team` and `Player`, plus a `Player.season_stats` relationship with cascade delete-orphan.

- [ ] **Step 4: Implement the migration**

Create revision `20260925_api_nba_player_seasons` with `down_revision = "20260923_balldontlie_ids"`. Add both provider-ID columns and unique constraints, then create the table and indexes matching the model. Downgrade drops the table before its provider-ID columns.

- [ ] **Step 5: Implement repository replacement**

`upsert_player_season` must:

1. Validate that every `primary_team_abbr` exists in the normalized team list.
2. Update matching teams' `api_nba_id` without changing BALLDONTLIE or official IDs.
3. Match players by `api_nba_id`, then by one exact normalized-name match when provider ID is absent.
4. Create missing players with nullable official/BALLDONTLIE IDs and the season's primary team.
5. Require every row's season to equal the explicit `season` argument, then delete existing `PlayerSeasonStat` rows only for that season after all inputs have been validated and mapped.
6. Insert the complete replacement rows without committing.

`list_player_seasons` uses `select(PlayerSeasonStat.season).distinct().order_by(PlayerSeasonStat.season.desc())`.

- [ ] **Step 6: Run repository and migration metadata tests**

Run: `uv run pytest backend/tests/test_api_nba_repositories.py backend/tests/test_balldontlie_models.py -v`

Expected: all tests pass.

- [ ] **Step 7: Verify a single Alembic head**

Run: `cd backend && ../.venv/bin/alembic heads`

Expected: exactly `20260925_api_nba_player_seasons (head)`.

- [ ] **Step 8: Commit Task 2**

```bash
git add pyproject.toml uv.lock backend/tests/conftest.py backend/app/models backend/app/services/repositories/player_seasons.py backend/alembic/versions/20260925_add_api_nba_player_seasons.py backend/tests/test_api_nba_repositories.py
git commit -m "feat: persist api-nba player seasons"
```

---

### Task 3: Atomic Season Sync and Manual Operations

**Files:**
- Create: `backend/app/services/player_seasons.py`
- Create: `backend/scripts/seed_player_season.py`
- Create: `backend/tests/test_api_nba_sync.py`
- Modify: `backend/app/services/__init__.py`
- Modify: `.env.example`
- Modify: `compose.yaml`
- Modify: `compose.prod.yaml`
- Modify: `Makefile`
- Modify: `README.md`

**Interfaces:**
- Consumes: Task 1 client/normalizers and Task 2 repository.
- Produces: `sync_player_season(db: AsyncSession, season: str) -> tuple[int, int]` and `python -m scripts.seed_player_season --season 2025-26`.

- [ ] **Step 1: Add failing synchronization tests**

Use an injected fake client and 30 generated team records. Verify 61 total calls, exact season conversion, one repository call, one commit, and zero writes when team 17 fails:

```python
NORMALIZED_30_TEAMS = [
    {"api_nba_id": index, "abbr": f"T{index:02d}"}
    for index in range(1, 31)
]
RAW_30_TEAMS = [
    {"id": team["api_nba_id"], "code": team["abbr"], "nbaFranchise": True}
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
        if team_id == self.fail_team:
            raise ApiNbaError("provider unavailable")
        return [{"id": team_id * 100, "firstname": "Test", "lastname": str(team_id)}]

    async def _stats(self, *, team_id: int, season: int) -> list[dict]:
        return []


@pytest.mark.asyncio
async def test_sync_player_season_fetches_each_team_and_commits_once(monkeypatch) -> None:
    client = FakeApiNbaClient(teams=RAW_30_TEAMS)
    db = FakeSession()
    upsert = AsyncMock(return_value=(450, 450))
    monkeypatch.setattr(player_seasons, "create_api_nba_client", lambda: client)
    monkeypatch.setattr(
        player_seasons,
        "normalize_api_nba_teams",
        lambda raw, valid: NORMALIZED_30_TEAMS,
    )
    monkeypatch.setattr(
        player_seasons,
        "aggregate_player_season",
        lambda *args: ([], []),
    )
    monkeypatch.setattr(player_seasons.player_seasons_repo, "upsert_player_season", upsert)

    result = await player_seasons.sync_player_season(db, "2025-26")

    assert result == (450, 450)
    assert client.get_teams.await_count == 1
    assert client.get_players.await_count == 30
    assert client.get_player_statistics.await_count == 30
    db.commit.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_provider_failure_rolls_back_without_repository_write(monkeypatch) -> None:
    client = FakeApiNbaClient(teams=RAW_30_TEAMS, fail_team=17)
    db = FakeSession()
    upsert = AsyncMock()
    monkeypatch.setattr(player_seasons, "create_api_nba_client", lambda: client)
    monkeypatch.setattr(
        player_seasons,
        "normalize_api_nba_teams",
        lambda raw, valid: NORMALIZED_30_TEAMS,
    )
    monkeypatch.setattr(player_seasons.player_seasons_repo, "upsert_player_season", upsert)

    with pytest.raises(ApiNbaError):
        await player_seasons.sync_player_season(db, "2025-26")

    upsert.assert_not_awaited()
    db.commit.assert_not_awaited()
    db.rollback.assert_awaited_once_with()
```

- [ ] **Step 2: Run sync tests and verify RED**

Run: `uv run pytest backend/tests/test_api_nba_sync.py -v`

Expected: collection fails because the orchestration module does not exist.

- [ ] **Step 3: Implement orchestration**

Implement this control flow without database writes until all provider calls normalize successfully:

```python
async def sync_player_season(db: AsyncSession, season: str) -> tuple[int, int]:
    start_year = season_start_year(season)
    try:
        valid_abbrs = set((await db.execute(select(Team.abbr))).scalars().all())
        async with create_api_nba_client() as client:
            teams = normalize_api_nba_teams(await client.get_teams(), valid_abbrs)
            if len(teams) != 30:
                raise ValueError(f"Expected 30 NBA teams, received {len(teams)}")
            roster_pages: dict[int, list[dict[str, Any]]] = {}
            stat_pages: dict[int, list[dict[str, Any]]] = {}
            for team in teams:
                team_id = team["api_nba_id"]
                roster_pages[team_id] = await client.get_players(
                    team_id=team_id, season=start_year
                )
                stat_pages[team_id] = await client.get_player_statistics(
                    team_id=team_id, season=start_year
                )
        profiles, rows = aggregate_player_season(
            season,
            {team["api_nba_id"]: team["abbr"] for team in teams},
            roster_pages,
            stat_pages,
        )
        result = await player_seasons_repo.upsert_player_season(
            db, season=season, teams=teams, profiles=profiles, rows=rows
        )
        await db.commit()
        return result
    except (ApiNbaError, ValueError):
        await db.rollback()
        raise
```

- [ ] **Step 4: Add the manual command and configuration**

The script parses a required strict season and returns a non-zero process exit on provider/configuration failure:

```python
async def main(season: str) -> None:
    async with SessionLocal() as db:
        players, rows = await sync_player_season(db, season)
    print(f"Imported {players} players and {rows} season rows for {season}")
```

Add:

```make
seed-players:
	$(COMPOSE) exec backend python -m scripts.seed_player_season --season $(SEASON)
```

Add `API_NBA_KEY=` to `.env.example` and pass it to backend/scheduler/migrate services in both Compose files. Document account setup, the 100 requests/day quota, `make seed-players SEASON=2025-26`, and that historical imports are manual.

- [ ] **Step 5: Run Task 3 tests and configuration validation**

Run: `uv run pytest backend/tests/test_api_nba_sync.py backend/tests/test_api_nba_client.py backend/tests/test_api_nba_normalizers.py -v`

Expected: all tests pass.

Run: `docker compose --env-file .env.example -f compose.yaml config -q`

Expected: exit 0.

Run: `APP_HOST=stats.example.com docker compose --env-file .env.example -f compose.prod.yaml config -q`

Expected: exit 0.

- [ ] **Step 6: Commit Task 3**

```bash
git add backend/app/services/player_seasons.py backend/app/services/__init__.py backend/scripts/seed_player_season.py backend/tests/test_api_nba_sync.py .env.example compose.yaml compose.prod.yaml Makefile README.md
git commit -m "feat: sync api-nba player seasons"
```

---

### Task 4: Season-aware Player API

**Files:**
- Modify: `backend/app/routers/players.py`
- Modify: `backend/app/schemas/player.py`
- Modify: `backend/tests/test_players_api.py`

**Interfaces:**
- Consumes: `PlayerSeasonStat` and `list_player_seasons` from Task 2.
- Produces: `GET /players/seasons`, optional `season` on `GET /players/`, and optional `season` on `GET /players/{player_id}`.

- [ ] **Step 1: Add failing API tests**

Use a real test database session or focused fake results to verify:

```python
async def insert_player_seasons(
    db_session: AsyncSession, seasons: list[str]
) -> Player:
    db_session.add(Team(
        abbr="GSW", nba_id=1610612744, balldontlie_id=10, api_nba_id=10,
        name="Warriors", city="Golden State", record="0-0",
    ))
    player = Player(
        nba_id=None, balldontlie_id=115, api_nba_id=417,
        name="Stephen Curry", team_abbr="GSW", position="G",
        jersey_number="30", games_played=0, pts=0, reb=0, ast=0,
        stl=0, blk=0, fg_pct=0, fg3_pct=0, ft_pct=0, mins=0,
        recent_games=0,
    )
    db_session.add(player)
    await db_session.flush()
    db_session.add_all([
        PlayerSeasonStat(
            player_id=player.id, season=season, primary_team_abbr="GSW",
            games_played=79, pts=26.4, reb=4.5, ast=6.1, stl=1.0,
            blk=0.4, fg_pct=0.47, fg3_pct=0.41, ft_pct=0.92,
            mins=33.2, recent_games=10,
        )
        for season in seasons
    ])
    await db_session.commit()
    return player


@pytest.mark.asyncio
async def test_player_list_uses_selected_season_stats(
    players_client, db_session
) -> None:
    await insert_player_seasons(db_session, ["2025-26"])

    response = await players_client.get(
        "/players/?season=2025-26&sort_by=pts&min_games=10"
    )
    assert response.status_code == 200
    assert response.json()[0] == {
        "id": 1,
        "nbaId": None,
        "balldontlieId": 115,
        "apiNbaId": 417,
        "season": "2025-26",
        "name": "Stephen Curry",
        "teamAbbr": "GSW",
        "position": "G",
        "jerseyNumber": "30",
        "gamesPlayed": 79,
        "pts": 26.4,
        "reb": 4.5,
        "ast": 6.1,
        "stl": 1.0,
        "blk": 0.4,
        "fgPct": 0.47,
        "fg3Pct": 0.41,
        "ftPct": 0.92,
        "mins": 33.2,
        "recentGames": 10,
    }


@pytest.mark.asyncio
async def test_unknown_imported_season_returns_empty_list(players_client) -> None:
    response = await players_client.get("/players/?season=1990-91")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_player_seasons_are_reverse_chronological(
    players_client, db_session
) -> None:
    # Insert one player with two PlayerSeasonStat rows as in the list test.
    await insert_player_seasons(db_session, ["2024-25", "2025-26"])
    response = await players_client.get("/players/seasons")
    assert response.json() == ["2025-26", "2024-25"]
```

Retain the existing detail test without `season` to pin backward compatibility. Add invalid-season tests expecting HTTP 422.

- [ ] **Step 2: Run API tests and verify RED**

Run: `uv run pytest backend/tests/test_players_api.py -v`

Expected: new tests fail because season-aware fields and routes do not exist.

- [ ] **Step 3: Extend schemas**

Add to both player schemas:

```python
api_nba_id: int | None = None
season: str | None = None
```

Keep `nba_id` nullable and all existing camel-case response behavior.

- [ ] **Step 4: Implement season-aware routes**

Declare `/seasons` before `/{player_id}`. Validate `season` with `pattern=r"^\d{4}-\d{2}$"` and strict rollover validation. For a season query, join `PlayerSeasonStat`, filter/sort on season columns, and construct `PlayerSchema` with `primary_team_abbr` plus season values. For the seasonless query, retain the current ORM query unchanged.

The detail route queries the matching season row when requested and returns 404 when the player exists but has no row for that season. Team name/city are loaded for the season row's primary team, not blindly from `Player.team_abbr`.

- [ ] **Step 5: Run API tests and full backend regression suite**

Run: `uv run pytest backend/tests/test_players_api.py -v`

Expected: all player API tests pass.

Run: `uv run pytest`

Expected: all backend tests pass.

- [ ] **Step 6: Commit Task 4**

```bash
git add backend/app/routers/players.py backend/app/schemas/player.py backend/tests/test_players_api.py
git commit -m "feat: expose season-aware player statistics"
```

---

### Task 5: Frontend Season Selector and Navigation

**Files:**
- Create: `frontend/src/hooks/usePlayerSeasons.ts`
- Create: `frontend/src/pages/Players.test.tsx`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/hooks/usePlayers.ts`
- Modify: `frontend/src/hooks/usePlayerDetail.ts`
- Modify: `frontend/src/pages/Players.tsx`
- Modify: `frontend/src/pages/PlayerDetail.tsx`
- Modify: `frontend/src/types/index.ts`

**Interfaces:**
- Consumes: Task 4 endpoints.
- Produces: season selector persisted as `?season=YYYY-YY` through player list/detail navigation.

- [ ] **Step 1: Add failing API helper and Players-page tests**

Mock `getPlayerSeasons`, `getPlayers`, and `getTeams`. Test newest default, explicit query selection, selection updates, detail navigation, and no-season empty state:

```tsx
it("defaults to the newest imported player season", async () => {
  vi.mocked(getPlayerSeasons).mockResolvedValue(["2025-26", "2024-25"]);
  vi.mocked(getPlayers).mockResolvedValue([player]);
  renderPlayers("/players");

  await waitFor(() =>
    expect(getPlayers).toHaveBeenCalledWith(
      expect.objectContaining({ season: "2025-26" }),
    ),
  );
  expect(screen.getByRole("combobox", { name: /season/i })).toHaveValue("2025-26");
});

it("does not request unscoped players when no seasons are imported", async () => {
  vi.mocked(getPlayerSeasons).mockResolvedValue([]);
  renderPlayers("/players");
  expect(await screen.findByText(/no player seasons imported/i)).toBeInTheDocument();
  expect(getPlayers).not.toHaveBeenCalled();
});
```

Add a detail-hook test asserting `getPlayer(1, "2025-26")` and a back link preserving `?season=2025-26`.

- [ ] **Step 2: Run frontend tests and verify RED**

Run: `npm test -- --run frontend/src/pages/Players.test.tsx`

Working directory: `frontend`

Expected: tests fail because the season API and selector do not exist.

- [ ] **Step 3: Extend API helpers and types**

Add `apiNbaId: number | null` and `season: string | null` to `Player`; correct `nbaId` to `number | null`.

Implement:

```typescript
export function getPlayerSeasons(): Promise<string[]> {
  return fetcher("/players/seasons");
}

// Add season?: string to getPlayers params and URLSearchParams.
export function getPlayer(id: number, season?: string): Promise<PlayerDetail> {
  const query = season ? `?season=${encodeURIComponent(season)}` : "";
  return fetcher(`/players/${id}${query}`);
}
```

- [ ] **Step 4: Implement hooks and selector**

`usePlayerSeasons` returns `{ seasons, loading, error }` with cancellation protection. `usePlayers` accepts `season?: string` and `enabled?: boolean`, resets loading/error when dependencies change, and makes no request when disabled. `usePlayerDetail(id, season)` includes both in its completed-request key.

In `Players.tsx`, use `useSearchParams`. When no query season exists and seasons load, replace the URL with the first season. Render an accessible `<select aria-label="Season">`; updating it writes the query string. Pass the selected season to `usePlayers`, and navigate to `/players/${id}?season=${season}`.

In `PlayerDetail.tsx`, read the season query, pass it to the hook, display it near “Games Played,” and preserve it in both Back actions.

- [ ] **Step 5: Run frontend tests, lint, and build**

Run: `npm test -- --run`

Expected: all frontend tests pass.

Run: `npm run lint`

Expected: exit 0 with no lint errors.

Run: `npm run build`

Expected: TypeScript and Vite build exit 0.

- [ ] **Step 6: Commit Task 5**

```bash
git add frontend/src/lib/api.ts frontend/src/hooks/usePlayerSeasons.ts frontend/src/hooks/usePlayers.ts frontend/src/hooks/usePlayerDetail.ts frontend/src/pages/Players.tsx frontend/src/pages/PlayerDetail.tsx frontend/src/pages/Players.test.tsx frontend/src/types/index.ts
git commit -m "feat: select player statistics by season"
```

---

### Task 6: Live Provider Probe and Final Verification

**Files:**
- Review: all files changed in Tasks 1-5
- Modify only if verification exposes a requirement failure.

**Interfaces:**
- Consumes: completed API-NBA MVP.
- Produces: verified branch and exact local import instructions.

- [ ] **Step 1: Run a one-request provider probe**

With `API_NBA_KEY` configured locally, run a single `/teams` call through the new client and print only the response count and remaining-quota headers. Do not print the key or full payload.

Expected: HTTP 200, a non-empty team list, and no authentication/provider error.

- [ ] **Step 2: Run all backend verification**

Run: `uv run pytest`

Expected: zero failures.

Run: `cd backend && ../.venv/bin/alembic heads`

Expected: exactly one head, `20260925_api_nba_player_seasons`.

- [ ] **Step 3: Run all frontend verification**

Run: `npm test -- --run`

Working directory: `frontend`

Expected: zero failures.

Run: `npm run lint`

Expected: exit 0.

Run: `npm run build`

Expected: exit 0.

- [ ] **Step 4: Validate Compose and build production images**

Run: `docker compose --env-file .env.example -f compose.yaml config -q`

Run: `APP_HOST=stats.example.com docker compose --env-file .env.example -f compose.prod.yaml config -q`

Run: `APP_HOST=stats.example.com docker compose --env-file .env.example -f compose.prod.yaml build`

Expected: both configurations validate and every production image builds.

- [ ] **Step 5: Run source and secret checks**

Run: `git diff --check origin/main...HEAD`

Run: `git grep -n -E '(API_NBA_KEY|BALLDONTLIE_API_KEY)=[^$]' -- ':!*.example' ':!docs/**' || true`

Expected: no whitespace errors and no committed key values.

Run: `git status --short`

Expected: clean worktree.

- [ ] **Step 6: Review requirements against evidence**

Confirm from tests and code that the implementation uses API-NBA rather than API-Basketball, stays within 61 calls, stores one atomic season snapshot, preserves seasonless APIs, exposes imported seasons, carries frontend selection into detail navigation, and leaves BALLDONTLIE team/game sync unchanged.

- [ ] **Step 7: Commit any verification-only corrections**

If verification required a correction, stage only the relevant files and commit:

```bash
git commit -m "fix: complete api-nba player season verification"
```

If no correction was needed, create no empty commit.
