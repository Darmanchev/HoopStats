from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ..cache import (
    TODAY_GAMES_CACHE_KEY,
    box_score_cache_key,
    get_cached_json,
    set_cached_json,
)
from ..config import settings
from ..database import get_db
from ..schemas.game import (
    GameDetailSchema,
    LiveGameSchema,
    PastGameSchema,
    UpcomingGameSchema,
)
from ..schemas.player_game_stat import PlayerGameStatSchema
from ..models.game import Game
from ..models.player_game_stat import PlayerGameStat

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


@router.get("/today", response_model=list[LiveGameSchema])
async def get_today(request: Request, db: AsyncSession = Depends(get_db)):
    cached = await get_cached_json(
        request.app.state.redis,
        TODAY_GAMES_CACHE_KEY,
    )
    if cached is not None:
        return cached

    result = await db.execute(
        select(Game)
        .options(
            selectinload(Game.home_team),
            selectinload(Game.away_team),
        )
        .where(Game.is_today == True)
        .order_by(Game.date, Game.time)
    )
    payload = [
        LiveGameSchema.model_validate(game).model_dump(
            by_alias=True,
            mode="json",
        )
        for game in result.scalars().all()
    ]
    await set_cached_json(
        request.app.state.redis,
        TODAY_GAMES_CACHE_KEY,
        payload,
        ttl=settings.live_cache_ttl_seconds,
    )
    return payload


@router.get("/past", response_model=list[PastGameSchema])
async def get_past(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=250),
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


@router.get("/{id}/boxscore", response_model=list[PlayerGameStatSchema])
async def get_boxscore(
    id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    game_result = await db.execute(select(Game).where(Game.id == id))
    if game_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Game not found")

    key = box_score_cache_key(id)
    cached = await get_cached_json(request.app.state.redis, key)
    if cached is not None:
        return cached

    result = await db.execute(
        select(PlayerGameStat)
        .where(PlayerGameStat.game_id == id)
        .order_by(PlayerGameStat.points.desc(), PlayerGameStat.name.asc())
    )
    payload = [
        PlayerGameStatSchema.model_validate(row).model_dump(
            by_alias=True,
            mode="json",
        )
        for row in result.scalars().all()
    ]
    await set_cached_json(
        request.app.state.redis,
        key,
        payload,
        ttl=settings.live_cache_ttl_seconds,
    )
    return payload


@router.get("/{id}", response_model=GameDetailSchema)
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

    return GameDetailSchema(
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
        status=game.status,
        status_text=game.status_text,
        period=game.period,
        clock=game.clock,
        score1=game.score1,
        score2=game.score2,
        home_team=game.home_team,
        away_team=game.away_team,
    )
