"""Repair recognizable legacy NBA games and require explicit seasons.

NBA IDs encode game type and the two-digit season start year. Only IDs with
an unambiguous century consistent with the stored calendar date are repaired.
Unknown formats (including BALLDONTLIE IDs) are deliberately left unchanged.
Downgrading restores the old default, not the incorrect historical labels.
"""
from datetime import date
import logging
import re

from alembic import op
import sqlalchemy as sa

revision = "20261004_game_seasons"
down_revision = "20261002_season_profiles"
branch_labels = None
depends_on = None

GAME_TYPES = {"001": "preseason", "002": "regular", "004": "playoffs", "005": "playoffs"}


def upgrade():
    games = sa.table("games", sa.column("id", sa.String),
        sa.column("date", sa.String), sa.column("season", sa.String),
        sa.column("season_type", sa.String))
    connection = op.get_bind()
    repaired = 0
    skipped = 0
    for row in connection.execute(sa.select(games)).mappings().all():
        game_id = row["id"]
        if not re.fullmatch(r"00[1245][0-9]{7}", game_id):
            continue
        try:
            calendar_year = date.fromisoformat(row["date"]).year
        except (ValueError, TypeError):
            skipped += 1
            continue
        # Supports January-June games and the delayed 2019-20 season, without
        # assuming every game after a particular month belongs to a new season.
        candidates = [year for year in (calendar_year - 1, calendar_year)
                      if year % 100 == int(game_id[3:5]) and year >= 1946]
        if len(candidates) != 1:
            skipped += 1
            continue
        year = candidates[0]
        season = f"{year}-{(year + 1) % 100:02d}"
        kind = GAME_TYPES[game_id[:3]]
        if (row["season"], row["season_type"]) != (season, kind):
            connection.execute(games.update().where(games.c.id == game_id)
                .values(season=season, season_type=kind))
            repaired += 1
    logging.getLogger("alembic.runtime.migration").info(
        "Repaired %d legacy NBA games; skipped %d ambiguous records", repaired, skipped)
    with op.batch_alter_table("games") as batch:
        batch.alter_column("season", existing_type=sa.String(7), server_default=None)


def downgrade():
    # A schema rollback must not deliberately corrupt corrected season data.
    with op.batch_alter_table("games") as batch:
        batch.alter_column("season", existing_type=sa.String(7), server_default="2025-26")
