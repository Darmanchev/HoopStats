"""ESPN API client — fetches injury data for all NBA teams.

No SQLAlchemy imports: returns raw JSON structures from the ESPN public API.
"""

import logging

import httpx

logger = logging.getLogger(__name__)

ESPN_INJURIES_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
)


async def fetch_injuries() -> list[dict]:
    """Загружает данные о травмах всех команд NBA из ESPN API.

    Возвращает список team-объектов:
    ``[{"displayName": "Atlanta Hawks", "injuries": [...]}, ...]``
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            ESPN_INJURIES_URL,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()

    teams_injuries: list[dict] = data.get("injuries", [])
    logger.info("ESPN вернул %d команд с травмами", len(teams_injuries))
    return teams_injuries
