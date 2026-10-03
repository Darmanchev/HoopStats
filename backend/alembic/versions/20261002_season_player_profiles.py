"""Store player profile fields per season.

Existing historical profile values cannot be reconstructed reliably;
NULL values use the legacy shared profile until the season is reimported.
"""
from alembic import op
import sqlalchemy as sa

revision = "20261002_season_profiles"
down_revision = "20260925_api_nba_player_seasons"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("player_season_stats", sa.Column("position", sa.String(10), nullable=True))
    op.add_column("player_season_stats", sa.Column("jersey_number", sa.String(10), nullable=True))


def downgrade():
    op.drop_column("player_season_stats", "jersey_number")
    op.drop_column("player_season_stats", "position")
