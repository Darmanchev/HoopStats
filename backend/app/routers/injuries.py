from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models.injury import Injury
from ..schemas.injury import InjurySchema


router = APIRouter(prefix="/injuries", tags=["injuries"])

@router.get("/", response_model=list[InjurySchema])
async def get_injuries(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Injury))
    return result.scalars().all()

@router.get("/{team_abbr}", response_model=list[InjurySchema])
async def get_team_injuries(team_abbr: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Injury).where(Injury.team_abbr == team_abbr))
    return result.scalar_one_or_none()