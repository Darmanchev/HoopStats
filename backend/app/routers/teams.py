from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models.team import Team
from ..schemas.team import TeamSchema

router = APIRouter(prefix="/teams", tags=["teams"])

@router.get("/", response_model=list[TeamSchema])
async def get_teams(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team))
    return result.scalars().all()

@router.get("/{abbr}", response_model=TeamSchema)
async def get_team(abbr: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.abbr == abbr))
    return result.scalar_one_or_none()
