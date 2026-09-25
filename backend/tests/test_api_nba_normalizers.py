import pytest

from app.services.clients.api_nba_normalizers import (
    aggregate_player_season,
    normalize_api_nba_teams,
    season_start_year,
)


RAW_PLAYER = {
    "id": 417,
    "firstname": " Stephen ",
    "lastname": "Curry",
    "leagues": {"standard": {"jersey": 30, "active": True, "pos": "G"}},
}


def stat(
    game_id: int | None,
    team_id: int,
    *,
    attempts: bool = True,
    minutes: str | None = "30:00",
) -> dict:
    return {
        "player": {"id": 417, "firstname": "Stephen", "lastname": "Curry"},
        "team": {"id": team_id},
        "game": {"id": game_id},
        "points": 20,
        "totReb": 4,
        "assists": 6,
        "steals": 1,
        "blocks": 0,
        "min": minutes,
        "fgm": 5 if attempts else 0,
        "fga": 10 if attempts else 0,
        "tpm": 2 if attempts else 0,
        "tpa": 5 if attempts else 0,
        "ftm": 4 if attempts else 0,
        "fta": 5 if attempts else 0,
        "comment": None,
    }


def test_normalize_api_nba_teams_keeps_only_nba_franchises() -> None:
    raw = [
        {
            "id": 1,
            "code": "ATL",
            "nbaFranchise": True,
            "allStar": False,
        },
        {
            "id": 99,
            "code": "EST",
            "nbaFranchise": True,
            "allStar": True,
        },
        {
            "id": 100,
            "code": "OLD",
            "nbaFranchise": False,
            "allStar": False,
        },
    ]

    assert normalize_api_nba_teams(raw, {"ATL", "BOS"}) == [
        {"api_nba_id": 1, "abbr": "ATL"}
    ]


def test_nonempty_team_response_without_valid_codes_is_rejected() -> None:
    raw = [{"id": 1, "code": "XXX", "nbaFranchise": True, "allStar": False}]

    with pytest.raises(ValueError, match="valid teams"):
        normalize_api_nba_teams(raw, {"ATL"})


@pytest.mark.parametrize(
    "season",
    ["2025", "25-26", "2025/26", "2025-27", "2025-2a", "2025-026"],
)
def test_season_start_year_rejects_invalid_format_or_rollover(season: str) -> None:
    with pytest.raises(ValueError, match="season"):
        season_start_year(season)


def test_season_start_year_returns_four_digit_start() -> None:
    assert season_start_year("2025-26") == 2025
    assert season_start_year("1999-00") == 1999


def test_aggregate_combines_trade_stints_and_selects_primary_team() -> None:
    atl_game_1 = stat(1001, 1)
    atl_game_2 = stat(1002, 1)
    bos_game = stat(1003, 2)

    profiles, seasons = aggregate_player_season(
        "2025-26",
        {1: "ATL", 2: "BOS"},
        {1: [RAW_PLAYER], 2: [RAW_PLAYER]},
        {1: [atl_game_1, atl_game_2], 2: [bos_game]},
    )

    assert profiles == [{
        "api_nba_id": 417,
        "name": "Stephen Curry",
        "position": "G",
        "jersey_number": "30",
    }]
    assert seasons == [{
        "api_nba_id": 417,
        "season": "2025-26",
        "primary_team_abbr": "ATL",
        "games_played": 3,
        "pts": 20.0,
        "reb": 4.0,
        "ast": 6.0,
        "stl": 1.0,
        "blk": 0.0,
        "fg_pct": 0.5,
        "fg3_pct": 0.4,
        "ft_pct": 0.8,
        "mins": 30.0,
        "recent_games": 3,
    }]


def test_primary_team_tie_uses_explicit_descending_code_order() -> None:
    _, seasons = aggregate_player_season(
        "2025-26",
        {1: "ATL", 2: "BOS"},
        {1: [RAW_PLAYER], 2: [RAW_PLAYER]},
        {1: [stat(1001, 1)], 2: [stat(1002, 2)]},
    )

    assert seasons[0]["primary_team_abbr"] == "BOS"


def test_aggregate_deduplicates_player_game_and_handles_zero_attempts() -> None:
    zero_attempt_game = stat(1004, 1, attempts=False)
    duplicated = {1: [zero_attempt_game, zero_attempt_game]}

    _, seasons = aggregate_player_season(
        "2025-26", {1: "ATL"}, {1: [RAW_PLAYER]}, duplicated
    )

    assert seasons[0]["games_played"] == 1
    assert seasons[0]["fg_pct"] == 0.0
    assert seasons[0]["fg3_pct"] == 0.0
    assert seasons[0]["ft_pct"] == 0.0


def test_dnp_and_missing_game_id_rows_are_not_counted() -> None:
    _, seasons = aggregate_player_season(
        "2025-26",
        {1: "ATL"},
        {1: [RAW_PLAYER]},
        {1: [stat(1001, 1), stat(1002, 1, minutes=None), stat(None, 1)]},
    )

    assert seasons[0]["games_played"] == 1


def test_minutes_are_parsed_from_mm_ss_and_averaged() -> None:
    _, seasons = aggregate_player_season(
        "2025-26",
        {1: "ATL"},
        {1: [RAW_PLAYER]},
        {1: [stat(1001, 1, minutes="30:30"), stat(1002, 1, minutes="31")]},
    )

    assert seasons[0]["mins"] == 30.8


def test_roster_player_with_no_games_gets_zero_season_row() -> None:
    _, seasons = aggregate_player_season(
        "2025-26", {1: "ATL"}, {1: [RAW_PLAYER]}, {1: []}
    )

    assert seasons[0]["primary_team_abbr"] == "ATL"
    assert seasons[0]["games_played"] == 0
    assert seasons[0]["recent_games"] == 0


def test_missing_positive_player_id_is_rejected_when_no_valid_player_exists() -> None:
    invalid = {**RAW_PLAYER, "id": 0}

    with pytest.raises(ValueError, match="valid players"):
        aggregate_player_season(
            "2025-26", {1: "ATL"}, {1: [invalid]}, {1: []}
        )
