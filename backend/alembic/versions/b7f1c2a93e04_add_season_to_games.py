"""add_season_to_games

Revision ID: b7f1c2a93e04
Revises: e783596e4ef2
Create Date: 2026-05-20 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7f1c2a93e04'
down_revision: Union[str, Sequence[str], None] = 'e783596e4ef2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default='2025-26' заполнит уже существующие игры (все они сезона
    # 2025-26); новые сезоны sync-функции записывают со своим значением.
    op.add_column(
        'games',
        sa.Column('season', sa.String(7), nullable=False, server_default='2025-26'),
    )
    op.create_index('ix_games_season', 'games', ['season'])


def downgrade() -> None:
    op.drop_index('ix_games_season', table_name='games')
    op.drop_column('games', 'season')
