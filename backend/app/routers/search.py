"""Bounded, escaped global search over locally imported data."""
from urllib.parse import quote
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from ..database import get_db
from ..models import Player, Team, Game, PlayerSeasonStat

router = APIRouter(tags=["search"])


@router.get("/search")
async def search(q: str = Query(..., max_length=100), limit: int = Query(5, ge=1, le=10), db: AsyncSession = Depends(get_db)):
    term = q.strip()
    empty = {"players": [], "teams": [], "games": []}
    if len(term) < 2:
        return empty
    pattern = "%" + term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    def matches(column):
        return column.ilike(pattern, escape="\\")
    players = (await db.execute(select(Player).where(matches(Player.name)).order_by(Player.name, Player.id).limit(limit))).scalars().all()
    latest_seasons = dict((await db.execute(select(PlayerSeasonStat.player_id, func.max(PlayerSeasonStat.season)).where(PlayerSeasonStat.player_id.in_([p.id for p in players])).group_by(PlayerSeasonStat.player_id))).all()) if players else {}
    teams = (await db.execute(select(Team).where(or_(matches(Team.abbr), matches(Team.city), matches(Team.name))).order_by(Team.abbr).limit(limit))).scalars().all()
    away, home = aliased(Team), aliased(Team)
    query = select(Game).join(away, away.abbr == Game.team1).join(home, home.abbr == Game.team2).where(or_(
        matches(Game.date), matches(Game.team1), matches(Game.team2), matches(away.city), matches(away.name), matches(home.city), matches(home.name)))
    games = (await db.execute(query.order_by(Game.date.desc(), Game.id).limit(limit))).scalars().all()
    return {
        "players": [{"id": str(p.id), "label": p.name, "url": f"/players/{p.id}" + (f"?season={latest_seasons[p.id]}" if p.id in latest_seasons else "")} for p in players],
        "teams": [{"id": t.abbr, "label": f"{t.city} {t.name}", "url": f"/teams/{t.abbr}"} for t in teams],
        "games": [{"id": g.id, "label": f"{g.team1} at {g.team2} · {g.date}", "url": f"/match/{quote(g.id, safe='')}"} for g in games],
    }
