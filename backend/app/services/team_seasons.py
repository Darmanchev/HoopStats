"""Derive season records from imported, completed regular-season games."""
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.models.team import Team
from app.schemas.team import TeamWithStatsSchema
from app.schemas.team_stats import TeamStatsSchema


def completed_regular_games():
    return (
        Game.status == "final", Game.season_type == "regular",
        Game.score1.is_not(None), Game.score2.is_not(None),
        Game.score1 != Game.score2,
        Game.team1.is_not(None), Game.team2.is_not(None),
    )


async def list_team_seasons(db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(Game.season).where(*completed_regular_games())
        .distinct().order_by(Game.season.desc())
    )
    return list(result.scalars().all())


async def season_teams(db: AsyncSession, season: str) -> list[TeamWithStatsSchema]:
    teams = (await db.execute(select(Team).order_by(Team.abbr))).scalars().all()
    games = (await db.execute(
        select(Game).where(Game.season == season, *completed_regular_games())
        .order_by(Game.date.desc(), Game.start_time.desc(), Game.id.desc())
    )).scalars().all()
    results = defaultdict(list)
    for game in games:
        results[game.team1].append(("W" if game.score1 > game.score2 else "L", game.score1))
        results[game.team2].append(("W" if game.score2 > game.score1 else "L", game.score2))
    response = []
    for team in teams:
        appearances = results[team.abbr]
        wins = sum(outcome == "W" for outcome, _ in appearances)
        recent = appearances[:10]
        recent_wins = sum(outcome == "W" for outcome, _ in recent)
        streak = None
        if appearances:
            outcome = appearances[0][0]
            length = 0
            for result, _ in appearances:
                if result != outcome:
                    break
                length += 1
            streak = f"{outcome}{length}"
        response.append(TeamWithStatsSchema(
            abbr=team.abbr, name=team.name, city=team.city,
            conference=team.conference,
            record=f"{wins}-{len(appearances) - wins}",
            last_ten=f"{recent_wins}-{len(recent) - recent_wins}" if recent else None,
            streak=streak,
            # Official conference tiebreakers are unavailable in imported games.
            conference_rank=None,
            stats=TeamStatsSchema(
                team_abbr=team.abbr,
                form=[outcome for outcome, _ in recent[:5]],
                last_scores=[score for _, score in recent],
            ),
        ))
    return response
