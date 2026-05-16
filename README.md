# HoopStats — NBA Statistics & Predictions

A full-stack application for tracking NBA game statistics, team performance, and match predictions powered by machine learning.

## Features

- **Live game tracking** — today's games, scores, and status
- **Team statistics** — win/loss records, recent form, scoring trends
- **Injury reports** — player injury status for all teams
- **Match predictions** — ML-based win probability using RandomForest
- **Historical data** — past game results and team performance

## Tech Stack

### Backend
- Python 3.13
- FastAPI
- SQLAlchemy (async) + PostgreSQL
- Alembic (migrations)
- NBA API (data source)
- scikit-learn (ML predictions)
- Poetry (dependency management)

### Frontend
- React 19 + TypeScript
- Vite
- Tailwind CSS 4

### Infrastructure
- Docker + Docker Compose
- PostgreSQL 17

## Quick Start

### Prerequisites

- Python 3.13+
- Poetry
- Node.js 20+
- Docker & Docker Compose (optional)

### Backend

```bash
cd backend

# Install dependencies
poetry install

# Set up environment
cp .env.example .env
# Edit .env with your database URL and NBA API key

# Run database migrations
alembic upgrade head

# Seed the database
python seed.py

# Start the server
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set up environment
cp .env.example .env

# Start dev server
npm run dev
```

### Docker

```bash
# Build and run all services
docker compose up --build
```

Backend will be available at `http://localhost:8000`, frontend at `http://localhost:5173`.

## Project Structure

```
basketballStatistics/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── models/       # SQLAlchemy models
│   │   ├── routers/      # API endpoints
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic (NBA API sync)
│   │   └── tasks/        # Background tasks
│   ├── alembic/          # Database migrations
│   └── tests/            # Backend tests
├── frontend/             # React application
│   └── src/
│       ├── components/   # UI components
│       ├── hooks/        # Custom React hooks
│       ├── lib/          # API client
│       ├── pages/        # Page components
│       └── types/        # TypeScript types
├── ml/                   # ML training scripts
│   ├── train.py          # Model training
│   └── model.pkl         # Trained model
└── data/                 # Database volumes (gitignored)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/games/upcoming` | Upcoming games |
| GET | `/games/today` | Today's games |
| GET | `/games/past` | Past game results |
| GET | `/games/{id}` | Single game details |
| GET | `/teams` | All teams |
| GET | `/teams/{abbr}/stats` | Team statistics |
| GET | `/injuries` | All injuries |
| GET | `/injuries/{team_abbr}` | Team injuries |

## ML Model

The prediction model uses RandomForest classifier trained on:
- Team win percentage
- Recent form (last 5 games)
- Average scoring

To retrain:

```bash
cd ml
python train.py
```

## License

MIT
