"""ESPN API client."""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

logger = logging.getLogger(__name__)

ESPN_BASE_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
)
ESPN_SCOREBOARD_URL = f"{ESPN_BASE_URL}/scoreboard"
ESPN_INJURIES_URL = f"{ESPN_BASE_URL}/injuries"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 Chrome/145.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def _parse_score(value: object) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def _to_eastern_datetime(value: str) -> str:
    """Преобразует ESPN UTC datetime в дату/время NBA Eastern Time."""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        eastern = parsed.astimezone(ZoneInfo("America/New_York"))
        return eastern.isoformat()
    except (TypeError, ValueError):
        return value


def _normalize_scoreboard_event(event: dict) -> dict | None:
    """Преобразует ESPN event в формат NBA live scoreboard."""
    competitions = event.get("competitions") or []
    if not competitions:
        return None

    competition = competitions[0]
    competitors = competition.get("competitors") or []

    home = next(
        (item for item in competitors if item.get("homeAway") == "home"),
        None,
    )
    away = next(
        (item for item in competitors if item.get("homeAway") == "away"),
        None,
    )

    if not home or not away:
        return None

    home_team = home.get("team") or {}
    away_team = away.get("team") or {}

    home_abbr = home_team.get("abbreviation")
    away_abbr = away_team.get("abbreviation")
    game_id = event.get("id")

    if not game_id or not home_abbr or not away_abbr:
        return None

    status_type = ((event.get("status") or {}).get("type") or {})
    status_text = (
        status_type.get("shortDetail")
        or status_type.get("detail")
        or status_type.get("description")
        or "Scheduled"
    )

    state = status_type.get("state")
    game_status = {
        "pre": 1,
        "in": 2,
        "post": 3,
    }.get(state, 1)

    venue = competition.get("venue") or {}

    return {
        "gameId": str(game_id),
        "gameEt": _to_eastern_datetime(event.get("date", "")),
        "gameStatus": game_status,
        "gameStatusText": status_text,
        "arenaName": venue.get("fullName", ""),
        "homeTeam": {
            "teamId": str(home_team.get("id", "")),
            "teamName": home_team.get("name", ""),
            "teamCity": home_team.get("location", ""),
            "teamTricode": home_abbr,
            "score": _parse_score(home.get("score")),
        },
        "awayTeam": {
            "teamId": str(away_team.get("id", "")),
            "teamName": away_team.get("name", ""),
            "teamCity": away_team.get("location", ""),
            "teamTricode": away_abbr,
            "score": _parse_score(away.get("score")),
        },
    }


async def fetch_scoreboard(
    date_yyyymmdd: str | None = None,
) -> list[dict]:
    """Загружает текущие или указанные матчи ESPN."""
    params = {}
    if date_yyyymmdd:
        params["dates"] = date_yyyymmdd

    timeout = httpx.Timeout(20.0, connect=10.0)

    async with httpx.AsyncClient(
        headers=HEADERS,
        timeout=timeout,
        follow_redirects=True,
    ) as client:
        response = await client.get(
            ESPN_SCOREBOARD_URL,
            params=params,
        )
        response.raise_for_status()
        data = response.json()

    games: list[dict] = []

    for event in data.get("events", []):
        normalized = _normalize_scoreboard_event(event)
        if normalized:
            games.append(normalized)

    logger.info("ESPN scoreboard вернул %d матчей", len(games))
    return games


async def fetch_injuries() -> list[dict]:
    """Загружает данные о травмах всех команд."""
    timeout = httpx.Timeout(20.0, connect=10.0)

    async with httpx.AsyncClient(
        headers=HEADERS,
        timeout=timeout,
        follow_redirects=True,
    ) as client:
        response = await client.get(ESPN_INJURIES_URL)
        response.raise_for_status()
        data = response.json()

    injuries: list[dict] = data.get("injuries", [])
    logger.info("ESPN вернул %d команд с травмами", len(injuries))
    return injuries