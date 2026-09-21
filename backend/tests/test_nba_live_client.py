import json
from pathlib import Path

import pytest

from app.services.clients import nba as nba_client


FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_parse_scoreboard_skips_invalid_games_and_normalizes_live_state() -> None:
    games = nba_client.parse_live_scoreboard(load_fixture("live_scoreboard.json"))

    assert games[1] == {
        "game_id": "0022500002",
        "away_abbr": "BOS",
        "home_abbr": "LAL",
        "date": "2026-09-21",
        "start_time": "2026-09-21T22:00:00Z",
        "status": "live",
        "status_text": "Q3 04:12",
        "period": 3,
        "clock": "PT04M12.00S",
        "away_score": 78,
        "home_score": 74,
        "venue": "Crypto.com Arena",
    }
    assert len(games) == 2


def test_parse_boxscore_returns_both_teams_players() -> None:
    players = nba_client.parse_live_boxscore(load_fixture("live_boxscore.json"))

    assert len(players) == 2
    assert players[0] == {
        "game_id": "0022500002",
        "nba_id": 2544,
        "name": "LeBron James",
        "team_abbr": "BOS",
        "points": 22,
        "rebounds": 7,
        "assists": 8,
        "steals": 2,
        "blocks": 1,
        "minutes": 32.5,
    }


def test_parse_standings_returns_dashboard_fields() -> None:
    data = {
        "resultSets": [
            {
                "headers": [
                    "TeamID",
                    "WINS",
                    "LOSSES",
                    "Conference",
                    "PlayoffRank",
                    "L10",
                    "strCurrentStreak",
                ],
                "rowSet": [[1610612738, 52, 20, "East", 2, "7-3", "W 3"]],
            }
        ]
    }

    standings = nba_client.parse_standings(data)

    assert standings[1610612738] == {
        "record": "52-20",
        "conference": "East",
        "conference_rank": 2,
        "last_ten": "7-3",
        "streak": "W3",
    }


def test_invalid_scoreboard_envelope_is_not_treated_as_empty_day() -> None:
    with pytest.raises(ValueError, match="scoreboard"):
        nba_client.parse_live_scoreboard({})


def test_nonempty_scoreboard_with_only_invalid_entries_is_rejected() -> None:
    with pytest.raises(ValueError, match="valid games"):
        nba_client.parse_live_scoreboard({"scoreboard": {"games": [None]}})


@pytest.mark.parametrize("away_score", [None, -1])
def test_final_scoreboard_game_requires_both_nonnegative_scores(
    away_score: int | None,
) -> None:
    data = {
        "scoreboard": {
            "games": [{
                "gameId": "game-1",
                "gameEt": "2026-09-21T22:00:00Z",
                "gameStatus": 3,
                "gameStatusText": "Final",
                "awayTeam": {"teamTricode": "BOS", "score": away_score},
                "homeTeam": {"teamTricode": "LAL", "score": 104},
            }]
        }
    }

    with pytest.raises(ValueError, match="valid games"):
        nba_client.parse_live_scoreboard(data)


def test_boxscore_skips_players_without_statistics() -> None:
    data = {
        "game": {
            "gameId": "game-1",
            "awayTeam": {
                "teamTricode": "BOS",
                "players": [{"personId": 1, "name": "Missing Stats"}],
            },
            "homeTeam": {"teamTricode": "LAL", "players": []},
        }
    }

    assert nba_client.parse_live_boxscore(data) == []


def test_boxscore_skips_incomplete_statistics() -> None:
    data = {
        "game": {
            "gameId": "game-1",
            "awayTeam": {
                "teamTricode": "BOS",
                "players": [{
                    "personId": 1,
                    "name": "Incomplete Stats",
                    "statistics": {"points": 12},
                }],
            },
            "homeTeam": {"teamTricode": "LAL", "players": []},
        }
    }

    assert nba_client.parse_live_boxscore(data) == []
