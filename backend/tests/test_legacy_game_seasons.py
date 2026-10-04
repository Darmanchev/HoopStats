"""Regression coverage for the mislabeled October 2026 preseason game."""
import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.models.game import Game
from app.schemas.game import PastGameSchema


def test_migration_repairs_only_recognized_nba_ids():
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    games = sa.Table("games", metadata,
        sa.Column("id", sa.String(20), primary_key=True),
        sa.Column("date", sa.String(10), nullable=False),
        sa.Column("season", sa.String(7), nullable=False, server_default="2025-26"),
        sa.Column("season_type", sa.String(20), nullable=False),
        sa.Column("score1", sa.Integer), sa.Column("score2", sa.Integer))
    metadata.create_all(engine)
    cases = [
        ("0012600009", "2026-10-03", "2026-27", "preseason"),
        ("0022400001", "2024-10-22", "2024-25", "regular"),
        ("0042300001", "2024-04-20", "2023-24", "playoffs"),
        ("0052300001", "2024-04-16", "2023-24", "playoffs"),
        ("0021900001", "2020-08-01", "2019-20", "regular"),
        ("0029900001", "2000-01-01", "1999-00", "regular"),
        ("bdl:123", "2026-10-03", "2025-26", "regular"),
        ("unknown", "2026-10-03", "2025-26", "regular"),
        ("001260000", "2026-10-03", "2025-26", "regular"),
        ("0012600008", "not-a-date", "2025-26", "regular"),
        ("0022400002", "2026-10-03", "2025-26", "regular"),
        ("0032600001", "2027-02-01", "2025-26", "regular"),
    ]
    with engine.begin() as connection:
        connection.execute(games.insert(), [dict(id=id, date=date,
            season="2025-26", season_type="regular", score1=129, score2=105)
            for id, date, _, _ in cases])
        path = Path(__file__).parents[1] / "alembic/versions/20261004_repair_legacy_game_seasons.py"
        spec = importlib.util.spec_from_file_location("repair_game_seasons", path)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = {row.id: row for row in connection.execute(sa.select(games))}
        for id, _, season, kind in cases:
            assert (rows[id].season, rows[id].season_type) == (season, kind)
            assert (rows[id].score1, rows[id].score2) == (129, 105)
        # Raw inserts cannot silently inherit the old season after the migration.
        with pytest.raises(IntegrityError):
            connection.execute(games.insert().values(id="no-season", date="2026-10-03", season_type="regular"))
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        corrected = connection.execute(sa.select(games).where(games.c.id == "0012600009")).one()
        assert (corrected.season, corrected.season_type) == ("2026-27", "preseason")
        connection.execute(games.insert().values(id="rollback-default", date="2026-10-03", season_type="regular"))
        assert connection.execute(sa.select(games.c.season).where(games.c.id == "rollback-default")).scalar_one() == "2025-26"
    engine.dispose()


@pytest.mark.asyncio
async def test_game_insert_requires_an_explicit_season(db_session):
    db_session.add(Game(id="missing-season", date="2026-10-03", time="Final", venue=""))
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


def test_game_response_requires_season_and_accepts_preseason():
    payload = dict(id="0012600009", team1="MIA", team2="TOR", date="2026-10-03",
                   time="Final", venue="", score1=129, score2=105)
    with pytest.raises(ValidationError):
        PastGameSchema(**payload)
    game = PastGameSchema(**payload, season="2026-27", season_type="preseason")
    assert game.season == "2026-27"
    assert game.season_type == "preseason"
