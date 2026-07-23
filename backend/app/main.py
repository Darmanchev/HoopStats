from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from .config import settings
from .rate_limit import RateLimitMiddleware
from .routers import teams, games, injuries, players, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    await redis.ping()
    app.state.redis = redis
    try:
        yield
    finally:
        await redis.aclose()

app = FastAPI(title="HoopStats API", lifespan=lifespan)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(teams.router)
app.include_router(games.router)
app.include_router(injuries.router)
app.include_router(players.router)
app.include_router(analytics.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
