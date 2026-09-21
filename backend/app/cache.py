"""Shared cache keys and invalidation helpers."""

import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

from .config import settings

logger = logging.getLogger(__name__)

ELO_CACHE_KEY = "analytics:elo:v1"
ELO_LOCK_KEY = f"{ELO_CACHE_KEY}:lock"
TEAMS_CACHE_KEY = "api:teams:v1"


async def invalidate_elo_cache() -> None:
    """Invalidate Elo after committed game updates."""
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await redis.delete(ELO_CACHE_KEY)
    except RedisError:
        # Game data is already committed; cache failure must not roll it back.
        logger.exception("Failed to invalidate Elo cache")
    finally:
        await redis.aclose()


async def invalidate_teams_cache() -> None:
    """Invalidate the combined team list after committed team updates."""
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await redis.delete(TEAMS_CACHE_KEY)
    except RedisError:
        # Database changes are already committed; cache failure is non-fatal.
        logger.exception("Failed to invalidate teams cache")
    finally:
        await redis.aclose()
