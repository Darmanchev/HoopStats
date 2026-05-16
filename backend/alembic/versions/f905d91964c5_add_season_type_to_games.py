"""add_season_type_to_games

Revision ID: f905d91964c5
Revises: 763d27e46f90
Create Date: 2026-05-16 02:00:16.165503

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f905d91964c5'
down_revision: Union[str, Sequence[str], None] = '763d27e46f90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('games', sa.Column('season_type', sa.String(20), server_default='regular'))


def downgrade() -> None:
    op.drop_column('games', 'season_type')
