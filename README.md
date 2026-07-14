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
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend python seed.py
```

The initial sync calls external NBA/ESPN services and may take several minutes. After it finishes:

- frontend: [http://localhost:5173](http://localhost:5173)
- API: [http://localhost:8000](http://localhost:8000)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

To train a model on several seasons:

```bash
docker compose exec backend python seed.py --seasons 2023-24 2024-25 2025-26
docker compose exec backend python train_model.py
docker compose exec backend python seed.py
```

Useful shortcuts:

```bash
make logs
make migrate
make seed
make status
make down
```

## Architecture

```text
frontend/                       React dashboard
backend/app/routers/            API endpoints
backend/app/services/clients/   NBA and ESPN clients
backend/app/services/repositories/ database operations
backend/app/services/sync.py    data synchronization
backend/app/ml/                 features, training and prediction
backend/alembic/                database migrations
```

## Current status and next steps

The main dashboard, data synchronization and prediction flow are implemented. The scheduler currently refreshes teams, today's games, team stats, players and injuries; schedule refresh and prediction recalculation still need to be added to that periodic job. I also plan to add proper automated API tests, caching/rate-limit handling, model experiment tracking and deployment configuration.
