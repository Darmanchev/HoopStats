"""NBA API client — thin wrapper around nba_api and httpx.

No SQLAlchemy imports: every function either calls the nba_api endpoints
synchronously or fetches data over HTTP and returns raw Python objects.
"""

import asyncio
import logging
import re
from typing import Any

import httpx
from nba_api.live.nba.endpoints import boxscore, scoreboard
from nba_api.stats.endpoints import (
    leaguedashplayerstats,
    leaguegamefinder,
    leaguestandings,
    teamgamelog,
)
from nba_api.stats.static import teams as nba_teams

from .types import LiveGameData, LivePlayerStatData, StandingData
from ..utils import SCHEDULE_URL

logger = logging.getLogger(__name__)

NBA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
}

_GAME_STATUS = {1: "scheduled", 2: "live", 3: "final"}
_ISO_DURATION = re.compile(
    r"^PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?"
    r"(?:(?P<seconds>\d+(?:\.\d+)?)S)?$"
)


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _minutes_float(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return 0.0
    match = _ISO_DURATION.fullmatch(value)
    if not match:
        return 0.0
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = float(match.group("seconds") or 0)
    return hours * 60 + minutes + seconds / 60


def parse_standings(data: dict[str, Any]) -> dict[int, StandingData]:
    result_sets = data.get("resultSets") or []
    if not result_sets:
        return {}
    headers = result_sets[0].get("headers") or []
    records: dict[int, StandingData] = {}
    for row in result_sets[0].get("rowSet") or []:
        standing = dict(zip(headers, row))
        team_id = _optional_int(standing.get("TeamID"))
        if team_id is None:
            continue
        conference = str(standing.get("Conference") or "")
        records[team_id] = {
            "record": (
                f"{_optional_int(standing.get('WINS')) or 0}-"
                f"{_optional_int(standing.get('LOSSES')) or 0}"
            ),
            "conference": (
                "East" if conference.lower().startswith("east") else "West"
            ),
            "conference_rank": (
                _optional_int(standing.get("PlayoffRank")) or 0
            ),
            "last_ten": str(standing.get("L10") or ""),
            "streak": str(
                standing.get("strCurrentStreak") or ""
            ).replace(" ", ""),
        }
    return records


def parse_live_scoreboard(data: dict[str, Any]) -> list[LiveGameData]:
    games: list[LiveGameData] = []
    for raw in (data.get("scoreboard") or {}).get("games") or []:
        game_id = str(raw.get("gameId") or "")
        away = raw.get("awayTeam") or {}
        home = raw.get("homeTeam") or {}
        away_abbr = str(away.get("teamTricode") or "")
        home_abbr = str(home.get("teamTricode") or "")
        game_date = str(raw.get("gameEt") or "")[:10]
        status = _GAME_STATUS.get(_optional_int(raw.get("gameStatus")) or 0)
        if not game_id or not away_abbr or not home_abbr or not game_date or not status:
            logger.warning("Skipping malformed live scoreboard game %r", game_id)
            continue
        has_score = status in {"live", "final"}
        games.append(
            {
                "game_id": game_id,
                "away_abbr": away_abbr,
                "home_abbr": home_abbr,
                "date": game_date,
                "status": status,
                "status_text": str(raw.get("gameStatusText") or ""),
                "period": _optional_int(raw.get("period")) or None,
                "clock": str(raw.get("gameClock") or "") or None,
                "away_score": _optional_int(away.get("score")) if has_score else None,
                "home_score": _optional_int(home.get("score")) if has_score else None,
                "venue": str(raw.get("arenaName") or ""),
            }
        )
    return games


def parse_live_boxscore(data: dict[str, Any]) -> list[LivePlayerStatData]:
    game = data.get("game") or {}
    game_id = str(game.get("gameId") or "")
    if not game_id:
        return []

    players: list[LivePlayerStatData] = []
    for side in ("awayTeam", "homeTeam"):
        team = game.get(side) or {}
        team_abbr = str(team.get("teamTricode") or "")
        if not team_abbr:
            continue
        for raw in team.get("players") or []:
            nba_id = _optional_int(raw.get("personId"))
            name = str(
                raw.get("name")
                or " ".join(
                    part
                    for part in (raw.get("firstName"), raw.get("familyName"))
                    if part
                )
            ).strip()
            if nba_id is None or not name:
                continue
            stats = raw.get("statistics") or {}
            players.append(
                {
                    "game_id": game_id,
                    "nba_id": nba_id,
                    "name": name,
                    "team_abbr": team_abbr,
                    "points": _optional_int(stats.get("points")) or 0,
                    "rebounds": _optional_int(stats.get("reboundsTotal")) or 0,
                    "assists": _optional_int(stats.get("assists")) or 0,
                    "steals": _optional_int(stats.get("steals")) or 0,
                    "blocks": _optional_int(stats.get("blocks")) or 0,
                    "minutes": _minutes_float(stats.get("minutes")),
                }
            )
    return players


def fetch_teams() -> list[dict]:
    """Return the full list of NBA teams from the static registry."""
    return nba_teams.get_teams()


def fetch_standings(season: str) -> dict[int, StandingData]:
    """Fetch normalized league standings for *season*."""
    try:
        standings = leaguestandings.LeagueStandings(season=season)
        data = standings.get_dict()
        records = parse_standings(data)
        logger.info("Standings: %d команд", len(records))
        return records
    except Exception as e:
        logger.error("Ошибка при загрузке standings: %s", e)
        return {}


def fetch_live_scoreboard() -> list[LiveGameData]:
    """Return today's live scoreboard games."""
    board = scoreboard.ScoreBoard(
        headers=NBA_HEADERS
    )
    return parse_live_scoreboard(board.get_dict())


def fetch_live_boxscore(game_id: str) -> list[LivePlayerStatData]:
    """Return normalized player box-score rows for one game."""
    response = boxscore.BoxScore(game_id=game_id, headers=NBA_HEADERS)
    return parse_live_boxscore(response.get_dict())


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
