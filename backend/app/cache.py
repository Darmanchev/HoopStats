"""Shared cache keys and invalidation helpers."""

import json
import logging
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from .config import settings

logger = logging.getLogger(__name__)

ELO_CACHE_KEY = "analytics:elo:v1"
ELO_LOCK_KEY = f"{ELO_CACHE_KEY}:lock"
TEAMS_CACHE_KEY = "api:teams:v1"
TODAY_GAMES_CACHE_KEY = "api:games:today:v1"


def box_score_cache_key(game_id: str) -> str:
    return f"api:game:{game_id}:boxscore:v1"


async def get_cached_json(redis: Redis, key: str) -> Any | None:
    """Read JSON from Redis, falling back to the database on any cache error."""
    try:
        raw = await redis.get(key)
        return json.loads(raw) if raw is not None else None
    except (RedisError, json.JSONDecodeError, TypeError):
        logger.exception("Failed to read cache key %s", key)
        return None


async def set_cached_json(
    redis: Redis,
    key: str,
    value: Any,
    *,
    ttl: int,
) -> None:
    """Write JSON to Redis without failing a successful API response."""
    try:
        await redis.set(key, json.dumps(value), ex=ttl)
    except (RedisError, TypeError):
        logger.exception("Failed to write cache key %s", key)


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


async def invalidate_live_caches(game_ids: list[str]) -> None:
    """Invalidate today's games and affected box scores after commit."""
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    keys = [TODAY_GAMES_CACHE_KEY]
    keys.extend(box_score_cache_key(game_id) for game_id in game_ids)
    try:
        await redis.delete(*keys)
    except RedisError:
        logger.exception("Failed to invalidate live game caches")
    finally:
        await redis.aclose()
