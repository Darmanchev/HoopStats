from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload  # ← НОВОЕ
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
        select(Injury)
        .options(selectinload(Injury.team))  # ← eagerly load team
        .offset(skip)
        .limit(limit)
    )
    injuries = result.scalars().all()

    return [
        InjurySchema(
            id=i.id,
            team_abbr=i.team_abbr,
            player_name=i.player_name,
            position=i.position,
            injury=i.injury,
            status=i.status,
            team_name=i.team.name if i.team else None,  # ← из relationship
        )
        for i in injuries
    ]


@router.get("/{team_abbr}", response_model=list[InjurySchema])
async def get_team_injuries(
        team_abbr: str,
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Injury)
        .options(selectinload(Injury.team))
        .where(Injury.team_abbr == team_abbr)
        .offset(skip)
        .limit(limit)
    )
    injuries = result.scalars().all()

    return [
        InjurySchema(
            id=i.id,
            team_abbr=i.team_abbr,
            player_name=i.player_name,
            position=i.position,
            injury=i.injury,
            status=i.status,
            team_name=i.team.name if i.team else None,
        )
        for i in injuries
    ]