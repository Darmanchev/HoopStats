import json
from pathlib import Path

import pytest

from app.ml import train
from test_ml_improvements import training_games


def test_training_publishes_each_eligible_holdout_season(tmp_path, monkeypatch):
    rows = training_games()
    rows += [{**g, 'id': 'next-' + g['id'], 'date': g['date'].replace('2024-', '2025-'), 'season': '2025-26'} for g in rows if g['season'] == '2024-25']
    monkeypatch.setattr(train, 'MODEL_PATH', tmp_path / 'model.joblib')
    train.train(rows)
    older = json.loads((tmp_path / 'evaluation-2024-25.json').read_text())
    newer = json.loads((tmp_path / 'evaluation-2025-26.json').read_text())
    assert older['n_train'] < newer['n_train']
    assert {g['season'] for g in older['games']} == {'2024-25'}
    assert {g['season'] for g in newer['games']} == {'2025-26'}
    assert json.loads((tmp_path / 'evaluation.json').read_text()) == newer


def test_read_performance_selects_archive_before_paginating(tmp_path, monkeypatch):
    from app.ml.performance import read_performance
    monkeypatch.setattr(train, 'MODEL_PATH', tmp_path / 'model.joblib')
    train.train(training_games())
    result = read_performance(tmp_path / 'evaluation.json', season='2024-25', skip=100, limit=10)
    assert result['seasons'] == ['2024-25']
    assert result['selected_season'] == '2024-25'
    assert result['total'] == 120 and len(result['games']) == 10
    assert result['season_metrics'] == result['metrics']


def test_unavailable_and_invalid_archive_do_not_break_performance(tmp_path):
    from app.ml.performance import read_performance
    (tmp_path / 'evaluation-2024-25.json').write_text('invalid')
    result = read_performance(tmp_path / 'evaluation.json')
    assert result['available'] is False and result['seasons'] == []
    assert read_performance(tmp_path / 'evaluation.json', season='../../secret')['available'] is False
