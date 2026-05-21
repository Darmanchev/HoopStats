from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload  # ← НОВОЕ
from ..database import get_db
from ..schemas.game import PastGameSchema, UpcomingGameSchema, GameBase
from ..models.game import Game

router = APIRouter(prefix="/games", tags=["games"])


@router.get("/upcoming", response_model=list[UpcomingGameSchema])
async def get_upcoming(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Game)
        .options(
            selectinload(Game.home_team),  # ← eagerly load home team
            selectinload(Game.away_team),  # ← eagerly load away team
        )
        .where(Game.score1 == None)
        .order_by(Game.date)
    )
    games = result.scalars().all()

    # КОНВЕРТИРУЕМ в UpcomingGameSchema с team info
    return [
        UpcomingGameSchema(
            id=g.id,
            team1=g.team1,
            team2=g.team2,
            date=g.date,
            time=g.time,
            venue=g.venue,
            season_type=g.season_type,
            season=g.season,
            is_today=g.is_today,
            win1=g.win1,
            prediction=g.prediction,
            home_team=g.home_team,  # ← автоматически из relationship
            away_team=g.away_team,  # ← автоматически из relationship
        )
        for g in games
    ]


@router.get("/today", response_model=list[UpcomingGameSchema])
async def get_today(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Game)
        .options(
            selectinload(Game.home_team),
            selectinload(Game.away_team),
        )
        .where(Game.is_today == True)
    )
    games = result.scalars().all()

    return [
        UpcomingGameSchema(
            id=g.id,
            team1=g.team1,
            team2=g.team2,
            date=g.date,
            time=g.time,
            venue=g.venue,
            season_type=g.season_type,
            season=g.season,
            is_today=g.is_today,
            win1=g.win1,
            prediction=g.prediction,
            home_team=g.home_team,
            away_team=g.away_team,
        )
        for g in games
    ]


@router.get("/past", response_model=list[PastGameSchema])
async def get_past(
        skip: int = Query(0, ge=0),
        limit: int = Query(1500, ge=1, le=5000),
        season: str | None = Query(None, description="например 2024-25"),
        season_type: str | None = Query(None, pattern="^(regular|playoffs)$"),
        db: AsyncSession = Depends(get_db),
):
    query = select(Game).where(Game.score1 != None)
    if season:
        query = query.where(Game.season == season)
    if season_type:
        query = query.where(Game.season_type == season_type)
    result = await db.execute(
        query.order_by(Game.date.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/seasons", response_model=list[str])
async def get_seasons(db: AsyncSession = Depends(get_db)):
    """Список сезонов, по которым есть игры — для выпадающего списка."""
    result = await db.execute(
        select(Game.season).distinct().order_by(Game.season.desc())
    )
    return [s for s in result.scalars().all() if s]


@router.get("/{id}", response_model=GameBase)
async def get_game(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Game)
        .options(
            selectinload(Game.home_team),
            selectinload(Game.away_team),
        )
        .where(Game.id == id)
    )
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    return UpcomingGameSchema(
        id=game.id,
        team1=game.team1,
        team2=game.team2,
        date=game.date,
        time=game.time,
        venue=game.venue,
        season_type=game.season_type,
        season=game.season,
        is_today=game.is_today,
        win1=game.win1,
        prediction=game.prediction,
        home_team=game.home_team,
        away_team=game.away_team,
    )