# HoopStats

HoopStats is a full-stack NBA statistics dashboard with match predictions. I started it because I wanted one project where I could combine backend development, external data, visualization and a small machine-learning pipeline instead of keeping them as separate exercises.

## What the project does

- imports teams, games, schedules, basic player profiles and injuries;
- shows dashboards, standings, schedules, team form and player leaders;
- calculates Elo ratings from historical games;
- predicts upcoming matches with logistic regression;
- explains a prediction using Elo, recent form, record and net rating;
- refreshes live data every 15 minutes and the remaining data daily.

## Why these technologies

I chose **FastAPI** for an async API because most backend work is waiting for the NBA and ESPN data sources. **PostgreSQL, SQLAlchemy and Alembic** give the project a real data model and repeatable schema changes. The frontend uses **React + TypeScript** because the dashboard has many related states and reusable widgets.

For the prediction model I used **logistic regression** instead of a more complex model. The output I need is a win probability, and features such as Elo difference naturally fit a logistic decision boundary. Scaling is included because Elo and percentage-based features have very different ranges.

The main difficulty was external data: different sources use different identifiers, formats and update times. I separated API clients, repositories and synchronization code so parsing problems do not leak into the routes. For model evaluation, the latest season is kept as a time-based test set instead of randomly mixing future and past games.

## Stack

- Python 3.13, FastAPI, SQLAlchemy, Alembic
- scikit-learn, pandas, joblib
- React 19, TypeScript, Vite, Tailwind CSS
- PostgreSQL 17, APScheduler
- Docker Compose, uv

## Local setup

Requirements: Docker with Compose.

```bash
git clone https://github.com/Darmanchev/HoopStats.git
cd HoopStats
cp .env.example .env
# Add your BALLDONTLIE_API_KEY and API_NBA_KEY before importing NBA data.
make up
```

The local `.env` file is intentionally ignored by Git. The database migrations
run automatically when the backend starts.

