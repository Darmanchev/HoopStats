# API-NBA Player Seasons MVP Design

## Context

HoopStats currently imports basic player profiles from BALLDONTLIE. The free
BALLDONTLIE plan does not provide the season statistics needed by the Players
page, and the current `players` table stores only one team and one mutable
statistics snapshot per player.

The MVP will use API-NBA from API-Sports for season-specific player rosters and
game statistics while retaining BALLDONTLIE for teams and games. The first
supported import is the 2025-26 season, represented by `2025` in API-NBA.

## Goals

- Import NBA player profiles associated with teams in a selected season.
- Import game-level player statistics and aggregate them into season averages.
- Store season data in PostgreSQL so frontend traffic does not consume the
  provider's daily quota.
- Let users select an available season on the Players page.
- Preserve the existing `/players` and `/players/{id}` paths and response
  conventions.
- Fit a full 30-team season import within API-NBA's free 100-request daily
  allowance.

## Non-goals

- Replacing BALLDONTLIE for teams, games, schedules, or live scores.
- Importing every historical season during the first rollout.
- Live per-possession player-stat updates.
- Redesigning the Players page.
- Perfectly representing every mid-season roster transaction in the MVP.

## Provider Integration

Add an asynchronous API-NBA client using the base URL
`https://v2.nba.api-sports.io` and the `x-apisports-key` header. Configuration
uses `API_NBA_KEY` and an overridable base URL for deterministic tests.

The synchronization flow will:

1. Fetch API-NBA teams once and match standard NBA franchises to existing
   HoopStats teams by abbreviation.
2. For each of the 30 teams, fetch `/players?team=ID&season=2025`.
3. For each team, fetch `/players/statistics?team=ID&season=2025`.
4. Normalize profiles and aggregate game rows per player across all team
   stints.
5. Select the team with the most games as the player's primary team for that
   season, using a deterministic abbreviation tie-breaker.
6. Commit the complete season atomically so a partial provider failure cannot
   leave a partly refreshed season.

The expected initial budget is approximately 61 requests: one team-directory
request plus two requests for each NBA team. The client will inspect API-Sports
quota headers when present and fail clearly before repeatedly retrying a daily
quota exhaustion response.

## Data Model

Add nullable, unique `api_nba_id` columns to `teams` and `players`. Provider IDs
remain separate from official NBA IDs and BALLDONTLIE IDs.

Add a `player_season_stats` table with one row per player and season:

- internal player foreign key;
- season label such as `2025-26`;
- primary team abbreviation;
- games played and recent-games count;
- points, rebounds, assists, steals, blocks, and minutes per game;
- field-goal, three-point, and free-throw percentages;
- source update timestamp.

The unique key is `(player_id, season)`. Percentages are calculated from total
makes and attempts rather than averaging per-game percentages. Rows are
replaced only after the provider data for the requested season is fully
validated.

The current statistics columns on `players` remain temporarily for backward
compatibility. Season-aware API responses read from `player_season_stats`.

## Backend API

Extend `GET /players/` with an optional `season` query parameter. When present,
the route joins `player_season_stats`, applies the existing team, position,
minimum-games, sorting, and pagination behavior to the selected season, and
returns the existing player response shape populated with that season's
values. Without `season`, current behavior remains unchanged.

Extend `GET /players/{player_id}` with the same optional season parameter.

Add `GET /players/seasons` returning imported player-season labels in reverse
chronological order. Declare this static route before the numeric player-detail
route.

## Frontend

The Players page will load `/players/seasons`, select the newest available
season by default, and send that season with player list and detail requests.
The existing visual design, search, team filter, position filter, sorting, and
cards remain unchanged. The selected season is stored in the URL query string
so refresh and navigation preserve it.

Player detail links carry the selected season. Empty and error states explain
whether a season has not yet been imported.

## Operations

Add `API_NBA_KEY` to `.env.example`, local Compose, and production Compose
without storing a real key.

Add a manual command for importing one season, for example:

```bash
make seed-players SEASON=2025-26
```

Historical player imports are manual and are not added to the frequent
scheduler. This protects the 100-request daily free quota. A later iteration
may schedule a single current-season refresh per day after quota monitoring is
in place.

## Error Handling

- Missing key or authentication failure: abort before database writes.
- Daily quota exhaustion: report a clear operational error and keep existing
  season data.
- Invalid season label: reject before any provider request.
- Missing or malformed team/player identifiers: reject the season import.
- Individual nullable statistic fields: treat missing counting values as zero
  only when the response represents a played game; otherwise skip the row.
- Partial team failure: roll back the entire season refresh.

## Testing

- Client tests for authentication, parameters, status errors, and quota errors.
- Normalizer tests for profiles, game rows, percentages, traded players, and
  malformed payloads.
- Repository tests for idempotent season upserts and atomic replacement.
- Sync tests proving the 30-team request pattern and rollback behavior.
- API tests for season filtering, sorting, pagination, and backward
  compatibility without a season.
- Frontend tests for default season selection, query propagation, navigation,
  and empty/error states.
- Full backend suite, frontend tests/lint/build, migration-head check, Compose
  validation, and production image build before completion.

## Success Criteria

- A manual `2025-26` import populates player profiles and non-zero season
  statistics without exceeding 100 requests.
- The Players page defaults to 2025-26 and supports selecting any imported
  player season.
- Player list and detail values change consistently with the selected season.
- Existing team/game synchronization and seasonless player routes continue to
  work.
- Provider failures never replace a complete stored season with partial data.
