import json

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from ..cache import TEAMS_CACHE_KEY
from ..config import settings
from ..database import get_db
from ..models.player import Player
from ..models.team import Team
from ..schemas.team import TeamDetailSchema, TeamWithStatsSchema
from ..models.team_stats import TeamStats
from ..schemas.team_stats import TeamStatsSchema

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/", response_model=list[TeamWithStatsSchema])
async def get_teams(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    redis: Redis = request.app.state.redis
    cacheable = skip == 0 and limit == 100
    if cacheable:
        cached = await redis.get(TEAMS_CACHE_KEY)
        if cached:
            return json.loads(cached)

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
        await redis.set(
            TEAMS_CACHE_KEY,
            json.dumps(response),
            ex=settings.teams_cache_ttl_seconds,
        )
    return response


@router.get("/{abbr}", response_model=TeamDetailSchema)
async def get_team(abbr: str, db: AsyncSession = Depends(get_db)):
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
        stats=team.stats,
        players_count=players_count.scalar_one(),
    )
@router.get("/{abbr}/stats", response_model=TeamStatsSchema)
async def get_team_stats(abbr: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TeamStats).where(TeamStats.team_abbr == abbr)
    )
    stats = result.scalar_one_or_none()
    if not stats:
        raise HTTPException(status_code=404, detail="Team stats not found")
    return stats
