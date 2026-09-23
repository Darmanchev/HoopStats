"""add BALLDONTLIE provider identifiers

Revision ID: 20260923_balldontlie_ids
Revises: 20260922_game_start_time
Create Date: 2026-09-23 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260923_balldontlie_ids"
down_revision: Union[str, Sequence[str], None] = "20260922_game_start_time"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "teams",
        sa.Column("balldontlie_id", sa.Integer(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_teams_balldontlie_id",
        "teams",
        ["balldontlie_id"],
    )
    op.add_column(
        "players",
        sa.Column("balldontlie_id", sa.Integer(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_players_balldontlie_id",
        "players",
        ["balldontlie_id"],
    )
    op.alter_column(
        "players",
        "nba_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    connection = op.get_bind()
    missing_official_id = connection.execute(
        sa.text("SELECT 1 FROM players WHERE nba_id IS NULL LIMIT 1")
    ).first()
    if missing_official_id is not None:
        raise RuntimeError(
            "Cannot downgrade while players without official NBA IDs exist"
        )

    op.alter_column(
        "players",
        "nba_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.drop_constraint(
        "uq_players_balldontlie_id",
        "players",
        type_="unique",
    )
    op.drop_column("players", "balldontlie_id")
    op.drop_constraint(
        "uq_teams_balldontlie_id",
        "teams",
        type_="unique",
    )
    op.drop_column("teams", "balldontlie_id")
