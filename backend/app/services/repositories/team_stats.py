import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...models.team_stats import TeamStats

logger = logging.getLogger(__name__)


async def upsert_team_stats(
    db: AsyncSession,
    team_abbr: str,
    form: list[str],
    last_scores: list[int],
) -> None:
    """Создаёт или обновляет статистику формы команды."""
    existing = await db.execute(
        select(TeamStats).where(TeamStats.team_abbr == team_abbr)
    )
    stats = existing.scalar_one_or_none()

    if not stats:
        db.add(TeamStats(
            team_abbr=team_abbr,
            form=form[:5],
            last_scores=last_scores,
        ))
    else:
        stats.form = form[:5]
        stats.last_scores = last_scores
