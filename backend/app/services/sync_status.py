"""Keep source update timestamps separately from browser refresh timestamps."""
import json
import logging
import math
from datetime import datetime, timezone

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import settings

logger = logging.getLogger(__name__)
SYNC_STATUS_KEY = "sync:status:v1"
SYNC_SOURCES = (
    "sync_games", "sync_box_scores", "sync_schedule", "sync_injuries",
    "sync_teams", "sync_players", "sync_team_stats", "sync_historical_games",
    "sync_predictions",
)
PUBLIC_STATUS_FIELDS = (
    "state", "last_attempt", "last_success", "count", "started_at",
    "finished_at", "duration_seconds", "queued_at",
)


def retry_key(name: str) -> str:
    return f"sync:retry:{name}"


# Queue admission and status change happen together across API and scheduler processes.
ENQUEUE_RETRY = """
local raw = redis.call('HGET', KEYS[1], ARGV[1])
local ok, status = pcall(cjson.decode, raw or '{}')
if not ok or type(status) ~= 'table' then status = {} end
if status.state == 'running' then return -1 end
if redis.call('EXISTS', KEYS[2]) == 1 then return 0 end
status.state = 'queued'
status.queued_at = ARGV[2]
redis.call('SET', KEYS[2], 'queued')
redis.call('HSET', KEYS[1], ARGV[1], cjson.encode(status))
return 1
"""


def decode_status(raw) -> dict:
    try:
        values = json.loads(raw) if raw else {}
    except (ValueError, TypeError):
        values = {}
    if not isinstance(values, dict):
        values = {}
    status = {key: value for key, value in values.items() if key in PUBLIC_STATUS_FIELDS}
    if status.get('state') not in {'queued', 'running', 'success', 'failed'}:
        status['state'] = 'failed'
    for key in ('last_attempt', 'last_success', 'started_at', 'finished_at', 'queued_at'):
        if key in status and status[key] is not None:
            try:
                if datetime.fromisoformat(status[key]).tzinfo is None:
                    status.pop(key)
            except (ValueError, TypeError):
                status.pop(key)
    for key in ('duration_seconds', 'count'):
        value = status.get(key)
        if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
            status.pop(key)
    return status


async def record_sync_status(name: str, state: str, count=None, *, redis=None) -> None:
    owned = redis is None
    redis = redis or Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        raw = await redis.hget(SYNC_STATUS_KEY, name)
        previous = decode_status(raw)
        now = datetime.now(timezone.utc)
        timestamp = now.isoformat()
        previous["state"] = state
        if state == "queued":
            previous["queued_at"] = timestamp
        else:
            previous["last_attempt"] = timestamp
        if state == "running":
            previous.update(started_at=timestamp, finished_at=None, duration_seconds=None)
        elif state in ("success", "failed"):
            previous["finished_at"] = timestamp
            started = previous.get("started_at")
            if started:
                previous["duration_seconds"] = max(0, (now - datetime.fromisoformat(started)).total_seconds())
        if state == "success":
            previous.update(last_success=timestamp, count=count)
        # Never persist provider exception messages, which may contain credentials.
        await redis.hset(SYNC_STATUS_KEY, name, json.dumps(previous))
    except (RedisError, ValueError, TypeError):
        logger.warning("Unable to save synchronization status for %s", name)
    finally:
        if owned:
            await redis.aclose()
