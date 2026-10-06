from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, extract, cast, Date, Integer
from datetime import date as DateValue
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


def validate_season(season: str | None) -> None:
    if season:
        from ..services.clients.api_nba_normalizers import season_start_year
        try:
            season_start_year(season)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/")
async def list_games(
    season: str | None = None,
    season_type: str | None = Query(None, pattern="^(preseason|regular|playoffs)$"),
    status: str | None = Query(None, pattern="^(scheduled|live|final)$"),
    team: str | None = Query(None, max_length=200, pattern=r"^[A-Za-z]{2,5}(,[A-Za-z]{2,5})*$"),
    date_from: DateValue | None = None,
    date_to: DateValue | None = None,
    weekday: int | None = Query(None, ge=0, le=6),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=250),
    db: AsyncSession = Depends(get_db),
):
    validate_season(season)
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="Start date must precede end date")
    query = select(Game).where(Game.team1.is_not(None), Game.team2.is_not(None))
    for column, value in [(Game.season, season), (Game.season_type, season_type), (Game.status, status)]:
        if value is not None:
            query = query.where(column == value)
    if team:
        teams = team.upper().split(",")
        query = query.where(or_(Game.team1.in_(teams), Game.team2.in_(teams)))
    if date_from:
        query = query.where(Game.date >= date_from.isoformat())
    if date_to:
        query = query.where(Game.date <= date_to.isoformat())
    if weekday is not None:
        # ISO date strings remain portable across SQLite tests and PostgreSQL.
        dialect = db.bind.dialect.name
        day = (
            cast(func.strftime("%w", Game.date), Integer)
            if dialect == "sqlite" else extract("dow", cast(Game.date, Date))
        )
        query = query.where(day == weekday)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    rows = (await db.execute(query.options(selectinload(Game.home_team), selectinload(Game.away_team))
        .order_by(Game.date.desc(), Game.start_time.asc().nullslast(), Game.id.asc()).offset(skip).limit(limit))).scalars().all()
    return {"items": [GameDetailSchema.model_validate(g).model_dump(by_alias=True, mode="json") for g in rows], "total": total}


@router.get("/months", response_model=list[str])
async def get_months(season: str | None = None, db: AsyncSession = Depends(get_db)):
    validate_season(season)
    month = func.substr(Game.date, 1, 7)
    query = select(month).distinct().where(Game.team1.is_not(None), Game.team2.is_not(None))
    if season:
        query = query.where(Game.season == season)
    return (await db.execute(query.order_by(month))).scalars().all()


@router.get("/upcoming", response_model=list[UpcomingGameSchema])
async def get_upcoming(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Game)
        .options(
            selectinload(Game.home_team),  # ← eagerly load home team
            selectinload(Game.away_team),  # ← eagerly load away team
        )
        .where(Game.status == "scheduled")
        .order_by(Game.start_time.asc().nullslast(), Game.date, Game.time)
    )
    games = result.scalars().all()

    # КОНВЕРТИРУЕМ в UpcomingGameSchema с team info
    return [
        UpcomingGameSchema(
            id=g.id,
            team1=g.team1,
            team2=g.team2,
            home_abbr=g.home_abbr,
            date=g.date,
            time=g.time,
            venue=g.venue,
            season_type=g.season_type,
            season=g.season,
            is_today=g.is_today,
            win1=g.win1,
            prediction=g.prediction,
            start_time=g.start_time,
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
        .order_by(Game.start_time.asc().nullslast(), Game.date, Game.time)
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
        season_type: str | None = Query(None, pattern="^(preseason|regular|playoffs)$"),
        db: AsyncSession = Depends(get_db),
):
    query = select(Game).where(Game.status == "final")
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
        home_abbr=game.home_abbr,
        date=game.date,
        time=game.time,
        venue=game.venue,
        season_type=game.season_type,
        season=game.season,
        is_today=game.is_today,
        win1=game.win1,
        prediction=game.prediction,
        start_time=game.start_time,
        status=game.status,
        status_text=game.status_text,
        period=game.period,
        clock=game.clock,
        period_scores=game.period_scores,
        score1=game.score1,
        score2=game.score2,
        home_team=game.home_team,
        away_team=game.away_team,
    )
