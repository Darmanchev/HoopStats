"""Оркестрация синхронизации данных: client → repository.

Каждая sync_* функция — тонкий «клей», который вызывает API-клиент,
передаёт данные в репозиторий и логирует результат.
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.team import Team
from .utils import CURRENT_SEASON, parse_log_date
from .clients import nba as nba_client
from .clients import espn as espn_client
from .repositories import teams as teams_repo
from .repositories import games as games_repo
from .repositories import team_stats as team_stats_repo
from .repositories import players as players_repo
from .repositories import injuries as injuries_repo

logger = logging.getLogger(__name__)


async def sync_teams(db: AsyncSession) -> None:
    """Загружает все команды из NBA API и обновляет БД."""
    raw_teams = nba_client.fetch_teams()
    logger.info("NBA API вернул %d команд", len(raw_teams))

    records = nba_client.fetch_standings(CURRENT_SEASON)

    count_new = await teams_repo.upsert_teams(db, raw_teams, records)
    logger.info("Синхронизировано %d команд (%d новых)", len(raw_teams), count_new)


async def sync_games(db: AsyncSession) -> None:
    """Загружает живые игры сегодня из NBA scoreboard."""
    try:
        games_data = nba_client.fetch_live_scoreboard()
    except Exception as e:
        logger.error("Ошибка при загрузке игр: %s: %s", type(e).__name__, e)
        return

    if not games_data:
        logger.info("Сегодня игр нет")
        return

    await games_repo.reset_today_flag(db)
    count = await games_repo.upsert_live_games(db, games_data)
    logger.info("Синхронизировано %d игр", count)


async def sync_historical_games(db: AsyncSession, season: str = CURRENT_SEASON) -> None:
    """Загружает все игры сезона (regular + playoffs) из LeagueGameFinder."""
    logger.info("Загрузка игр сезона %s...", season)

    # Регулярный сезон
    try:
        await asyncio.sleep(1.0)
        headers, rows = nba_client.fetch_league_games(season, "Regular Season")
        logger.info("NBA API вернул %d записей (регулярный сезон)", len(rows))
    except Exception as e:
        logger.error("Ошибка при запросе регулярного сезона: %s: %s", type(e).__name__, e)
        return

    if not rows:
        logger.warning("Нет данных для сезона %s", season)
        return

    count = await games_repo.upsert_historical_games(db, headers, rows, season, "regular")
    logger.info("Загружено %d игр регулярного сезона", count)

    # Плей-офф
    logger.info("Загрузка игр плей-офф сезона %s...", season)
    try:
        await asyncio.sleep(1.0)
        headers, rows = nba_client.fetch_league_games(season, "Playoffs")
        logger.info("NBA API вернул %d записей (плей-офф)", len(rows))
    except Exception as e:
        logger.info("Плей-офф ещё не начался или данные недоступны: %s", e)
        return

    if not rows:
        logger.info("Игр плей-офф не найдено")
        return

    count = await games_repo.upsert_historical_games(db, headers, rows, season, "playoffs")
    logger.info("Загружено %d игр плей-офф", count)


async def sync_schedule(db: AsyncSession) -> None:
    """Загружает будущие (ещё не сыгранные) игры из расписания NBA CDN."""
    logger.info("Загрузка расписания NBA...")
    try:
        schedule_data = await nba_client.fetch_schedule()
    except Exception as e:
        logger.error("Ошибка при загрузке расписания: %s: %s", type(e).__name__, e)
        return

    count_new, count_updated = await games_repo.upsert_schedule_games(db, schedule_data)
    logger.info("Расписание загружено: %d новых, %d обновлено", count_new, count_updated)


async def sync_team_stats(db: AsyncSession) -> None:
    """Загружает форму и последние счета для всех команд."""
    result = await db.execute(select(Team))
    teams = result.scalars().all()
    logger.info("Загрузка статистики для %d команд...", len(teams))

    success_count = 0
    error_count = 0

    for team in teams:
        if not team.nba_id:
            continue

        try:
            # тянем регулярку И плей-офф — чтобы «последние» игры были
            # реально последними, а не последними только в регулярке
            games: list[dict] = []
            for season_type in ("Regular Season", "Playoffs"):
                await asyncio.sleep(1.0)  # rate limit
                try:
                    games += nba_client.fetch_team_game_log(
                        team.nba_id, CURRENT_SEASON, season_type,
                    )
                except Exception as e:
                    logger.debug(
                        "%s (%s): %s: %s",
                        team.abbr, season_type, type(e).__name__, e,
                    )

            if not games:
                logger.warning("%s: нет игр в логе", team.abbr)
                error_count += 1
                continue

            # сортируем по дате — реально последние игры сверху
            games.sort(
                key=lambda g: parse_log_date(g.get("GAME_DATE", "")),
                reverse=True,
            )
            recent = games[:10]
            form = [g["WL"] for g in recent]
            scores = [int(g["PTS"]) for g in recent]

            await team_stats_repo.upsert_team_stats(db, team.abbr, form, scores)
            success_count += 1

        except Exception as e:
            error_count += 1
            if error_count <= 3:
                logger.error("Ошибка %s: %s: %s", team.abbr, type(e).__name__, e)

    await db.commit()
    logger.info(
        "Статистика команд синхронизирована: %d успешно, %d ошибок",
        success_count, error_count,
    )


async def sync_players(db: AsyncSession, season: str = CURRENT_SEASON) -> None:
    """Загружает игроков и их статистику из NBA API."""
    logger.info("Загрузка статистики игроков сезона %s...", season)

    try:
        await asyncio.sleep(1.0)
        headers, rows = nba_client.fetch_player_stats(season)
        logger.info("NBA API вернул %d записей игроков", len(rows))
    except Exception as e:
        logger.error("Ошибка при загрузке статистики игроков: %s: %s", type(e).__name__, e)
        return

    if not headers or not rows:
        logger.warning("Нет данных об игроках")
        return

    count_new, count_updated = await players_repo.upsert_players(db, headers, rows)
    logger.info("Игроки синхронизированы: %d новых, %d обновлено", count_new, count_updated)


async def sync_injuries(db: AsyncSession) -> None:
    """Загружает данные о травмах из ESPN API."""
    logger.info("Загрузка данных о травмах из ESPN...")

    try:
        teams_injuries = await espn_client.fetch_injuries()
    except Exception as e:
        logger.error("Ошибка при загрузке травм: %s: %s", type(e).__name__, e)
        return

    if not teams_injuries:
        logger.warning("Травм не найдено")
        return

    count = await injuries_repo.replace_all_injuries(db, teams_injuries)
    logger.info("Загружено %d записей о травмах", count)
