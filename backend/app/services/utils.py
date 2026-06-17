"""Константы и утилиты для сервисов синхронизации NBA."""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Текущий сезон NBA (единственная точка изменения при смене сезона)
CURRENT_SEASON = "2025-26"

# URL расписания NBA (публичный CDN)
SCHEDULE_URL = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json"

# Минимум сыгранных игр, чтобы попасть в лидеры
LEADER_MIN_GAMES = 15


def determine_season_type(date_str: str) -> str:
    """Определяет тип сезона (regular/playoffs) по дате игры.

    NBA Playoffs start mid-April (14-20) and end in June.
    Regular season runs from October to mid-April.
    """
    try:
        if "T" in date_str:
            date_str = date_str.split("T")[0]

        for fmt in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y", "%m/%d/%Y"):
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                if dt.month == 4 and dt.day >= 14:
                    return "playoffs"
                if dt.month in (5, 6):
                    return "playoffs"
                return "regular"
            except ValueError:
                continue

        date_lower = date_str.lower()
        if any(m in date_lower for m in ["may", "june"]):
            return "playoffs"
        if "april" in date_lower:
            try:
                day = int(date_str.split()[1].replace(",", ""))
                if day >= 14:
                    return "playoffs"
            except (ValueError, IndexError):
                pass

        return "regular"
    except Exception:
        return "regular"


def parse_log_date(s: str) -> datetime:
    """Парсит GAME_DATE из TeamGameLog ('APR 13, 2026') для сортировки."""
    for fmt in ("%b %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    return datetime.min


def schedule_season_type(game_id: str) -> str:
    """Тип сезона по NBA game id (3-й символ: 2=регулярка, 4=плей-офф, 5=плей-ин)."""
    return "playoffs" if game_id[2:3] in ("4", "5") else "regular"


# Цвета команд перенесены на фронтенд (src/utils/colors.ts)

# Маппинг полных названий команд ESPN → аббревиатуры
TEAM_NAME_TO_ABBR: dict[str, str] = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
    "LA Clippers": "LAC", "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA", "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP", "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR", "Utah Jazz": "UTA", "Washington Wizards": "WAS",
}
