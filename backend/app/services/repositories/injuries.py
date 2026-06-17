import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...models.injury import Injury
from ..utils import TEAM_NAME_TO_ABBR

logger = logging.getLogger(__name__)


async def replace_all_injuries(
    db: AsyncSession,
    teams_injuries: list[dict],
) -> int:
    """Полностью заменяет все травмы в БД на новые данные из ESPN.
    
    teams_injuries — список от ESPN API:
    [{"displayName": "Atlanta Hawks", "injuries": [...]}, ...]
    
    Возвращает количество добавленных записей.
    """
    # Очищаем старые травмы
    result = await db.execute(select(Injury))
    existing = result.scalars().all()
    for inj in existing:
        await db.delete(inj)
    await db.commit()

    count = 0
    for team_entry in teams_injuries:
        team_name = team_entry.get("displayName", "")
        team_abbr = TEAM_NAME_TO_ABBR.get(team_name, "UNK")
        injuries = team_entry.get("injuries", [])

        for inj in injuries:
            athlete = inj.get("athlete", {})
            details = inj.get("details", {})

            status = inj.get("status", "Out")
            if status == "Day-To-Day":
                status = "Day-to-Day"
            elif status not in ("Out", "Questionable", "Doubtful"):
                status = "Out"

            injury_type = details.get("type", "Not Specified")
            injury_detail = details.get("detail", "")
            injury_desc = f"{injury_type} {injury_detail}".strip() if injury_detail else injury_type

            player_name = athlete.get("displayName", "Unknown")
            position = athlete.get("position", {})
            pos_abbr = position.get("abbreviation", "N/A")

            try:
                db.add(Injury(
                    team_abbr=team_abbr,
                    player_name=player_name,
                    position=pos_abbr,
                    injury=injury_desc[:100],
                    status=status,
                ))
                count += 1
            except Exception as e:
                logger.error("Ошибка при сохранении %s: %s", player_name, e)

    await db.commit()
    return count
