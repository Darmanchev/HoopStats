import logging
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.game import Game
from ..clients.types import GameData

logger = logging.getLogger(__name__)


def _parse_start_time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        logger.warning("Invalid game start time %r", value)
        return None


async def reset_today_flag(db: AsyncSession) -> None:
    """Clear the current-day marker only after provider validation succeeds."""
    await db.execute(update(Game).values(is_today=False))


async def upsert_games(
    db: AsyncSession,
    games_data: list[GameData],
    *,
    today: str | None = None,
) -> list[str]:
    """Insert or update normalized games without committing the transaction."""
    affected_ids: list[str] = []
    for data in games_data:
        result = await db.execute(
            select(Game).where(Game.id == data["game_id"])
        )
        game = result.scalar_one_or_none()
        is_today = data["date"] == today if today is not None else False
        start_time = _parse_start_time(data["start_time"])

        if game is None:
            db.add(Game(
                id=data["game_id"],
                team1=data["away_abbr"],
                team2=data["home_abbr"],
                date=data["date"],
                time=data["status_text"],
                venue=data["venue"],
                is_today=is_today,
                season_type=data["season_type"],
                season=data["season"],
                score1=data["away_score"],
                score2=data["home_score"],
                status=data["status"],
                status_text=data["status_text"],
                period=data["period"],
                clock=data["clock"],
                start_time=start_time,
            ))
            affected_ids.append(data["game_id"])
            continue

        game.team1 = data["away_abbr"]
        game.team2 = data["home_abbr"]
        game.date = data["date"]
        game.time = data["status_text"]
        game.venue = data["venue"]
        game.status = data["status"]
        game.status_text = data["status_text"]
        game.period = data["period"]
        game.clock = data["clock"]
        game.start_time = start_time
        game.season = data["season"]
        game.season_type = data["season_type"]
        if today is not None:
            game.is_today = is_today
        if data["away_score"] is not None and data["home_score"] is not None:
            game.score1 = data["away_score"]
            game.score2 = data["home_score"]
        affected_ids.append(data["game_id"])

    return affected_ids
