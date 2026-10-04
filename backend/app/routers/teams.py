from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from ..cache import TEAMS_CACHE_KEY, get_cached_json, set_cached_json
from ..config import settings
from ..database import get_db
from ..models.player import Player
from ..models.player_season_stat import PlayerSeasonStat
from ..models.team import Team
from ..schemas.team import TeamDetailSchema, TeamWithStatsSchema
from ..models.team_stats import TeamStats
from ..schemas.team_stats import TeamStatsSchema
from ..services.team_seasons import list_team_seasons, season_teams
from ..services.clients.api_nba_normalizers import season_start_year

router = APIRouter(prefix="/teams", tags=["teams"])


def validate_season(season: str) -> None:
    try:
        season_start_year(season)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/seasons", response_model=list[str])
async def get_team_seasons(db: AsyncSession = Depends(get_db)):
    return await list_team_seasons(db)


@router.get("/", response_model=list[TeamWithStatsSchema])
async def get_teams(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    season: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if season is not None:
        validate_season(season)
        if season not in await list_team_seasons(db):
            raise HTTPException(status_code=404, detail="No imported team games for this season")
        return (await season_teams(db, season))[skip:skip + limit]
    cacheable = skip == 0 and limit == 100
    if cacheable:
        cached = await get_cached_json(request.app.state.redis, TEAMS_CACHE_KEY)
        if cached is not None:
            return cached

    result = await db.execute(
        select(Team)
        .options(selectinload(Team.stats))
        .order_by(Team.abbr)
        .offset(skip)
        .limit(limit)
    )
    response = [
        TeamWithStatsSchema.model_validate(team).model_dump(
            by_alias=True,
            mode="json",
        )
        for team in result.scalars().all()
    ]
    if cacheable:
        await set_cached_json(
            request.app.state.redis,
            TEAMS_CACHE_KEY,
            response,
            ttl=settings.teams_cache_ttl_seconds,
        )
    return response


@router.get("/{abbr}", response_model=TeamDetailSchema)
async def get_team(abbr: str, season: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    if season is not None:
        validate_season(season)
        if season not in await list_team_seasons(db):
            raise HTTPException(status_code=404, detail="No imported team games for this season")
        for team in await season_teams(db, season):
            if team.abbr == abbr.upper():
                count = await db.scalar(select(func.count(PlayerSeasonStat.player_id)).where(
                    PlayerSeasonStat.season == season,
                    PlayerSeasonStat.primary_team_abbr == team.abbr,
                ))
                return TeamDetailSchema(**team.model_dump(), players_count=count or 0)
        raise HTTPException(status_code=404, detail="Team not found")
    result = await db.execute(
        select(Team)
        .options(selectinload(Team.stats))
        .where(Team.abbr == abbr)
    )
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    players_count = await db.execute(
        select(func.count(Player.id)).where(Player.team_abbr == abbr)
    )
    return TeamDetailSchema(
        abbr=team.abbr,
        name=team.name,
        city=team.city,
        record=team.record,
        conference=team.conference,
        conference_rank=team.conference_rank,
        last_ten=team.last_ten,
        streak=team.streak,
        stats=team.stats,
        players_count=players_count.scalar_one(),
    )
@router.get("/{abbr}/stats", response_model=TeamStatsSchema)
async def get_team_stats(abbr: str, season: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    if season is not None:
        validate_season(season)
        if season not in await list_team_seasons(db):
            raise HTTPException(status_code=404, detail="No imported team games for this season")
        for team in await season_teams(db, season):
            if team.abbr == abbr.upper():
                return team.stats
        raise HTTPException(status_code=404, detail="Team not found")
    result = await db.execute(
        select(TeamStats).where(TeamStats.team_abbr == abbr)
    )
    stats = result.scalar_one_or_none()
    if not stats:
        raise HTTPException(status_code=404, detail="Team stats not found")
    return stats
