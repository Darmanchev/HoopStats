# Dynamic and Live Dashboard Design

Date: 2026-09-21
Status: Proposed for implementation
Branch: `develop`

## Goal

Replace every hard-coded dashboard value with data owned by HoopStats. The
dashboard must provide an accurate five-minute overview of scheduled games,
today's game state, league leaders, conference standings, recent team scoring,
and available player box scores. Browsers must only call the HoopStats API;
only the scheduler may call upstream NBA services.

## Success Criteria

- No dashboard component contains hard-coded teams, players, scores, clocks,
  rankings, or chart values.
- Dashboard data refreshes every five minutes without a page reload.
- The scheduler makes at most one upstream live-data synchronization run every
  five minutes, regardless of the number of website users.
- In-progress game scores, status text, period, and clock are stored and
  returned by the API.
- Available live or same-day player box scores are stored and returned by the
  API.
- Redis caches shared read responses and is invalidated after successful data
  synchronization.
- A failed upstream request preserves the last successfully synchronized data
  and does not make the dashboard unusable.
- Empty states clearly distinguish no scheduled games, no live game, and no
  box-score data.

## Non-goals

- WebSocket or server-sent-event updates. Five-minute polling is sufficient.
- Direct NBA API calls from the browser.
- Backfilling player box scores for old seasons. The new table stores games
  observed by the live synchronization flow; historical backfill can be a
  separate feature.
- Replacing the existing prediction model.
- Redesigning the global navigation or unrelated application pages.

## Selected Architecture

Use PostgreSQL plus Redis:

- PostgreSQL remains the durable source for games, teams, season averages, team
  form, and synchronized player game statistics.
- Redis stores short-lived serialized API responses. Cache loss is safe because
  every response can be rebuilt from PostgreSQL.
- The scheduler retrieves the NBA scoreboard and box score once every five
  minutes and updates PostgreSQL transactionally.
- The React dashboard polls only HoopStats endpoints every five minutes.

This is preferred over Redis-only storage because restarts must not remove the
latest known game state. It is preferred over browser-to-NBA requests because
direct requests multiply upstream traffic and are vulnerable to CORS, rate
limits, and datacenter IP blocking.

## Backend Data Model

### Game extensions

Add nullable or defaulted columns to `games`:

- `status`: `scheduled`, `live`, or `final`.
- `status_text`: upstream display text such as `7:30 PM ET`, `Q3 04:12`, or
  `Final`.
- `period`: current period number when available.
- `clock`: current upstream game clock when available.
- Continue using `score1` and `score2`, but update them during live games rather
  than only after final status.

Existing rows are migrated safely: rows with scores become `final`; future
rows without scores become `scheduled`. The existing `time` field remains for
compatibility during this change.

### Team standings extensions

Add fields required by the existing standings widget:

- `conference`: `East` or `West`.
- `conference_rank`.
- `last_ten`: a display value such as `7-3`.
- `streak`: a display value such as `W3`.

The existing `record` remains the canonical wins-losses string. Games played
and winning percentage are derived from it.

### PlayerGameStat

Create `player_game_stats` with a composite uniqueness constraint on
`game_id` and `nba_id`:

- `game_id`, linked to `games` with cascade deletion.
- `nba_id`, `name`, and `team_abbr`.
- `points`, `rebounds`, and `assists`.
- `steals`, `blocks`, and `minutes` when provided upstream.
- `updated_at` for freshness reporting.

The table is upserted so each synchronization replaces the current values for
the same player and game without creating duplicates.

## Upstream Client and Synchronization

Extend the NBA client behind two narrow functions:

- `fetch_live_scoreboard()` returns normalized game state.
- `fetch_live_boxscore(game_id)` returns normalized player rows for one live or
  same-day game.

The client module owns upstream field parsing. Repository and router code must
not depend on the raw NBA response structure.

`sync_games` will:

1. Fetch the scoreboard.
2. Upsert all scheduled, live, and final same-day games, including scores,
   status, period, and clock.
3. Fetch and upsert a box score for each live or final same-day game when the
   upstream source exposes one.
4. Commit database changes.
5. Invalidate affected Redis keys.

The `live-games` scheduler interval changes from 15 minutes to a configurable
`LIVE_SYNC_MINUTES`, defaulting to `5`. The frontend refresh interval uses the
same five-minute default through `VITE_DASHBOARD_REFRESH_MS=300000`.

If the upstream service fails, the job logs the error and keeps the previous
database state. A failure for one box score does not prevent other games from
being updated.

## API Contracts

### `GET /games/today`

Return a dedicated live-capable schema containing the existing game fields and:

- `status`
- `statusText`
- `period`
- `clock`
- `score1`
- `score2`

The endpoint returns scheduled, live, and final games marked for the current
day, ordered by start time.

### `GET /games/{id}`

Return the same optional live fields so the featured game and match detail page
share one truthful contract. Existing upcoming-game consumers remain compatible
because the new fields are optional.

### `GET /games/{id}/boxscore`

Return player rows ordered by points descending. Return an empty list when the
game exists but no box score is available, and `404` when the game does not
exist.

