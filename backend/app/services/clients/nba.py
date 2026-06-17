"""NBA API client — thin wrapper around nba_api and httpx.

No SQLAlchemy imports: every function either calls the nba_api endpoints
synchronously or fetches data over HTTP and returns raw Python objects.
"""

import asyncio
import logging
from typing import Any

import httpx
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.endpoints import (
    leaguedashplayerstats,
    leaguegamefinder,
    leaguestandings,
    teamgamelog,
)
from nba_api.stats.static import teams as nba_teams

from ..utils import SCHEDULE_URL

logger = logging.getLogger(__name__)


def fetch_teams() -> list[dict]:
    """Return the full list of NBA teams from the static registry."""
    return nba_teams.get_teams()


def fetch_standings(season: str) -> dict[int, str]:
    """Fetch league standings for *season* and return ``{team_id: 'W-L'}``."""
    try:
        standings = leaguestandings.LeagueStandings(season=season)
        data = standings.get_dict()
        headers = data["resultSets"][0]["headers"]
        rows = data["resultSets"][0]["rowSet"]
        logger.info("Standings: %d команд", len(rows))
        records: dict[int, str] = {}
        for row in rows:
            s = dict(zip(headers, row))
            records[int(s["TeamID"])] = f"{s.get('WINS', 0)}-{s.get('LOSSES', 0)}"
        return records
    except Exception as e:
        logger.error("Ошибка при загрузке standings: %s", e)
        return {}


def fetch_live_scoreboard() -> list[dict]:
    """Return today's live scoreboard games."""
    board = scoreboard.ScoreBoard(
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Referer": "https://www.nba.com/",
            "Origin": "https://www.nba.com",
        }
    )
    data = board.get_dict()
    return data.get("scoreboard", {}).get("games", [])


def fetch_team_game_log(
    nba_id: int,
    season: str,
    season_type: str,
) -> list[dict]:
    """Fetch a single team's game log for the given season/type."""
    log = teamgamelog.TeamGameLog(
        team_id=str(nba_id),
        season=season,
        season_type_all_star=season_type,
    )
    rs = log.get_dict().get("resultSets", [])
    if not rs:
        return []
    headers = rs[0].get("headers", [])
    return [dict(zip(headers, r)) for r in rs[0].get("rowSet", [])]


def fetch_league_games(
    season: str,
    season_type: str,
) -> tuple[list[str], list[list]]:
    """Возвращает (headers, rows) сыгранных игр сезона."""
    finder = leaguegamefinder.LeagueGameFinder(
        season_nullable=season,
        season_type_nullable=season_type,
    )
    data = finder.get_dict()
    result_sets = data.get("resultSets", [])
    if not result_sets:
        return [], []
    headers = result_sets[0].get("headers", [])
    rows = result_sets[0].get("rowSet", [])
    return headers, rows


async def fetch_schedule() -> dict:
    """Загружает расписание NBA из публичного CDN."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://www.nba.com/",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(SCHEDULE_URL, headers=headers)
        resp.raise_for_status()
        return resp.json()


def fetch_player_stats(season: str) -> tuple[list[str], list[list]]:
    """Возвращает (headers, rows) статистики всех игроков за сезон."""
    stats = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        season_type_all_star="Regular Season",
        per_mode_detailed="PerGame",
    )
    data = stats.get_dict()
    result_sets = data.get("resultSets", [])
    if not result_sets:
        return [], []
    headers = result_sets[0].get("headers", [])
    rows = result_sets[0].get("rowSet", [])
    return headers, rows
