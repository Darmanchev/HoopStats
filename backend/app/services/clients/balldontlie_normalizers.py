"""Pure normalization from BALLDONTLIE payloads to application records."""

from datetime import date, datetime
from typing import Any

from .types import GameData, PlayerProfileData, TeamProfileData


STATUS_MAP = {
    "scheduled": "scheduled",
    "in_progress": "live",
    "final": "final",
}


def _positive_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None
    return value


def _text(value: object, *, maximum: int) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned or len(cleaned) > maximum:
        return None
    return cleaned


def _abbr(value: object) -> str | None:
    cleaned = _text(value, maximum=5)
    return cleaned.upper() if cleaned else None


def normalize_teams(raw_teams: list[dict[str, Any]]) -> list[TeamProfileData]:
    """Return valid NBA team profiles from a provider list response."""
    teams: list[TeamProfileData] = []
    for raw in raw_teams:
        if not isinstance(raw, dict):
            continue
        provider_id = _positive_int(raw.get("id"))
        abbr = _abbr(raw.get("abbreviation"))
        city = _text(raw.get("city"), maximum=50)
        name = _text(raw.get("name"), maximum=50)
        conference = raw.get("conference")
        if (
            provider_id is None
            or abbr is None
            or city is None
            or name is None
            or conference not in {"East", "West"}
        ):
            continue
        teams.append({
            "balldontlie_id": provider_id,
            "abbr": abbr,
            "city": city,
            "name": name,
            "conference": conference,
        })
    if raw_teams and not teams:
        raise ValueError("BALLDONTLIE response contained no valid teams")
    return teams


def normalize_players(
    raw_players: list[dict[str, Any]],
    valid_team_abbrs: set[str],
) -> list[PlayerProfileData]:
    """Return valid basic profiles assigned to recognized NBA teams."""
    players: list[PlayerProfileData] = []
    structurally_valid = 0
    for raw in raw_players:
        if not isinstance(raw, dict):
            continue
        provider_id = _positive_int(raw.get("id"))
        first_name = _text(raw.get("first_name"), maximum=50)
        last_name = _text(raw.get("last_name"), maximum=50)
        position = _text(raw.get("position"), maximum=5)
        team = raw.get("team")
        team_abbr = _abbr(team.get("abbreviation")) if isinstance(team, dict) else None
        if (
            provider_id is None
            or first_name is None
            or last_name is None
            or position is None
            or team_abbr is None
        ):
            continue
        structurally_valid += 1
        if team_abbr not in valid_team_abbrs:
            continue
        jersey = _text(raw.get("jersey_number"), maximum=5)
        players.append({
            "balldontlie_id": provider_id,
            "name": f"{first_name} {last_name}",
            "team_abbr": team_abbr,
            "position": position,
            "jersey_number": jersey,
        })
    if raw_players and structurally_valid == 0:
        raise ValueError("BALLDONTLIE response contained no valid players")
    return players


def season_label(start_year: int) -> str:
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def _score(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _valid_date(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        date.fromisoformat(value)
    except ValueError:
        return None
    return value


def _valid_datetime(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return value


def normalize_games(raw_games: list[dict[str, Any]]) -> list[GameData]:
    """Return games whose lifecycle and required fields are safe to store."""
    games: list[GameData] = []
    for raw in raw_games:
        if not isinstance(raw, dict):
            continue
        provider_id = _positive_int(raw.get("id"))
        start_year = _positive_int(raw.get("season"))
        game_date = _valid_date(raw.get("date"))
        start_time = _valid_datetime(raw.get("datetime"))
        lifecycle = raw.get("status_state")
        status = STATUS_MAP.get(lifecycle)
        status_text = _text(raw.get("status"), maximum=50)
        home = raw.get("home_team")
        visitor = raw.get("visitor_team")
        home_abbr = _abbr(home.get("abbreviation")) if isinstance(home, dict) else None
        away_abbr = (
            _abbr(visitor.get("abbreviation"))
            if isinstance(visitor, dict)
            else None
        )
        if (
            provider_id is None
            or start_year is None
            or game_date is None
            or start_time is None
            or status is None
            or status_text is None
            or home_abbr is None
            or away_abbr is None
        ):
            continue

        away_score: int | None = None
        home_score: int | None = None
        if status in {"live", "final"}:
            away_score = _score(raw.get("visitor_team_score"))
            home_score = _score(raw.get("home_team_score"))
            if away_score is None or home_score is None:
                continue

        raw_period = raw.get("period")
        period = (
            raw_period
            if status != "scheduled"
            and isinstance(raw_period, int)
            and not isinstance(raw_period, bool)
            and raw_period > 0
            else None
        )
        raw_clock = raw.get("time")
        clock = (
            raw_clock.strip()
            if status == "live"
            and isinstance(raw_clock, str)
            and raw_clock.strip()
            else None
        )
        games.append({
            "game_id": f"bdl:{provider_id}",
            "away_abbr": away_abbr,
            "home_abbr": home_abbr,
            "date": game_date,
            "start_time": start_time,
            "status": status,
            "status_text": status_text,
            "period": period,
            "clock": clock,
            "away_score": away_score,
            "home_score": home_score,
            "venue": "",
            "season": season_label(start_year),
            "season_type": "playoffs" if raw.get("postseason") is True else "regular",
        })
    if raw_games and not games:
        raise ValueError("BALLDONTLIE response contained no valid games")
    return games
