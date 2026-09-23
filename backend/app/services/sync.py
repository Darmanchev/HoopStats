"""Оркестрация синхронизации данных: client → repository.

Каждая sync_* функция — тонкий «клей», который вызывает API-клиент,
передаёт данные в репозиторий и логирует результат.
"""

import asyncio
import logging
import re
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..cache import (
    invalidate_elo_cache,
    invalidate_live_caches,
    invalidate_teams_cache,
)
from ..models.team import Team
from .clients.balldontlie import (
    BallDontLieError,
    create_client as create_balldontlie_client,
)
from .clients.balldontlie_normalizers import (
    normalize_games,
    normalize_players,
    normalize_teams,
)
from .clients import espn as espn_client
from .clients import nba as nba_client
from .repositories import games as games_repo
from .repositories import injuries as injuries_repo
from .repositories import players as players_repo
from .repositories import team_stats as team_stats_repo
from .repositories import teams as teams_repo
from .utils import CURRENT_SEASON, parse_log_date

logger = logging.getLogger(__name__)


async def sync_teams(db: AsyncSession) -> None:
    """Load BALLDONTLIE team profiles without paid standings data."""
    try:
        async with create_balldontlie_client() as client:
            raw_teams = await client.get_teams()
        profiles = normalize_teams(raw_teams)
        count_new = await teams_repo.upsert_teams(db, profiles)
        await db.commit()
    except (BallDontLieError, ValueError) as exc:
        await db.rollback()
        logger.error("BALLDONTLIE team sync failed: %s", exc)
        return

    await invalidate_teams_cache()
    logger.info("Synced %d teams (%d new)", len(profiles), count_new)


async def sync_games(
    db: AsyncSession,
    *,
    today: date | None = None,
) -> None:
    """Load and persist the validated BALLDONTLIE games for one date."""
    sync_date = today or datetime.now(timezone.utc).date()
    date_text = sync_date.isoformat()
    try:
        async with create_balldontlie_client() as client:
            raw_games = await client.get_games(dates=[date_text])
        games_data = normalize_games(raw_games)
    except (BallDontLieError, ValueError) as exc:
        await db.rollback()
        logger.error("BALLDONTLIE game sync failed: %s", exc)
        return

    await games_repo.reset_today_flag(db)
    if not games_data:
        await db.commit()
        await invalidate_live_caches([])
        logger.info("No games returned for %s", date_text)
        return

    affected_ids = await games_repo.upsert_games(
        db,
        games_data,
        today=date_text,
    )
    await db.commit()
    await invalidate_live_caches(affected_ids)
    await invalidate_elo_cache()
    logger.info("Synced %d games for %s", len(affected_ids), date_text)


def season_start_year(season: str) -> int:
    """Convert an application season label into BALLDONTLIE's start year."""
    match = re.fullmatch(r"(\d{4})-(\d{2})", season)
    if match is None:
        raise ValueError(f"Invalid NBA season: {season}")
    start = int(match.group(1))
    if int(match.group(2)) != (start + 1) % 100:
        raise ValueError(f"Invalid NBA season: {season}")
    return start


async def sync_historical_games(
    db: AsyncSession,
    season: str = CURRENT_SEASON,
) -> None:
    """Load final regular-season and playoff games from BALLDONTLIE."""
    start_year = season_start_year(season)
    try:
        async with create_balldontlie_client() as client:
            regular_raw = await client.get_games(
                seasons=[start_year],
                season_type="regular",
            )
            playoffs_raw = await client.get_games(
                seasons=[start_year],
                season_type="playoffs",
            )
        games_data = [
            game
            for game in normalize_games(regular_raw) + normalize_games(playoffs_raw)
            if game["status"] == "final"
        ]
        affected_ids = await games_repo.upsert_games(db, games_data)
        await db.commit()
    except (BallDontLieError, ValueError) as exc:
        await db.rollback()
        logger.error("BALLDONTLIE historical sync failed: %s", exc)
        return

    await invalidate_elo_cache()
    logger.info("Synced %d final games for %s", len(affected_ids), season)


async def sync_schedule(
    db: AsyncSession,
    *,
    start_date: date | None = None,
) -> None:
    """Load the next 30 days of BALLDONTLIE games."""
    window_start = start_date or datetime.now(timezone.utc).date()
    window_end = window_start + timedelta(days=30)
    start_text = window_start.isoformat()
    try:
        async with create_balldontlie_client() as client:
            raw_games = await client.get_games(
                start_date=start_text,
                end_date=window_end.isoformat(),
            )
        games_data = normalize_games(raw_games)
        affected_ids = await games_repo.upsert_games(
            db,
            games_data,
            today=start_text,
        )
        await db.commit()
    except (BallDontLieError, ValueError) as exc:
        await db.rollback()
        logger.error("BALLDONTLIE schedule sync failed: %s", exc)
        return

    logger.info("Synced %d games in the 30-day schedule", len(affected_ids))


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
                    games += await asyncio.to_thread(
                        nba_client.fetch_team_game_log,
                        team.nba_id,
                        CURRENT_SEASON,
                        season_type,
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
    await invalidate_teams_cache()
    logger.info(
        "Статистика команд синхронизирована: %d успешно, %d ошибок",
        success_count, error_count,
    )


async def sync_players(db: AsyncSession, season: str = CURRENT_SEASON) -> None:
    """Load basic BALLDONTLIE profiles for teams present in the database."""
    del season
    try:
        result = await db.execute(select(Team.abbr))
        valid_team_abbrs = set(result.scalars().all())
        async with create_balldontlie_client() as client:
            raw_players = await client.get_players()
        profiles = normalize_players(raw_players, valid_team_abbrs)
        count_new, count_updated = await players_repo.upsert_players(
            db,
            profiles,
        )
        await db.commit()
    except (BallDontLieError, ValueError) as exc:
        await db.rollback()
        logger.error("BALLDONTLIE player sync failed: %s", exc)
        return

    logger.info(
        "Synced player profiles: %d new, %d updated",
        count_new,
        count_updated,
    )


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
