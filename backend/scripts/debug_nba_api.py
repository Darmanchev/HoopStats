#!/usr/bin/env python
"""Тест NBA API endpoints для отладки"""
from nba_api.stats.endpoints import leaguedashplayerstats
from nba_api.stats.static import teams as nba_teams
from nba_api.stats.endpoints import teamgamelog, leaguestandings, leaguegamefinder
import json
def test_player_stats():
    """Тестирует LeagueDashPlayerStats и выводит колонки"""
    print("=== Testing LeagueDashPlayerStats ===")
    try:
        stats = leaguedashplayerstats.LeagueDashPlayerStats(
            season="2025",
            season_type_nullable="Regular Season",
            per_mode_detailed="PerGame",
        )
        data = stats.get_dict()
        result_sets = data.get("resultSets", [])
        if result_sets:
            headers = result_sets[0].get("headers", [])
            rows = result_sets[0].get("rowSet", [])
            print(f"Headers ({len(headers)}): {headers}")
            if rows:
                print(f"\nFirst row as dict:")
                print(json.dumps(dict(zip(headers, rows[0])), indent=2))
            print(f"\nTotal rows: {len(rows)}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
def test_teams():
    """Тестирует получение команд"""
    print("\n=== Testing Teams ===")
    try:
        teams = nba_teams.get_teams()
        print(f"Teams: {len(teams)}")
        if teams:
            print(f"First team: {teams[0]}")
    except Exception as e:
        print(f"Error: {e}")
def test_team_gamelog():
    """Тестирует TeamGameLog"""
    print("\n=== Testing TeamGameLog ===")
    try:
        log = teamgamelog.TeamGameLog(team_id="1610612738", season="2025")  # BOS
        data = log.get_dict()
        result_sets = data.get("resultSets", [])
        if result_sets:
            headers = result_sets[0].get("headers", [])
            rows = result_sets[0].get("rowSet", [])
            print(f"Headers: {headers}")
            if rows:
                print(f"First game: {dict(zip(headers, rows[0]))}")
    except Exception as e:
        print(f"Error: {e}")
if __name__ == "__main__":
    test_teams()
    test_team_gamelog()
    test_player_stats()