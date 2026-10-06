import importlib.util
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, inspect, text
from alembic.migration import MigrationContext
from alembic.operations import Operations


@pytest.mark.asyncio
async def test_response_includes_request_duration_without_query_data():
    from app.timing import RequestTimingMiddleware
    app = FastAPI()
    app.add_middleware(RequestTimingMiddleware)
    @app.get('/sample')
    async def sample():
        return {'ok': True}
    async with AsyncClient(transport=ASGITransport(app), base_url='http://test') as client:
        response = await client.get('/sample?token=secret')
    assert response.json() == {'ok': True}
    header = response.headers['Server-Timing']
    assert header.startswith('app;dur=') and float(header.split('=')[1]) >= 0
    assert 'secret' not in header


def test_schedule_indexes_upgrade_and_downgrade_preserve_rows():
    path = Path(__file__).parents[1] / 'alembic/versions/20261006_schedule_indexes.py'
    spec = importlib.util.spec_from_file_location('schedule_indexes', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    engine = create_engine('sqlite://')
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE games (id VARCHAR PRIMARY KEY, season VARCHAR, status VARCHAR, date VARCHAR, start_time TIMESTAMP)'))
        connection.execute(text("INSERT INTO games VALUES ('g','2025-26','final','2026-01-01',NULL)"))
        with Operations.context(MigrationContext.configure(connection)):
            module.upgrade()
        indexes = {i['name']: i['column_names'] for i in inspect(connection).get_indexes('games')}
        assert indexes['ix_games_season_status_date'] == ['season','status','date']
        assert indexes['ix_games_status_start_time'] == ['status','start_time']
        with Operations.context(MigrationContext.configure(connection)):
            module.downgrade()
        assert not inspect(connection).get_indexes('games')
        assert connection.execute(text('SELECT id FROM games')).scalar_one() == 'g'
    engine.dispose()


@pytest.mark.asyncio
async def test_manual_prediction_refresh_records_source_freshness(monkeypatch):
    from contextlib import asynccontextmanager
    from unittest.mock import AsyncMock
    from scripts import train_model
    from app.services import sync_status
    @asynccontextmanager
    async def database():
        yield object()
    recorder = AsyncMock()
    monkeypatch.setattr(train_model, 'SessionLocal', database)
    monkeypatch.setattr(train_model, 'sync_predictions', AsyncMock(return_value=123))
    monkeypatch.setattr(sync_status, 'record_sync_status', recorder)
    assert await train_model.refresh_predictions() == 123
    assert recorder.await_args_list[0].args == ('sync_predictions','running')
    assert recorder.await_args_list[-1].args == ('sync_predictions','success',123)
