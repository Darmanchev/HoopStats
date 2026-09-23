from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.team import Team
from ..clients.types import TeamProfileData


async def upsert_teams(
    db: AsyncSession,
    teams_data: list[TeamProfileData],
) -> int:
    """Upsert provider-owned team fields without erasing standings data."""
    count_new = 0
    for data in teams_data:
        result = await db.execute(
            select(Team).where(Team.abbr == data["abbr"])
        )
        team = result.scalar_one_or_none()
        if team is None:
            db.add(Team(
                abbr=data["abbr"],
                nba_id=None,
                balldontlie_id=data["balldontlie_id"],
                name=data["name"],
                city=data["city"],
                record="0-0",
                conference=data["conference"],
                conference_rank=None,
                last_ten=None,
                streak=None,
            ))
            count_new += 1
            continue

        team.balldontlie_id = data["balldontlie_id"]
        team.name = data["name"]
        team.city = data["city"]
        team.conference = data["conference"]

    return count_new
