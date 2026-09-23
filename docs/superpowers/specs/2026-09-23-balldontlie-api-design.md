# BALLDONTLIE Free-Tier Backend Design

## Context

HoopStats currently obtains NBA data from the `nba_api` package and the NBA
public CDN. Those sources use different response formats and identifiers, and
some of them are unreliable outside a browser-like environment. The requested
change introduces BALLDONTLIE as the source for the data available on its free
tier while preserving the existing FastAPI and PostgreSQL architecture.

BALLDONTLIE's free tier exposes teams, player profiles, and games. It is limited
to five requests per minute. Player statistics, active-player filtering,
standings, box scores, and injuries are not available on the free tier.

## Goals

- Use BALLDONTLIE for teams, basic player profiles, live games, schedules, and
  historical games.
- Keep the existing `/teams`, `/players`, and `/games` HTTP routes backed by the
  local database.
- Respect the five-requests-per-minute limit during scheduled and manual syncs.
- Preserve existing official NBA identifiers when BALLDONTLIE identifiers are
  added.
- Continue returning the current frontend-compatible response shapes.
- Provide deterministic unit tests without making real network requests or
  waiting for the production rate limiter.

## Non-goals

- BALLDONTLIE paid endpoints, including player game statistics, season
  averages, standings, box scores, active-player filtering, and injuries.
- Replacing the existing frontend or redesigning its pages.
- Creating a BALLDONTLIE account or storing an API key in the repository.
- Deleting existing NBA- or ESPN-derived database records.
- Changing the prediction model.

## Selected Approach

Add a database-backed BALLDONTLIE provider adapter. Scheduled and manual jobs
will fetch provider data, normalize it into the application's existing service
types, and upsert it through repositories. Public API requests will continue to
read PostgreSQL and Redis rather than proxying BALLDONTLIE directly.

This approach protects the five-request-per-minute allowance from user traffic,
keeps the application usable during provider outages, and minimizes frontend
changes. A direct proxy was rejected because ordinary page traffic could exhaust
the free allowance. Separate `/balldontlie/*` routes were rejected because they
would duplicate the existing backend contract without adding user value.

## Configuration

Add the following settings:

- `balldontlie_api_key`: loaded from `BALLDONTLIE_API_KEY`; empty by default so
  imports and API startup remain possible before local configuration.
- `balldontlie_base_url`: defaults to
  `https://api.balldontlie.io/v1` and exists primarily for tests.
- `balldontlie_request_interval_seconds`: defaults to `12.0`, the minimum
  spacing required for five requests per minute.

The client will fail with a clear configuration error when a sync is attempted
without a key. `.env.example`, Compose configuration, and the README will name
the variable and describe the free-tier limitations. Secrets will never be
logged or committed.

## Provider Client

Create `backend/app/services/clients/balldontlie.py` as an asynchronous client
built on `httpx.AsyncClient`.

Responsibilities:

- Send the API key in the `Authorization` header.
- Serialize array query parameters using BALLDONTLIE's `field[]` convention.
- Follow cursor pagination with `per_page=100` until `next_cursor` is absent.
- Validate that list responses contain a `data` list and an optional `meta`
  object.
- Enforce one shared request interval within the client process.
- Retry a `429` response once, honoring a bounded `Retry-After` value when
  present.
- Raise provider-specific exceptions for configuration, authentication,
  rate-limit exhaustion, invalid responses, and other HTTP failures.
- Expose focused methods for `get_teams`, `get_players`, and `get_games`.

The rate limiter will use an injectable clock and sleep function. Tests can
therefore verify request spacing without real delays. All fetch methods will
accept an injected HTTP transport/client for fixture-based tests.

## Identifier Strategy and Database Changes

BALLDONTLIE team and player IDs are not official NBA IDs. Reusing the existing
`nba_id` columns would corrupt identifier semantics and could duplicate records
in an already populated database.

Add nullable, unique `balldontlie_id` columns to `teams` and `players` through
an Alembic migration:

- Teams are matched by abbreviation, then their `balldontlie_id`, name, city,
  and conference are updated. Existing `nba_id` values remain unchanged.
- Players are matched by `balldontlie_id`. During the first migration sync, an
  unmatched profile may reuse a single existing row with the same normalized
  name and team; otherwise a new row is inserted.
- `Player.nba_id` becomes nullable so a BALLDONTLIE-only installation does not
  invent an official NBA identifier.
- BALLDONTLIE game IDs are stored as strings prefixed with `bdl:`. This avoids
  collisions with existing NBA game IDs and fits the existing string key.

The public schema keeps the existing `nbaId` field but makes it nullable. It
adds `balldontlieId` so clients can use the correct provider identifier.

## Normalized Data

### Teams

Each provider team supplies abbreviation, city, name, and conference. The
repository keeps any existing record, conference rank, last-ten result, and
streak because those fields are not available on the free tier. New teams use
`0-0` for the required record and `null` for unavailable standings fields.

### Players

Each provider player supplies first name, last name, team, position, and
possibly a jersey number. The normalized profile contains:

