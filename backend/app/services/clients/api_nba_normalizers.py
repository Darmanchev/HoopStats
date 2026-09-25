import re
from collections import Counter, defaultdict
from typing import Any

from app.services.clients.types import (
    ApiNbaPlayerProfileData,
    ApiNbaTeamData,
    PlayerSeasonData,
)


_SEASON_PATTERN = re.compile(r"^(\d{4})-(\d{2})$")


def season_start_year(season: str) -> int:
    match = _SEASON_PATTERN.fullmatch(season)
    if match is None:
        raise ValueError("season must use YYYY-YY format")
    start = int(match.group(1))
    expected_end = (start + 1) % 100
    if int(match.group(2)) != expected_end:
        raise ValueError("season end year must follow its start year")
    return start


def _positive_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _number(value: object) -> float:
    if value is None or isinstance(value, bool):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _minutes(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return max(float(value), 0.0)
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if ":" not in raw:
        try:
            return max(float(raw), 0.0)
        except ValueError:
            return None
    minutes, seconds = raw.split(":", 1)
    try:
        parsed_minutes = float(minutes)
        parsed_seconds = float(seconds)
    except ValueError:
        return None
    if parsed_minutes < 0 or not 0 <= parsed_seconds < 60:
        return None
    return parsed_minutes + parsed_seconds / 60


def normalize_api_nba_teams(
    raw: list[dict[str, Any]],
    valid_abbrs: set[str],
) -> list[ApiNbaTeamData]:
    teams: list[ApiNbaTeamData] = []
    seen_ids: set[int] = set()
    seen_codes: set[str] = set()
    for record in raw:
        if not isinstance(record, dict):
            continue
        team_id = _positive_int(record.get("id"))
        code = record.get("code")
        if (
            team_id is None
            or not isinstance(code, str)
            or code not in valid_abbrs
            or record.get("nbaFranchise") is not True
            or record.get("allStar") is True
            or team_id in seen_ids
            or code in seen_codes
        ):
            continue
        seen_ids.add(team_id)
        seen_codes.add(code)
        teams.append({"api_nba_id": team_id, "abbr": code})
    if raw and not teams:
        raise ValueError("API-NBA response contained no valid teams")
    return teams


def _profile_from_record(record: object) -> ApiNbaPlayerProfileData | None:
    if not isinstance(record, dict):
        return None
    player_id = _positive_int(record.get("id"))
    first = record.get("firstname")
    last = record.get("lastname")
    if player_id is None or not isinstance(first, str) or not isinstance(last, str):
        return None
    name = " ".join(part.strip() for part in (first, last) if part.strip())
    if not name:
        return None
    leagues = record.get("leagues")
    standard = leagues.get("standard") if isinstance(leagues, dict) else None
    standard = standard if isinstance(standard, dict) else {}
    position = standard.get("pos")
    jersey = standard.get("jersey")
    return {
        "api_nba_id": player_id,
        "name": name,
        "position": position.strip() if isinstance(position, str) else "",
        "jersey_number": str(jersey) if jersey is not None else None,
    }


def _profile_from_stat(record: dict[str, Any]) -> ApiNbaPlayerProfileData | None:
    raw_player = record.get("player")
    if not isinstance(raw_player, dict):
        return None
    profile = _profile_from_record(raw_player)
    if profile is not None:
        if not profile["position"] and isinstance(record.get("pos"), str):
            profile["position"] = record["pos"].strip()
        return profile
    player_id = _positive_int(raw_player.get("id"))
    first = raw_player.get("firstname")
    last = raw_player.get("lastname")
    if player_id is None:
        return None
    name = " ".join(
        part.strip()
        for part in (first, last)
        if isinstance(part, str) and part.strip()
    )
    if not name:
        return None
    return {
        "api_nba_id": player_id,
        "name": name,
        "position": record.get("pos", "") if isinstance(record.get("pos"), str) else "",
        "jersey_number": None,
    }


def aggregate_player_season(
    season: str,
    team_map: dict[int, str],
    roster_pages: dict[int, list[dict[str, Any]]],
    stat_pages: dict[int, list[dict[str, Any]]],
) -> tuple[list[ApiNbaPlayerProfileData], list[PlayerSeasonData]]:
    season_start_year(season)
    valid_team_map = {
        team_id: abbr
        for team_id, abbr in team_map.items()
        if _positive_int(team_id) is not None and isinstance(abbr, str) and abbr
    }
    if not valid_team_map:
        raise ValueError("team map must contain at least one valid team")

    profiles: dict[int, ApiNbaPlayerProfileData] = {}
    roster_teams: dict[int, set[str]] = defaultdict(set)
    raw_roster_count = 0
    for team_id, records in roster_pages.items():
        abbr = valid_team_map.get(team_id)
        if abbr is None:
            continue
        raw_roster_count += len(records)
        for record in records:
            profile = _profile_from_record(record)
            if profile is None:
                continue
            player_id = profile["api_nba_id"]
            existing = profiles.get(player_id)
            if existing is None:
                profiles[player_id] = profile
            else:
                if not existing["position"] and profile["position"]:
                    existing["position"] = profile["position"]
                if existing["jersey_number"] is None and profile["jersey_number"] is not None:
                    existing["jersey_number"] = profile["jersey_number"]
            roster_teams[player_id].add(abbr)

    if raw_roster_count and not profiles:
        raise ValueError("API-NBA response contained no valid players")

    totals: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    team_counts: dict[int, Counter[str]] = defaultdict(Counter)
    seen_games: set[tuple[int, int]] = set()
    for records in stat_pages.values():
        for record in records:
            if not isinstance(record, dict):
                continue
            profile = _profile_from_stat(record)
            raw_team = record.get("team")
            raw_game = record.get("game")
            if profile is None or not isinstance(raw_team, dict) or not isinstance(raw_game, dict):
                continue
            team_id = _positive_int(raw_team.get("id"))
            game_id = _positive_int(raw_game.get("id"))
            minutes = _minutes(record.get("min"))
            if team_id is None or game_id is None or minutes is None:
                continue
            abbr = valid_team_map.get(team_id)
            if abbr is None:
                continue
            player_id = profile["api_nba_id"]
            dedupe_key = (player_id, game_id)
            if dedupe_key in seen_games:
                continue
            seen_games.add(dedupe_key)
            profiles.setdefault(player_id, profile)
            roster_teams[player_id].add(abbr)
            values = totals[player_id]
            values["games"] += 1
            values["points"] += _number(record.get("points"))
            values["rebounds"] += _number(record.get("totReb"))
            values["assists"] += _number(record.get("assists"))
            values["steals"] += _number(record.get("steals"))
            values["blocks"] += _number(record.get("blocks"))
            values["minutes"] += minutes
            values["fgm"] += _number(record.get("fgm"))
            values["fga"] += _number(record.get("fga"))
            values["tpm"] += _number(record.get("tpm"))
            values["tpa"] += _number(record.get("tpa"))
            values["ftm"] += _number(record.get("ftm"))
            values["fta"] += _number(record.get("fta"))
            team_counts[player_id][abbr] += 1

    season_rows: list[PlayerSeasonData] = []
    for player_id in sorted(profiles):
        values = totals[player_id]
        games = int(values["games"])
        counts = team_counts[player_id]
        candidates = counts.items() if counts else ((abbr, 0) for abbr in roster_teams[player_id])
        primary_team = max(candidates, key=lambda item: (item[1], item[0]))[0]

        def per_game(field: str) -> float:
            return round(values[field] / games, 1) if games else 0.0

        def percentage(makes: str, attempts: str) -> float:
            return round(values[makes] / values[attempts], 3) if values[attempts] else 0.0

        season_rows.append({
            "api_nba_id": player_id,
            "season": season,
            "primary_team_abbr": primary_team,
            "games_played": games,
            "pts": per_game("points"),
            "reb": per_game("rebounds"),
            "ast": per_game("assists"),
            "stl": per_game("steals"),
            "blk": per_game("blocks"),
            "fg_pct": percentage("fgm", "fga"),
            "fg3_pct": percentage("tpm", "tpa"),
            "ft_pct": percentage("ftm", "fta"),
            "mins": per_game("minutes"),
            "recent_games": min(games, 10),
        })

    return [profiles[player_id] for player_id in sorted(profiles)], season_rows