Create a free API key at [app.balldontlie.io](https://app.balldontlie.io), then
set `BALLDONTLIE_API_KEY` in `.env`. The free tier supplies the teams, basic
player profiles (name, team and position), and games used by HoopStats. It is
limited to five requests per minute, so the backend spaces provider requests
at least 12 seconds apart and large first-time imports can take several
minutes.

To load BALLDONTLIE/ESPN data after the containers start:

```bash
make seed
```

Player profiles and season statistics use the NBA-specific
[API-NBA service from API-Sports](https://api-sports.io/sports/nba). Create a
free API-Sports account and set `API_NBA_KEY` in `.env`. The free plan allows
100 requests per day. A complete season import uses about 61 requests, so
historical player seasons are imported manually and are not scheduled:

```bash
make seed-players SEASON=2025-26
```

The import fetches every NBA team before replacing that season in one database
transaction. If the provider rejects or interrupts any request, the existing
season data stays unchanged.

The initial sync calls external BALLDONTLIE and ESPN services. The application
is available at:

- frontend: [http://localhost:5173](http://localhost:5173)
- API: [http://localhost:8000](http://localhost:8000)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

To train a model on several seasons:

```bash
make seed-seasons SEASONS="2023-24 2024-25 2025-26"
make train
make seed
```

Useful shortcuts:

```bash
make logs
make migrate
make seed
make seed-players SEASON=2025-26
make train
make status
make down
```

The scheduler separates synchronization by cost:

| Data | Interval |
| --- | --- |
| Live games | 15 minutes |
| Schedule and injuries | 24 hours |
| Teams, players, team statistics, current-season history, and predictions | 24 hours |

After startup, live games sync immediately, schedule and injuries sync after
two minutes, and the larger statistics sync starts after six minutes. Jobs are
staggered and never run concurrently, which reduces load on the external APIs.

## Production deployment with Coolify

Set `CURRENT_SEASON=2026-27` (or the season you want the scheduled imports to
refresh) in the deployment environment. The value must use consecutive
`YYYY-YY` years. Dashboard historical statistics have a separate season selector:
leaders use imported player-season averages, and standings/form use completed
regular-season games. Seasons with only one dataset show an explicit missing-data
message for the other dataset. Partial game imports produce partial team records.

The `20261004_game_seasons` migration repairs season labels and game types for
recognizable legacy NBA game IDs, including preseason games. It preserves IDs,
scores and player box scores, and does not modify BALLDONTLIE (`bdl:`) records
or ambiguous IDs/dates. Preseason games can be selected separately on Schedule
and are excluded from regular-season standings. Game inserts must now supply an
explicit season rather than silently defaulting to `2025-26`.
Back up the production database before redeploying: production runs this repair
automatically through its migration service. Downgrading restores the old schema
default but deliberately does not restore incorrect season labels.

The live job matches NBA scoreboard games to local BALLDONTLIE records by home
team, away team, and Eastern game date. It imports box scores using the official
NBA ID and stores them under the local game ID; ambiguous matches are skipped.
NBA scoreboard/box-score availability still depends on the public NBA service.

The dashboard's "Last checked" time is the browser refresh time. Source update
status separately reports successful imports and failures. Status is held in
Redis and starts empty after Redis is recreated. `make seed` prints per-step
counts and exits unsuccessfully if any step fails, while completing other steps.

Choose the Docker Compose build pack in Coolify and set **Docker Compose
Location** to `/compose.prod.yaml`. Set a domain for the `hoopstats-frontend` service on
container port `8080`. Set `APP_HOST` to that domain's hostname without a
scheme, port, or path (for example, `stats.example.com`).
Enable **Force HTTPS** for that domain. Coolify terminates TLS and redirects
HTTP to HTTPS; the container port is only exposed inside the Compose network.
The production Nginx response adds HSTS and rejects requests with another
`Host` header. FastAPI validates the same host. Swagger, ReDoc, and the OpenAPI
schema are disabled in production.

Configure production values in Coolify instead of keeping a production
environment file in the repository. Required variables:

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`;
- `DATABASE_URL`, using the PostgreSQL owner account for migrations. Use
  `hoopstats-db` as the database host inside the Compose network;
- `APP_DB_USER` and `APP_DB_PASSWORD`, using a separate runtime account;
- `SECRET_KEY`, `APP_HOST`, `BALLDONTLIE_API_KEY`, and `API_NBA_KEY`.

`BACKEND_WORKERS`, `HTTP_PROXY`, `HTTPS_PROXY`, and `NO_PROXY`
are optional. For a manual deployment outside Coolify, provide an environment
file stored outside the repository:

```bash
docker compose \
  --env-file /secure/path/hoopstats.env \
  -f compose.prod.yaml \
  up -d --build
```

Production uses two PostgreSQL logins:

- `POSTGRES_USER` / `DATABASE_URL`: database owner, used only by PostgreSQL and
  the one-shot Alembic migration service;
- `APP_DB_USER` / `APP_DB_PASSWORD`: restricted runtime login used by the API
  and scheduler.

Use different random passwords for these roles. On every deployment the
one-shot `db_roles` service idempotently creates or updates the runtime role and
grants only schema usage and table/sequence DML permissions.

Redis provides shared API rate-limit counters and a 24-hour Elo cache. A
successful game sync invalidates the cache, so the first following request
rebuilds current ratings once. The scheduler runs in a separate container, so
multiple Uvicorn workers do not duplicate periodic synchronization jobs.

For the first production deployment, open the Coolify terminal for the
`hoopstats-scheduler` container and import older seasons once:

```bash
python -m scripts.seed --seasons 2023-24 2024-25 2025-26
```

Do not schedule old-season imports repeatedly. The 24-hour job refreshes only
the current season.

## Architecture

```text
frontend/                          React dashboard and production image
backend/app/routers/               API endpoints
backend/app/services/clients/      BALLDONTLIE, NBA and ESPN integrations
backend/app/services/repositories/ database operations
backend/app/services/sync.py       data synchronization
backend/app/ml/                    features, training and prediction
backend/scripts/                   operational commands
backend/alembic/                   database migrations
docker/postgres/                   database role configuration
```

## Current status and next steps

The main dashboard, data synchronization and prediction flow are implemented.
The scheduler refreshes teams, games, schedules, team statistics, players,
injuries, and predictions. Automated backend tests cover the main API contract
and scheduler behavior. The next priorities are broader integration coverage,
frontend tests, and model experiment tracking.

The existing player routes remain backward compatible, with an optional
season query and a new player-season listing endpoint. API-NBA supplies player
profiles and season statistics; BALLDONTLIE continues to supply teams and
games. Provider IDs remain separate, unsupported fields stay nullable, and
team statistics and injuries continue through their existing integrations.

## Exploration and prediction improvements

Schedule now filters games on the server and loads 50 results per page. It supports
season, competition, live/scheduled/final status, month, weekday and favorite teams.
The header searches imported players, teams and games. Player comparison uses one
shared season, and its URL preserves both players and the season.

Save teams or players from their cards and profiles. Favorites are stored in the
current browser and appear on the dashboard; no account is required. Player logs
show only imported official box scores. An empty historical log does not mean the
player did not play. Opening a log or comparison does not fetch external NBA data.

Match details display available scores, current period/clock, per-period points
(including overtime), and box scores. Supplementary request failures have their own
retry actions. Visible live match pages refresh every 30 seconds; provider imports
still run at the configured live-sync interval. Missing predictions and quarter
scores are explicitly labeled as unavailable.

Run migrations before using the new backend, then retrain the model:

```bash
make migrate
make train
```

Training requires at least 200 eligible rows with eight prior games per team and
both outcome classes. Ratings and model history include completed regular-season
and playoff games, excluding preseason, tied/incomplete results and invalid teams.
Historical fixture predictions use only results preceding the fixture date.
Home/away information is recorded explicitly by new imports. Older NBA history
imports did not reliably retain venue ordering; these games use an unknown-home
input rather than a guessed home team. BALLDONTLIE ordering is known.

The model now uses home advantage and rest-day difference alongside form, recent
win percentage, scoring margin and Elo. Rest is capped at seven days. Training
adds mirrored team-order samples so home advantage can be learned even though
provider records are away-first. Evaluation counts refer to real games, without
mirroring held-out results. Existing model files require retraining for the new
feature format; incompatible files produce unavailable predictions.

Analytics includes imported game seasons and displays Elo and leaders for the
selected season, with separate messages for missing datasets. Its prediction
performance section reports chronological held-out accuracy, log loss, Brier score,
AUC when defined, calibration bins and individual results. The evaluator fits on
prior seasons and tests the latest eligible season; the deployed model is then
refit on all eligible games. With only one season, test performance is unavailable.
The Elo baseline uses Elo probabilities; the fixed home-preference baseline uses
60% for a known home team (40% away, 50% unknown). These are evaluation baselines,
not guarantees of prediction quality.

Model and evaluation artifacts are written atomically to `HOOPSTATS_MODEL_DIR`
(default: `backend/app/ml` outside Docker). Docker uses `/app/artifacts`. Development
has a writable artifact volume; production shares it between the scheduler
(writable) and API (read-only), so manually training in the scheduler updates the
API's report and model. Production training:

```bash
python -m scripts.train_model
```

Run that command in the scheduler container after historical imports. It refreshes
upcoming predictions after training. Retraining and historical imports are manual;
viewing Analytics does not train a model or spend provider quota.
