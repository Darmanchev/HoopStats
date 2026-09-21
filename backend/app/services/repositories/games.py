import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ...models.game import Game
from ..clients.types import LiveGameData
from ..utils import determine_season_type, schedule_season_type

logger = logging.getLogger(__name__)


def _parse_start_time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        logger.warning("Invalid game start time %r", value)
        return None


async def reset_today_flag(db: AsyncSession) -> None:
    """Сбрасывает флаг is_today у всех игр."""
    await db.execute(update(Game).values(is_today=False))


async def upsert_live_games(
    db: AsyncSession,
    games_data: list[LiveGameData],
) -> list[str]:
    """Create or update today's normalized scoreboard games."""
    affected_ids: list[str] = []
    for g in games_data:
        game_id = g["game_id"]

        existing = await db.execute(select(Game).where(Game.id == game_id))
        game = existing.scalar_one_or_none()

        if not game:
            db.add(Game(
                id=game_id,
                team1=g["away_abbr"],
                team2=g["home_abbr"],
                date=g["date"],
                time=g["status_text"],
                venue=g["venue"],
                is_today=True,
                season_type=determine_season_type(g["date"]),
                status=g["status"],
                status_text=g["status_text"],
                period=g["period"],
                clock=g["clock"],
                start_time=_parse_start_time(g["start_time"]),
                score1=g["away_score"],
                score2=g["home_score"],
            ))
        else:
            game.team1 = g["away_abbr"]
            game.team2 = g["home_abbr"]
            game.date = g["date"]
            game.time = g["status_text"]
            game.venue = g["venue"]
            game.is_today = True
            game.status = g["status"]
            game.status_text = g["status_text"]
            game.period = g["period"]
            game.clock = g["clock"]
            game.start_time = _parse_start_time(g["start_time"])
            game.score1 = g["away_score"]
            game.score2 = g["home_score"]
        affected_ids.append(game_id)

    return affected_ids


async def upsert_historical_games(
    db: AsyncSession,
    headers: list[str],
    rows: list[list],
    season: str,
    season_type: str,
) -> int:
    """Сохраняет исторические игры сезона (regular или playoffs).
    
    Каждая игра представлена двумя записями (по одной на каждую команду),
    поэтому объединяем пары по GAME_ID.
    Возвращает количество НОВЫХ игр.
    """
    if not headers or not rows:
        return 0

    seen: set[str] = set()
    count = 0

    for row in rows:
        g = dict(zip(headers, row))
        game_id = str(g["GAME_ID"])

        if game_id in seen:
            continue
        seen.add(game_id)

        # ищем пару для этой игры
        pair = [r for r in rows if dict(zip(headers, r))["GAME_ID"] == game_id]
        if len(pair) < 2:
            continue

        g1 = dict(zip(headers, pair[0]))
        g2 = dict(zip(headers, pair[1]))

        score1 = int(g1["PTS"]) if g1["PTS"] else None
        score2 = int(g2["PTS"]) if g2["PTS"] else None
        final_scores = {
            str(g1["TEAM_ABBREVIATION"]): score1,
            str(g2["TEAM_ABBREVIATION"]): score2,
        }

        existing = await db.execute(select(Game).where(Game.id == game_id))
        existing_game = existing.scalar_one_or_none()
        if existing_game:
            existing_game.is_today = False
            existing_game.status = "final"
            existing_game.status_text = "Final"
            if season_type == "playoffs":
                existing_game.season_type = "playoffs"
            team1_score = final_scores.get(existing_game.team1)
            team2_score = final_scores.get(existing_game.team2)
            if team1_score is not None and team2_score is not None:
                existing_game.score1 = team1_score
                existing_game.score2 = team2_score
            continue

        db.add(Game(
            id=game_id,
            team1=g1["TEAM_ABBREVIATION"],
            team2=g2["TEAM_ABBREVIATION"],
            date=g1["GAME_DATE"],
            time="Final",
            venue="",
            is_today=False,
            season=season,
            season_type=season_type,
            score1=score1,
            score2=score2,
            status="final",
            status_text="Final",
        ))
        count += 1

    await db.commit()
    return count


async def upsert_schedule_games(
    db: AsyncSession,
    schedule_data: dict,
) -> tuple[int, int]:
    """Сохраняет будущие (ещё не сыгранные) игры из расписания NBA.
    
    Возвращает (count_new, count_updated).
    """
    league = schedule_data.get("leagueSchedule", {})
    season = league.get("seasonYear", "2025-26")
    game_dates = league.get("gameDates", [])
    today = datetime.now().strftime("%Y-%m-%d")

    count_new = 0
    count_updated = 0

    for day in game_dates:
        for g in day.get("games", []):
            # gameStatus: 1 = запланирована, 2 = идёт, 3 = завершена
            if g.get("gameStatus") != 1:
                continue

            game_id = str(g.get("gameId", ""))
            date = (g.get("gameDateEst") or "")[:10]
            home = (g.get("homeTeam") or {}).get("teamTricode")
            away = (g.get("awayTeam") or {}).get("teamTricode")
            if not game_id or not date or not home or not away:
                continue

            existing = await db.execute(select(Game).where(Game.id == game_id))
            game = existing.scalar_one_or_none()

            if game:
                if game.status != "scheduled":
                    continue
                game.date = date
                game.time = g.get("gameStatusText", "")
                game.venue = g.get("arenaName", "") or ""
                game.is_today = date == today
                game.status = "scheduled"
                game.start_time = _parse_start_time(
                    g.get("gameDateTimeUTC") or g.get("gameDateEst")
                )
                count_updated += 1
            else:
                db.add(Game(
                    id=game_id,
                    team1=away,
                    team2=home,
                    date=date,
                    time=g.get("gameStatusText", ""),
                    venue=g.get("arenaName", "") or "",
                    is_today=date == today,
                    season=season,
                    season_type=schedule_season_type(game_id),
                    win1=50.0,
                    score1=None,
                    score2=None,
                    status="scheduled",
                    start_time=_parse_start_time(
                        g.get("gameDateTimeUTC") or g.get("gameDateEst")
                    ),
                ))
                count_new += 1

    await db.commit()
    return count_new, count_updated
