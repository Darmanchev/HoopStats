# HoopStats

HoopStats is a full-stack NBA statistics dashboard with match predictions. I started it because I wanted one project where I could combine backend development, external data, visualization and a small machine-learning pipeline instead of keeping them as separate exercises.

## What the project does

- imports teams, games, schedules, player statistics and injuries;
- shows dashboards, standings, schedules, team form and player leaders;
- calculates Elo ratings from historical games;
- predicts upcoming matches with logistic regression;
- explains a prediction using Elo, recent form, record and net rating;
- refreshes part of the data every 12 hours.

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
make up
```

The local `.env` file is intentionally ignored by Git. The database migrations
run automatically when the backend starts.

To load NBA/ESPN data after the containers start:

```bash
make seed
```

The initial sync calls external NBA/ESPN services and may take several minutes. The application is available at:

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
make train
make status
make down
```

The scheduler separates synchronization by cost:

| Data | Interval |
| --- | --- |
| Live games | 15 minutes |
| Schedule and injuries | 6 hours |
| Teams, players, team statistics, current-season history, and predictions | 12 hours |

After startup, live games sync immediately, schedule and injuries sync after
two minutes, and the larger statistics sync starts after five minutes. Jobs are
staggered and never run concurrently, which reduces load on the external APIs.

## Production deployment with Coolify

Choose the Docker Compose build pack in Coolify and set **Docker Compose
Location** to `/compose.prod.yaml`. Set a domain for the `frontend` service on
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
- `DATABASE_URL`, using the PostgreSQL owner account for migrations;
- `APP_DB_USER` and `APP_DB_PASSWORD`, using a separate runtime account;
- `SECRET_KEY` and `APP_HOST`.

`NBA_API_KEY`, `BACKEND_WORKERS`, `HTTP_PROXY`, `HTTPS_PROXY`, and `NO_PROXY`
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
`scheduler` container and import older seasons once:

```bash
python -m scripts.seed --seasons 2023-24 2024-25 2025-26
```

Do not schedule old-season imports repeatedly. The 12-hour job refreshes only
the current season.

## Architecture

```text
frontend/                          React dashboard and production image
backend/app/routers/               API endpoints
backend/app/services/clients/      NBA and ESPN integrations
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
