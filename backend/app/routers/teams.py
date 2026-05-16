from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models.team import Team
from ..schemas.team import TeamSchema
from ..models.team_stats import TeamStats
from ..schemas.team_stats import TeamStatsSchema

router = APIRouter(prefix="/teams", tags=["teams"])

@router.get("/", response_model=list[TeamSchema])
async def get_teams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Team).order_by(Team.abbr).offset(skip).limit(limit)
    )
    return result.scalars().all()

@router.get("/{abbr}", response_model=TeamSchema)
async def get_team(abbr: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.abbr == abbr))
    return result.scalar_one_or_none()

@router.get("/{abbr}/stats", response_model=TeamStatsSchema)
async def get_team_stats(abbr: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TeamStats).where(TeamStats.team_abbr == abbr)
    )
    return result.scalar_one_or_none()