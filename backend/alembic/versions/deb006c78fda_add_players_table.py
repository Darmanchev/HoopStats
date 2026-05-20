"""add_players_table

Revision ID: deb006c78fda
Revises: f905d91964c5
Create Date: 2026-05-16 22:28:32.148993

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'deb006c78fda'
down_revision: Union[str, Sequence[str], None] = 'f905d91964c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('players',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nba_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('team_abbr', sa.String(length=5), nullable=False),
        sa.Column('position', sa.String(length=5), nullable=False),
        sa.Column('jersey_number', sa.String(length=5), nullable=True),
        sa.Column('games_played', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('pts', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('reb', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('ast', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('stl', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('blk', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('fg_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('fg3_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('ft_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('mins', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('recent_games', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nba_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('players')
