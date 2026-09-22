"""add normalized game start time

Revision ID: 20260922_game_start_time
Revises: 20260921_live_dashboard
Create Date: 2026-09-22 00:50:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260922_game_start_time"
down_revision: Union[str, Sequence[str], None] = "20260921_live_dashboard"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "games",
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_games_start_time"),
        "games",
        ["start_time"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_games_start_time"), table_name="games")
    op.drop_column("games", "start_time")
