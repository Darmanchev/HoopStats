import pytest

from app.services.clients.balldontlie_normalizers import (
    normalize_games,
    normalize_players,
    normalize_teams,
)


BASE_GAME = {
    "id": 15907925,
    "date": "2026-01-05",
    "season": 2025,
    "status": "7:00 pm ET",
    "status_state": "scheduled",
    "period": 0,
    "time": " ",
    "postseason": False,
    "postponed": False,
    "home_team_score": 0,
    "visitor_team_score": 0,
    "datetime": "2026-01-05T23:00:00.000Z",
    "home_team": {
        "id": 14,
        "conference": "West",
        "city": "Los Angeles",
        "name": "Lakers",
        "abbreviation": "LAL",
    },
    "visitor_team": {
        "id": 2,
        "conference": "East",
        "city": "Boston",
        "name": "Celtics",
        "abbreviation": "BOS",
    },
}


def test_normalize_team_profile() -> None:
    result = normalize_teams([{
        "id": 2,
        "abbreviation": "BOS",
        "city": "Boston",
        "name": "Celtics",
        "conference": "East",
    }])

    assert result == [{
        "balldontlie_id": 2,
        "abbr": "BOS",
        "city": "Boston",
        "name": "Celtics",
        "conference": "East",
    }]


def test_normalize_player_keeps_only_recognized_team() -> None:
    raw = [{
        "id": 115,
        "first_name": " Stephen ",
        "last_name": "Curry",
        "position": "G",
        "jersey_number": "30",
        "team": {"abbreviation": "GSW"},
    }]

    assert normalize_players(raw, {"GSW"}) == [{
        "balldontlie_id": 115,
        "name": "Stephen Curry",
        "team_abbr": "GSW",
        "position": "G",
        "jersey_number": "30",
    }]
    assert normalize_players(raw, {"BOS"}) == []


def test_normalize_scheduled_game() -> None:
    assert normalize_games([BASE_GAME])[0] == {
        "game_id": "bdl:15907925",
        "away_abbr": "BOS",
        "home_abbr": "LAL",
        "date": "2026-01-05",
        "start_time": "2026-01-05T23:00:00.000Z",
        "status": "scheduled",
        "status_text": "7:00 pm ET",
        "period": None,
        "clock": None,
        "away_score": None,
        "home_score": None,
        "venue": "",
        "season": "2025-26",
        "season_type": "regular",
    }


def test_normalize_live_game_scores_and_clock() -> None:
    live = {
        **BASE_GAME,
        "status": "3rd Qtr",
        "status_state": "in_progress",
        "period": 3,
        "time": "4:12",
        "visitor_team_score": 78,
        "home_team_score": 74,
    }

    game = normalize_games([live])[0]

    assert game["status"] == "live"
    assert game["period"] == 3
    assert game["clock"] == "4:12"
    assert (game["away_score"], game["home_score"]) == (78, 74)


def test_normalize_final_postseason_game() -> None:
    final = {
        **BASE_GAME,
        "status": "Final",
        "status_state": "final",
        "period": 4,
        "time": "Final",
        "postseason": True,
        "visitor_team_score": 105,
        "home_team_score": 115,
    }

    game = normalize_games([final])[0]

    assert game["status"] == "final"
    assert game["season_type"] == "playoffs"
    assert (game["away_score"], game["home_score"]) == (105, 115)


def test_unsupported_game_state_is_skipped_when_valid_game_exists() -> None:
    postponed = {
        **BASE_GAME,
        "id": 15907926,
        "status": "Postponed",
        "status_state": "postponed",
    }

    games = normalize_games([postponed, BASE_GAME])

    assert [game["game_id"] for game in games] == ["bdl:15907925"]


def test_nonempty_games_response_with_no_valid_game_is_rejected() -> None:
    unknown = {**BASE_GAME, "status_state": "unknown"}

    with pytest.raises(ValueError, match="valid games"):
        normalize_games([unknown])


@pytest.mark.parametrize(
    ("score_field", "invalid_score"),
    [
        ("visitor_team_score", None),
        ("visitor_team_score", -1),
        ("home_team_score", None),
        ("home_team_score", -1),
    ],
)
def test_live_game_requires_complete_nonnegative_scores(
    score_field: str,
    invalid_score: int | None,
) -> None:
    live = {
        **BASE_GAME,
        "status_state": "in_progress",
        "visitor_team_score": 78,
        "home_team_score": 74,
        score_field: invalid_score,
    }

    with pytest.raises(ValueError, match="valid games"):
        normalize_games([live])
