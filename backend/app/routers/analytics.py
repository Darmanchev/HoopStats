"""Аналитика лиги: Elo power rankings и лидеры по статистике."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.game import Game
from ..models.player import Player
from ..schemas.player import PlayerSchema

router = APIRouter(prefix="/analytics", tags=["analytics"])

# минимум сыгранных игр, чтобы попасть в топы (отсев малой выборки)
LEADER_MIN_GAMES = 15


@router.get("/elo")
async def get_elo(db: AsyncSession = Depends(get_db)):
    """Power rankings — все команды, отсортированные по Elo-рейтингу."""
    from ..ml.features import build_state

    rows = (await db.execute(select(Game))).scalars().all()
    played = [
        {
            "team1": g.team1, "team2": g.team2, "date": g.date,
            "score1": g.score1, "score2": g.score2, "season": g.season,
        }
        for g in rows
        if g.score1 is not None and g.score2 is not None
    ]
    state = build_state(played)
    ranking = sorted(state.elo.items(), key=lambda kv: kv[1], reverse=True)
    return [{"teamAbbr": abbr, "elo": round(elo, 1)} for abbr, elo in ranking]


@router.get("/leaders", response_model=dict[str, list[PlayerSchema]])
async def get_leaders(db: AsyncSession = Depends(get_db)):
    """Лидеры лиги — топ-5 игроков в каждой ключевой категории."""
    result = await db.execute(
        select(Player).where(Player.games_played >= LEADER_MIN_GAMES)
    )
    players = list(result.scalars().all())

    def top(attr: str, n: int = 5):
        return sorted(players, key=lambda p: getattr(p, attr), reverse=True)[:n]

    return {
        "pts": top("pts"),
        "reb": top("reb"),
        "ast": top("ast"),
        "fgPct": top("fg_pct"),
    }
