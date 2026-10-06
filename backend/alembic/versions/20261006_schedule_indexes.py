"""Support filtered schedule ordering and upcoming game lookups."""
from alembic import op

revision = '20261006_schedule_indexes'
down_revision = '20261006_period_scores'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_games_season_status_date', 'games', ['season', 'status', 'date'])
    op.create_index('ix_games_status_start_time', 'games', ['status', 'start_time'])


def downgrade():
    op.drop_index('ix_games_status_start_time', table_name='games')
    op.drop_index('ix_games_season_status_date', table_name='games')