- BALLDONTLIE ID;
- combined, trimmed name;
- team abbreviation;
- position;
- jersey number when present.

Only profiles with a recognized current NBA team abbreviation are imported.
The existing statistics fields remain at their stored values for matched rows
and default to zero for new rows. The free endpoint does not reliably identify
active players, so the backend will not claim that the imported list is an
active roster.

### Games

The provider game object is normalized to the current `Game` model:

- visitor team becomes `team1` and home team becomes `team2`, preserving the
  existing application convention;
- provider `status_state` maps `scheduled` to `scheduled`, `in_progress` to
  `live`, and `final` to `final`;
- postponed, canceled, delayed, suspended, abandoned, or unknown games are
  skipped with a warning because the current public schema cannot represent
  those states safely;
- provider scores are stored only for live or final games;
- `datetime` becomes the timezone-aware start time;
- provider season year becomes the existing `YYYY-YY` season string;
- `postseason=true` maps to `playoffs`; other supported games map to `regular`;
- venue remains an empty string because it is unavailable from the free game
  response.

A non-empty provider page that contains no valid records is treated as invalid
data rather than an empty schedule, preventing accidental clearing of today's
games after an upstream schema change.

## Synchronization Flows

### Teams

`sync_teams` performs one teams request, normalizes the response, upserts all
teams, commits, and invalidates the teams cache. It does not call the paid
standings endpoint.

### Players

`sync_players` paginates the free players endpoint at 100 profiles per request,
filters invalid/teamless profiles, and upserts basic profiles. Because this can
take several minutes on the free tier, it remains part of the infrequent
statistics job rather than the live job.

### Today's Games

`sync_games` requests the current UTC date with `dates[]`, normalizes the
response, resets today's flags only after a valid response, upserts games, and
invalidates live and Elo caches. Free-tier box-score synchronization is removed
from this flow.

### Schedule

`sync_schedule` requests games from today through 30 days ahead. This range is
small enough to fit within a single 100-item page under a normal NBA schedule,
while cursor pagination remains available if necessary. Scheduled records are
upserted through the same normalized game repository path.

### Historical Games

`sync_historical_games` converts an application season such as `2025-26` to
BALLDONTLIE's starting year `2025`, requests regular and playoff games, follows
pagination, and upserts final scores. Manual multi-season imports are supported
but naturally take several minutes because every page observes the rate limit.

### Scheduler

Existing scheduler separation remains:

- live game refresh uses the lightweight date-filtered games request;
- schedule refresh imports the next 30 days;
- the infrequent job refreshes teams, player profiles, current-season history,
  and database-derived predictions.

Unsupported paid BALLDONTLIE operations are not called. ESPN injury behavior is
left unchanged because it is a separate provider and outside this change.

## Error Handling and Data Safety

- Missing API key: the sync step logs a configuration error and leaves stored
  data unchanged.
- `401`: report an invalid or unauthorized API key without logging the key.
- First `429`: wait for the bounded retry delay and retry once.
- Second `429`, transport failure, or `5xx`: fail that sync step; the scheduler
  rolls back the active transaction and continues with later independent steps.
- Malformed envelope or records: reject the response before reset/delete-style
  operations.
- Individual malformed records: skip with a warning when other valid records
  remain.
- Existing rows: unavailable free-tier fields are preserved instead of being
  overwritten with invented values.

## Testing Strategy

Follow test-driven development with fixture responses and injected dependencies.

Client tests will cover:

- authorization header and array parameter serialization;
- cursor pagination;
- five-per-minute spacing without real sleep;
- one bounded `429` retry;
- `401`, transport, and malformed-envelope errors.

Normalization tests will cover:

- teams and simple player profiles;
- scheduled, live, and final game mappings;
- unsupported lifecycle states;
- season and start-time conversion;
- rejection of a wholly invalid non-empty response.

Repository and sync tests will cover:

- preservation of official NBA IDs and unavailable statistics;
- idempotent upserts by BALLDONTLIE ID;
- no reset or commit after a failed provider response;
- correct date, season, and schedule filters;
- cache invalidation after successful writes.

The complete backend suite and frontend build will be run before completion.
No verification test will require a real API key or external network access.

## Rollout and Operations

1. Apply the Alembic migration.
2. Configure `BALLDONTLIE_API_KEY` in local or deployment secrets.
3. Deploy the backend and scheduler.
4. Run the regular seed command once to populate teams, players, current games,
   and schedule data.
5. Use the existing season seed command for older seasons when needed, allowing
   enough time for the free-tier request interval.

Existing data remains available if the provider is temporarily unavailable.
Rollback consists of deploying the previous application version; the new
nullable columns can remain without affecting older code.

## Success Criteria

- Teams, simple player profiles, and games are populated from BALLDONTLIE using
  only free-tier endpoints.
- No request path calls BALLDONTLIE directly.
- Repeated syncs are idempotent and do not duplicate provider records.
- The client never intentionally exceeds five requests in any rolling minute
  within the scheduler process.
- Existing official NBA IDs and unrelated user changes are preserved.
- Backend tests and the frontend production build pass without network access.
