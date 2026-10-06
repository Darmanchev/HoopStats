"""Match official NBA scoreboard games to local provider IDs before importing stats."""
import asyncio
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.cache import invalidate_live_caches
from app.models.game import Game
from app.services.clients import nba
from app.services.repositories.player_game_stats import upsert_player_game_stats


def match_official_game(game: Game, scoreboard: list[dict]) -> str | None:
    # NBA uses the Eastern calendar date, even when tip-off is after midnight UTC.
    game_date = game.date
    if game.start_time:
        start = game.start_time
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        game_date = start.astimezone(ZoneInfo("America/New_York")).date().isoformat()
    matches = [row["game_id"] for row in scoreboard
               if row["away_abbr"] == game.team1 and row["home_abbr"] == game.team2
               and row["date"] == game_date and row["status"] in {"live", "final"}]
    return matches[0] if len(matches) == 1 else None


async def sync_box_scores(db) -> int:
    since = (datetime.now(timezone.utc) - timedelta(days=2)).date().isoformat()
    games = (await db.execute(select(Game).where(
        Game.date >= since,
        Game.date <= datetime.now(timezone.utc).date().isoformat(),
    ))).scalars().all()
    if not games:
        return 0
    scoreboard = await asyncio.to_thread(nba.fetch_live_scoreboard)
    affected = []
    imported = 0
    unmatched_live = []
    for game in games:
        official_id = match_official_game(game, scoreboard)
        if official_id is None:
            if game.status == "live":
                unmatched_live.append(game.id)
            continue
        rows = await asyncio.to_thread(nba.fetch_live_boxscore, official_id)
        if not rows or any(row["game_id"] != official_id or row["team_abbr"] not in {game.team1, game.team2} for row in rows):
            raise ValueError(f"Missing or mismatched NBA box score for {game.id}")
        official_game = next(row for row in scoreboard if row["game_id"] == official_id)
        game.is_today = True
        game.status = official_game["status"]
        game.status_text = official_game.get("status_text", "")
        game.period = official_game.get("period")
        game.clock = official_game.get("clock")
        game.score1 = official_game.get("away_score")
        game.score2 = official_game.get("home_score")
        rows = [{**row, "game_id": game.id} for row in rows]
        imported += await upsert_player_game_stats(db, game.id, rows)
        affected.append(game.id)
    await db.commit()
    if affected:
        await invalidate_live_caches(affected)
    if unmatched_live:
        raise ValueError("Official NBA IDs unavailable for live games: " + ", ".join(unmatched_live))
    return imported
