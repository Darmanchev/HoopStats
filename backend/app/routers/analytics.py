"""Аналитика лиги: Elo power rankings и лидеры по статистике."""
import asyncio
import json
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..cache import ELO_CACHE_KEY
from ..config import settings
from ..database import get_db
from ..models.game import Game
from ..models.player import Player
from ..schemas.player import PlayerSchema
from ..models.player_season_stat import PlayerSeasonStat
from ..routers.players import _season_player_schema
from ..services.clients.api_nba_normalizers import season_start_year
from ..services.repositories.player_seasons import list_player_seasons
from ..services.team_seasons import list_team_seasons, season_teams
from ..services.sync_status import SYNC_STATUS_KEY
from redis.exceptions import RedisError

router = APIRouter(prefix="/analytics", tags=["analytics"])

# минимум сыгранных игр, чтобы попасть в топы (отсев малой выборки)
LEADER_MIN_GAMES = 15
_RELEASE_LOCK = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
  return redis.call('DEL', KEYS[1])
end
return 0
"""


@router.get("/elo")
async def get_elo(request: Request, db: AsyncSession = Depends(get_db), season: str | None = None):
    """Power rankings — все команды, отсортированные по Elo-рейтингу."""
    from ..ml.features import build_state

    if season is not None:
        try:
            season_start_year(season)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    cache_key = f"{ELO_CACHE_KEY}:{season}" if season else ELO_CACHE_KEY
    lock_key = f"{cache_key}:lock"
    redis: Redis = request.app.state.redis
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    lock_token = secrets.token_urlsafe(24)
    has_lock = await redis.set(lock_key, lock_token, ex=30, nx=True)
    if not has_lock:
        # Another worker is rebuilding the shared cache. Do not duplicate the
        # expensive work; briefly wait for its result.
        for _ in range(30):
            await asyncio.sleep(0.1)
            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)
        raise HTTPException(
            status_code=503,
            detail="Analytics is being refreshed",
            headers={"Retry-After": "2"},
        )

    try:
        rows = (
            await db.execute(
                select(
                    Game.team1,
                    Game.team2,
                    Game.date,
                    Game.score1,
                    Game.score2,
                    Game.season,
                    Game.season_type,
                ).where(
                    Game.status == "final",
                    Game.season_type.in_(["regular", "playoffs"]),
                    Game.score1 != Game.score2,
                    *([Game.season <= season] if season else []),
                    Game.score1.is_not(None),
                    Game.score2.is_not(None),
                    Game.team1.is_not(None),
                    Game.team2.is_not(None),
                )
            )
        ).all()
        played = [
            {
                "team1": row.team1,
                "team2": row.team2,
                "date": row.date,
                "score1": row.score1,
                "score2": row.score2,
                "season": row.season,
                "season_type": row.season_type,
            }
            for row in rows
        ]
        if season and not any(g["season"] == season for g in played):
            return []
        state = await asyncio.to_thread(build_state, played)
        ranking = sorted(state.elo.items(), key=lambda kv: kv[1], reverse=True)
        response = [
            {"teamAbbr": abbr, "elo": round(elo, 1)}
            for abbr, elo in ranking
        ]
        await redis.set(
            cache_key,
            json.dumps(response),
            ex=settings.elo_cache_ttl_seconds,
        )
        return response
    finally:
        await redis.eval(_RELEASE_LOCK, 1, lock_key, lock_token)


@router.get("/leaders", response_model=dict[str, list[PlayerSchema]])
async def get_leaders(season: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    """Лидеры лиги — топ-5 игроков в каждой ключевой категории."""
    if season is None:
        seasons = await list_player_seasons(db)
        season = seasons[0] if seasons else None
    if season is not None:
        try:
            season_start_year(season)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    players = []
    if season:
        result = await db.execute(select(Player, PlayerSeasonStat)
            .join(PlayerSeasonStat, PlayerSeasonStat.player_id == Player.id)
            .where(PlayerSeasonStat.season == season, PlayerSeasonStat.games_played >= LEADER_MIN_GAMES))
        players = [_season_player_schema(player, stats) for player, stats in result.all()]

    def top(attr: str, n: int = 5):
        return sorted(players, key=lambda p: getattr(p, attr), reverse=True)[:n]

    return {
        "pts": top("pts"),
        "reb": top("reb"),
        "ast": top("ast"),
        "fgPct": top("fg_pct"),
    }


@router.get("/dashboard")
async def get_dashboard_season(season: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    player_seasons = await list_player_seasons(db)
    team_seasons = await list_team_seasons(db)
    game_seasons = list((await db.execute(select(Game.season).distinct().order_by(Game.season.desc()))).scalars().all())
    seasons = sorted(set(player_seasons + team_seasons + game_seasons), reverse=True)
    complete_seasons = sorted(set(player_seasons).intersection(team_seasons), reverse=True)
    default_seasons = complete_seasons or player_seasons or team_seasons or game_seasons
    selected = season or (default_seasons[0] if default_seasons else None)
    if selected:
        try:
            season_start_year(selected)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    leaders = await get_leaders(season=selected, db=db)
    teams = await season_teams(db, selected) if selected in team_seasons else []
    return {
        "season": selected, "seasons": seasons,
        "teams": [team.model_dump(by_alias=True) for team in teams],
        "leaders": leaders,
        "teamsAvailable": selected in team_seasons,
        "playersAvailable": selected in player_seasons,
    }


@router.get("/sync-status")
async def get_sync_status(request: Request):
    try:
        rows = await request.app.state.redis.hgetall(SYNC_STATUS_KEY)
        return {name: json.loads(value) for name, value in rows.items()}
    except (RedisError, ValueError, TypeError):
        raise HTTPException(status_code=503, detail="Source update status unavailable")


@router.get("/model-performance")
async def get_model_performance(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    from ..ml.predict import MODEL_PATH
    from ..ml.evaluation import read_report
    report = await asyncio.to_thread(read_report, MODEL_PATH.with_name("evaluation.json"))
    if report is None:
        return {"available": False, "reason": "Model evaluation unavailable", "games": [], "total": 0}
    games = report["games"]
    return {**report, "games": games[skip:skip + limit], "total": len(games)}
