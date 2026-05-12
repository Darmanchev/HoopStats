from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..schemas.game import PastGameSchema, UpcomingGameSchema, GameBase
from ..models.game import Game


router = APIRouter(prefix="/games", tags=["games"])

@router.get("/upcoming", response_model=list[UpcomingGameSchema])
async def get_upcoming(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.score1 == None))
    return result.scalars().all()

@router.get("/today", response_model=list[UpcomingGameSchema])
async def get_today(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.is_today == True))
    return result.scalars().all()

@router.get("/past", response_model=list[PastGameSchema])
async def get_past(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.score1 != None))
    return result.scalars().all()

@router.get("/{id}", response_model=GameBase)
async def get_game(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == id))
    return result.scalar_one_or_none()

