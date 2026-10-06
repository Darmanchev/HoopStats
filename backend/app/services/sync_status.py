"""Keep source update timestamps separately from browser refresh timestamps."""
import json
import logging
from datetime import datetime, timezone

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import settings

logger = logging.getLogger(__name__)
SYNC_STATUS_KEY = "sync:status:v1"


async def record_sync_status(name: str, state: str, count=None) -> None:
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        raw = await redis.hget(SYNC_STATUS_KEY, name)
        previous = json.loads(raw) if raw else {}
        timestamp = datetime.now(timezone.utc).isoformat()
        previous.update(state=state, last_attempt=timestamp)
        if state == "success":
            previous.update(last_success=timestamp, count=count)
        # Don't persist provider exception messages, which may contain credentials.
        await redis.hset(SYNC_STATUS_KEY, name, json.dumps(previous))
    except (RedisError, ValueError, TypeError):
        logger.warning("Unable to save synchronization status for %s", name)
    finally:
        await redis.aclose()