### Existing endpoints

- `/teams/` supplies team identity, record, standings fields, and embedded team
  form statistics.
- `/analytics/leaders` supplies the dashboard's top season player.
- `/games/upcoming` supplies the next three scheduled games.

No separate aggregate dashboard endpoint is required. The frontend makes a
small fixed set of HoopStats requests, deduplicates them in memory, and stays
well below the internal rate limit.

## Redis Caching

Use versioned keys:

- `api:games:today:v1`
- `api:game:{game_id}:boxscore:v1`
- Existing `api:teams:v1`
- Existing analytics cache where applicable

Today-game and box-score caches use a 300-second TTL. Successful live
synchronization deletes today-game and affected box-score keys after the
database commit. Cache reads fail open: a Redis read error falls back to
PostgreSQL, and a Redis write error does not fail a successful API response.

The existing rate limiter still counts requests before endpoint cache lookup.
Frontend deduplication and the fixed five-minute refresh keep request volume
small; caching primarily reduces database work and improves response time.

## Frontend Data Flow

Create `useDashboard` as the only data coordinator for the page. It loads:

- teams with statistics;
- upcoming games;
- today's games;
- analytics leaders;
- the selected live or same-day game's box score.

It performs an immediate load, refreshes every 300,000 milliseconds, reuses
in-flight requests during React Strict Mode, and cleans up its timer when the
page unmounts. Partial failures are tracked per dataset so one unavailable
widget does not replace the entire dashboard with a page-level error.

Selection priority for the featured game is:

1. An in-progress game.
2. The next scheduled game today.
3. The nearest upcoming game.
4. The most recently final same-day game.

## Widget Behavior

### Upcoming Games

Show the nearest three scheduled games. The Preview button navigates to
`/match/{id}`. Display a clear empty state when the schedule has no future
games.

### Featured Game

For a live game, show current scores, status text, period, and clock. For a
scheduled game, show date, time, venue, prediction, and win probability without
inventing a score. Its action navigates to the match detail page.

### Top Player

Use the first points leader from `/analytics/leaders`, including the player's
NBA headshot, season averages, and a link to `/players/{id}`. Do not display
plus-minus because the current season-average model does not store it.

### Standings

Use real conference, rank, record, last-ten, and streak fields. Default to the
Western Conference to preserve the current layout and provide an East/West
toggle. Calculate games played and winning percentage from the record.

### Team Efficiency

Render the selected team's `lastScores` through the existing `SparkLine`
component. Default to the first featured-game team, otherwise the highest-ranked
available team. Provide a team selector and calculate the displayed scoring
average from the same values.

### Live Game Stats

Show up to six player rows from the selected live or most recently final
same-day game. Include headshot, team, points, rebounds, and assists. When no
same-day box score exists, show a truthful `No live box score available` state
instead of fallback sample players.

## Navigation and Interaction

- Preview and featured-game actions open the match detail route.
- Top-player action opens the player detail route.
- View Data from team efficiency opens the selected team route.
- Interactive controls remain keyboard accessible and show focus styles.

## Loading, Empty, and Error States

- Initial page loading may use the existing page loading state.
- After initial data exists, refreshes keep old data visible and expose an
  `Updating` indicator rather than blanking the page.
- Each widget owns its empty and error presentation.
- The dashboard displays a `Last updated` timestamp based on the most recent
  successful refresh.
- Stale data remains visible when refresh fails, with a non-blocking warning.

## Testing Strategy

Backend work follows test-driven development:

- Migration/model tests for new defaults and constraints.
- NBA client parsing tests using captured minimal response fixtures.
- Repository tests for live score and player-stat upserts.
- API tests for live, scheduled, final, missing-game, and empty-box-score cases.
- Redis hit, miss, failure fallback, TTL, and invalidation tests.
- Scheduler test proving the default live interval is five minutes.

Frontend testing adds Vitest and React Testing Library:

- `useDashboard` immediate load, five-minute refresh, cleanup, deduplication,
  and partial-failure tests.
- Widget tests for live, scheduled, final, empty, and error states.
- Navigation tests for all dashboard actions.

Final verification includes the complete backend suite, frontend tests, lint,
production build, Compose configuration validation, container health, and a
runtime smoke test against the dashboard APIs.

## Delivery Sequence

1. Add backend tests, migration, and models.
2. Normalize upstream scoreboard and box-score data.
3. Implement repository upserts and cache invalidation.
4. Extend game APIs and add box-score API with tests.
5. Configure the five-minute scheduler and environment examples.
6. Add frontend test tooling and dashboard data hook.
7. Convert widgets one at a time and wire navigation.
8. Run full verification and rebuild local containers.

## Deployment Notes

- Run Alembic migration before the backend starts; the existing container
  startup command already does this.
- Run exactly one scheduler container to avoid duplicate upstream work.
- Keep `LIVE_SYNC_MINUTES=5` unless upstream limits require a slower interval.
- A datacenter block remains observable as scheduler errors; the application
  continues serving the last stored data instead of making browser-side
  fallback requests.
