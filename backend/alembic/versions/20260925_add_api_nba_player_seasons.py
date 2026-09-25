"""add API-NBA provider IDs and player season statistics

Revision ID: 20260925_api_nba_player_seasons
Revises: 20260923_balldontlie_ids
Create Date: 2026-09-25 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260925_api_nba_player_seasons"
down_revision: Union[str, Sequence[str], None] = "20260923_balldontlie_ids"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("teams", sa.Column("api_nba_id", sa.Integer(), nullable=True))
    op.create_unique_constraint(
        "uq_teams_api_nba_id",
        "teams",
        ["api_nba_id"],
    )
    op.add_column("players", sa.Column("api_nba_id", sa.Integer(), nullable=True))
    op.create_unique_constraint(
        "uq_players_api_nba_id",
        "players",
        ["api_nba_id"],
    )
    op.create_table(
        "player_season_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("season", sa.String(length=7), nullable=False),
        sa.Column("primary_team_abbr", sa.String(length=5), nullable=False),
        sa.Column("games_played", sa.Integer(), nullable=False),
        sa.Column("pts", sa.Float(), nullable=False),
        sa.Column("reb", sa.Float(), nullable=False),
        sa.Column("ast", sa.Float(), nullable=False),
        sa.Column("stl", sa.Float(), nullable=False),
        sa.Column("blk", sa.Float(), nullable=False),
        sa.Column("fg_pct", sa.Float(), nullable=False),
        sa.Column("fg3_pct", sa.Float(), nullable=False),
        sa.Column("ft_pct", sa.Float(), nullable=False),
        sa.Column("mins", sa.Float(), nullable=False),
        sa.Column("recent_games", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["primary_team_abbr"], ["teams.abbr"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "player_id",
            "season",
            name="uq_player_season_stats_player_season",
        ),
    )
    op.create_index(
        "ix_player_season_stats_player_id",
        "player_season_stats",
        ["player_id"],
        unique=False,
    )
    op.create_index(
        "ix_player_season_stats_primary_team_abbr",
        "player_season_stats",
        ["primary_team_abbr"],
        unique=False,
    )
    op.create_index(
        "ix_player_season_stats_season",
        "player_season_stats",
        ["season"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_player_season_stats_season", table_name="player_season_stats")
    op.drop_index(
        "ix_player_season_stats_primary_team_abbr",
        table_name="player_season_stats",
    )
    op.drop_index("ix_player_season_stats_player_id", table_name="player_season_stats")
    op.drop_table("player_season_stats")
    op.drop_constraint("uq_players_api_nba_id", "players", type_="unique")
    op.drop_column("players", "api_nba_id")
    op.drop_constraint("uq_teams_api_nba_id", "teams", type_="unique")
    op.drop_column("teams", "api_nba_id")
