"""Store optional away/home period scores including overtime."""
from alembic import op
import sqlalchemy as sa

revision = "20261006_period_scores"
down_revision = "20261004_game_seasons"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("games", sa.Column("period_scores", sa.JSON(), nullable=True))
    op.add_column("games", sa.Column("home_abbr", sa.String(5), nullable=True))
    games = sa.table("games", sa.column("id", sa.String), sa.column("team2", sa.String), sa.column("home_abbr", sa.String))
    # BALLDONTLIE has always been normalized away-first; older NBA history has not.
    op.execute(games.update().where(games.c.id.like("bdl:%")).values(home_abbr=games.c.team2))


def downgrade():
    op.drop_column("games", "home_abbr")
    op.drop_column("games", "period_scores")
