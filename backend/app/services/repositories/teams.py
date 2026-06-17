import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...models.team import Team

logger = logging.getLogger(__name__)


async def upsert_teams(
    db: AsyncSession,
    teams_data: list[dict],
    records: dict[int, str],
) -> int:
    """Создаёт или обновляет команды в БД.
    
    teams_data — список словарей от nba_api: {"id", "abbreviation", "nickname", "city"}
    records — словарь nba_id → record ("52-28")
    
    Возвращает количество НОВЫХ команд.
    """
    count_new = 0
    for t in teams_data:
        abbr = t["abbreviation"]
        record = records.get(int(t["id"]), "0-0")

        existing = await db.execute(select(Team).where(Team.abbr == abbr))
        team = existing.scalar_one_or_none()

        if not team:
            db.add(Team(
                abbr=abbr,
                nba_id=t["id"],
                name=t["nickname"],
                city=t["city"],
                record=record,
            ))
            count_new += 1
        else:
            team.record = record
            team.nba_id = t["id"]

    await db.commit()
    return count_new
