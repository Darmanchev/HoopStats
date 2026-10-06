"""Player game logs from imported official box scores, without provider calls."""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import Game, Player, PlayerGameStat
from ..services.player_identity import resolve_nba_id
from .players import _validate_season

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/{player_id}/games")
async def player_games(player_id: int, season: str | None = None, skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    _validate_season(season)
    player = await db.get(Player, player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    nba_id = resolve_nba_id(player.name, player.nba_id)
    coverage = {"identityResolved": nba_id is not None, "importedGames": 0, "note": "Only imported box scores are available; historical coverage may be incomplete."}
    if nba_id is None:
        return {"items": [], "total": 0, "coverage": coverage}
    query = select(PlayerGameStat, Game).join(Game, Game.id == PlayerGameStat.game_id).where(
        PlayerGameStat.nba_id == nba_id, Game.status == "final",
        (PlayerGameStat.team_abbr == Game.team1) | (PlayerGameStat.team_abbr == Game.team2), Game.team1.is_not(None), Game.team2.is_not(None))
    if season:
        query = query.where(Game.season == season)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    rows = (await db.execute(query.order_by(Game.date.desc(), Game.id).offset(skip).limit(limit))).all()
    items = []
    for stats, game in rows:
        away = stats.team_abbr == game.team1
        score, opponent_score = (game.score1, game.score2) if away else (game.score2, game.score1)
        result = None if score is None or opponent_score is None else "W" if score > opponent_score else "L"
        items.append({"gameId": game.id, "date": game.date, "teamAbbr": stats.team_abbr,
            "opponent": game.team2 if away else game.team1, "homeAway": ("Home" if stats.team_abbr == game.home_abbr else "Away") if game.home_abbr else "Unknown", "result": result,
            **{attr: getattr(stats, attr) for attr in ["points", "rebounds", "assists", "steals", "blocks", "minutes"]}})
    coverage["importedGames"] = total
    return {"items": items, "total": total, "coverage": coverage}
