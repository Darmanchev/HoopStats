from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.player import Player
from ..models.player_season_stat import PlayerSeasonStat
from ..models.team import Team
from ..schemas.player import PlayerDetailSchema, PlayerSchema
from ..services.clients.api_nba_normalizers import season_start_year
from ..services.repositories.player_seasons import list_player_seasons


router = APIRouter(prefix="/players", tags=["players"])


def _validate_season(season: str | None) -> None:
    if season is None:
        return
    try:
        season_start_year(season)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _season_player_schema(
    player: Player,
    stats: PlayerSeasonStat,
) -> PlayerSchema:
    return PlayerSchema(
        id=player.id,
        nba_id=player.nba_id,
        balldontlie_id=player.balldontlie_id,
        api_nba_id=player.api_nba_id,
        season=stats.season,
        name=player.name,
        team_abbr=stats.primary_team_abbr,
        position=player.position,
        jersey_number=player.jersey_number,
        games_played=stats.games_played,
        pts=stats.pts,
        reb=stats.reb,
        ast=stats.ast,
        stl=stats.stl,
        blk=stats.blk,
        fg_pct=stats.fg_pct,
        fg3_pct=stats.fg3_pct,
        ft_pct=stats.ft_pct,
        mins=stats.mins,
        recent_games=stats.recent_games,
    )


@router.get("/", response_model=list[PlayerSchema])
async def get_players(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sort_by: str = Query("pts", pattern="^(pts|reb|ast|games_played|name)$"),
    team: str | None = None,
    position: str | None = None,
    min_games: int = Query(0, ge=0),
    season: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    db: AsyncSession = Depends(get_db),
):
    _validate_season(season)
    if season is None:
        query = select(Player).where(Player.games_played >= min_games)
        if team:
            query = query.where(Player.team_abbr == team.upper())
        if position:
            query = query.where(Player.position == position.upper())
        sort_map = {
            "pts": Player.pts.desc(),
            "reb": Player.reb.desc(),
            "ast": Player.ast.desc(),
            "games_played": Player.games_played.desc(),
            "name": Player.name.asc(),
        }
        query = (
            query.order_by(sort_map.get(sort_by, Player.pts.desc()))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    query = (
        select(Player, PlayerSeasonStat)
        .join(PlayerSeasonStat, PlayerSeasonStat.player_id == Player.id)
        .where(
            PlayerSeasonStat.season == season,
            PlayerSeasonStat.games_played >= min_games,
        )
    )
    if team:
        query = query.where(PlayerSeasonStat.primary_team_abbr == team.upper())
    if position:
        query = query.where(Player.position == position.upper())
    season_sort_map = {
        "pts": PlayerSeasonStat.pts.desc(),
        "reb": PlayerSeasonStat.reb.desc(),
        "ast": PlayerSeasonStat.ast.desc(),
        "games_played": PlayerSeasonStat.games_played.desc(),
        "name": Player.name.asc(),
    }
    query = (
        query.order_by(season_sort_map.get(sort_by, PlayerSeasonStat.pts.desc()))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return [
        _season_player_schema(player, stats)
        for player, stats in result.all()
    ]


@router.get("/seasons", response_model=list[str])
async def get_player_seasons(
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    return await list_player_seasons(db)


@router.get("/{player_id}", response_model=PlayerDetailSchema)
async def get_player(
    player_id: int,
    season: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    db: AsyncSession = Depends(get_db),
):
    _validate_season(season)
    if season is not None:
        result = await db.execute(
            select(Player, PlayerSeasonStat, Team)
            .join(PlayerSeasonStat, PlayerSeasonStat.player_id == Player.id)
            .join(Team, Team.abbr == PlayerSeasonStat.primary_team_abbr)
            .where(
                Player.id == player_id,
                PlayerSeasonStat.season == season,
            )
        )
        record = result.one_or_none()
        if record is None:
            raise HTTPException(
                status_code=404,
                detail="Player season not found",
            )
        player, stats, team = record
        return PlayerDetailSchema(
            **_season_player_schema(player, stats).model_dump(),
            team_name=team.name,
            team_city=team.city,
        )

    result = await db.execute(
        select(Player)
        .options(selectinload(Player.team))
        .where(Player.id == player_id)
    )
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return PlayerDetailSchema(
        id=player.id,
        nba_id=player.nba_id,
        balldontlie_id=player.balldontlie_id,
        api_nba_id=player.api_nba_id,
        name=player.name,
        team_abbr=player.team_abbr,
        position=player.position,
        jersey_number=player.jersey_number,
        games_played=player.games_played,
        pts=player.pts,
        reb=player.reb,
        ast=player.ast,
        stl=player.stl,
        blk=player.blk,
        fg_pct=player.fg_pct,
        fg3_pct=player.fg3_pct,
        ft_pct=player.ft_pct,
        mins=player.mins,
        recent_games=player.recent_games,
        team_name=player.team.name if player.team else None,
        team_city=player.team.city if player.team else None,
    )
