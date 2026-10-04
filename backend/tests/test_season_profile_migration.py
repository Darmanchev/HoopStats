import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text


def test_profile_migration_preserves_existing_season_and_is_reversible():
    path = Path(__file__).parents[1] / "alembic/versions/20261002_season_player_profiles.py"
    spec = importlib.util.spec_from_file_location("season_profile_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE player_season_stats (id INTEGER PRIMARY KEY, season VARCHAR(7))"))
        connection.execute(text("INSERT INTO player_season_stats VALUES (1, '2024-25')"))
        with Operations.context(MigrationContext.configure(connection)):
            module.upgrade()
        assert connection.execute(text("SELECT season, position, jersey_number FROM player_season_stats")).one() == ("2024-25", None, None)
        with Operations.context(MigrationContext.configure(connection)):
            module.downgrade()
        assert {column["name"] for column in inspect(connection).get_columns("player_season_stats")} == {"id", "season"}
    engine.dispose()
