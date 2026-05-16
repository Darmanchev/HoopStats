from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models.injury import Injury
from ..schemas.injury import InjurySchema


router = APIRouter(prefix="/injuries", tags=["injuries"])

@router.get("/", response_model=list[InjurySchema])
async def get_injuries(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Injury).offset(skip).limit(limit)
    )
    return result.scalars().all()

@router.get("/{team_abbr}", response_model=list[InjurySchema])
async def get_team_injuries(
    team_abbr: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Injury).where(Injury.team_abbr == team_abbr).offset(skip).limit(limit)
    )
    return result.scalars().all()