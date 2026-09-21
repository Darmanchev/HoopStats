import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...models.team import Team
from ..clients.types import StandingData

logger = logging.getLogger(__name__)


async def upsert_teams(
    db: AsyncSession,
    teams_data: list[dict],
    records: dict[int, StandingData],
) -> int:
    """Создаёт или обновляет команды в БД.
    
    teams_data — список словарей от nba_api: {"id", "abbreviation", "nickname", "city"}
    records — словарь nba_id → record ("52-28")
    
    Возвращает количество НОВЫХ команд.
    """
    count_new = 0
    for t in teams_data:
        abbr = t["abbreviation"]
        standing = records.get(int(t["id"]))

        existing = await db.execute(select(Team).where(Team.abbr == abbr))
        team = existing.scalar_one_or_none()

        if not team:
            db.add(Team(
                abbr=abbr,
                nba_id=t["id"],
                name=t["nickname"],
                city=t["city"],
                record=standing["record"] if standing else "0-0",
                conference=standing["conference"] if standing else None,
                conference_rank=(
                    standing["conference_rank"] if standing else None
                ),
                last_ten=standing["last_ten"] if standing else None,
                streak=standing["streak"] if standing else None,
            ))
            count_new += 1
        else:
            team.nba_id = t["id"]
            if standing:
                team.record = standing["record"]
                team.conference = standing["conference"]
                team.conference_rank = standing["conference_rank"]
                team.last_ten = standing["last_ten"]
                team.streak = standing["streak"]

    await db.commit()
    return count_new
