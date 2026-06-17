import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ...models.game import Game
from ..utils import determine_season_type, schedule_season_type

logger = logging.getLogger(__name__)


async def reset_today_flag(db: AsyncSession) -> None:
    """Сбрасывает флаг is_today у всех игр."""
    await db.execute(update(Game).values(is_today=False))


async def upsert_live_games(db: AsyncSession, games_data: list[dict]) -> int:
    """Создаёт или обновляет сегодняшние игры из live scoreboard.
    
    games_data — список словарей от NBA live scoreboard API.
    Возвращает количество обработанных игр.
    """
    count = 0
    for g in games_data:
        game_id = str(g["gameId"])
        home = g["homeTeam"]
        away = g["awayTeam"]
        status = g["gameStatusText"]
        is_final = "Final" in status

        existing = await db.execute(select(Game).where(Game.id == game_id))
        game = existing.scalar_one_or_none()

        if not game:
            db.add(Game(
                id=game_id,
                team1=away["teamTricode"],
                team2=home["teamTricode"],
                date=g["gameEt"][:10],
                time=status,
                venue=g.get("arenaName", ""),
                is_today=True,
                season_type=determine_season_type(g["gameEt"]),
                score1=away["score"] if is_final else None,
                score2=home["score"] if is_final else None,
            ))
            count += 1
        elif is_final:
            game.score1 = away["score"]
            game.score2 = home["score"]
            count += 1

    await db.commit()
    return count


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

        existing = await db.execute(select(Game).where(Game.id == game_id))
        existing_game = existing.scalar_one_or_none()
        if existing_game:
            existing_game.is_today = False
            if season_type == "playoffs":
                existing_game.season_type = "playoffs"
            if existing_game.score1 is None and score1 is not None:
                existing_game.score1 = score1
                existing_game.score2 = score2
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
                if game.score1 is not None:
                    continue
                game.date = date
                game.time = g.get("gameStatusText", "")
                game.venue = g.get("arenaName", "") or ""
                game.is_today = date == today
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
                ))
                count_new += 1

    await db.commit()
    return count_new, count_updated
