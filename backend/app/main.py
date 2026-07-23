from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import settings
from .rate_limit import RateLimitMiddleware
from .routers import analytics, games, injuries, players, teams


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    await redis.ping()
    app.state.redis = redis
    try:
        yield
    finally:
        await redis.aclose()

app = FastAPI(
    title="HoopStats API",
    lifespan=lifespan,
    docs_url="/docs" if settings.api_docs_enabled else None,
    redoc_url="/redoc" if settings.api_docs_enabled else None,
    openapi_url="/openapi.json" if settings.api_docs_enabled else None,
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_host_list(),
)

app.include_router(teams.router)
app.include_router(games.router)
app.include_router(injuries.router)
app.include_router(players.router)
app.include_router(analytics.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
