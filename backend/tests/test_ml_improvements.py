from datetime import date
import pytest
from app.ml import features


class ArtifactModel:
    def __init__(self, label):
        self.label = label

    def predict_proba(self, rows):
        return [[.5, .5] for _ in rows]


def test_history_excludes_preseason_live_ties_and_missing_teams():
    rows = [{"team1":"BOS", "team2":"LAL", "date":"2025-01-01", "season":"2024-25", "season_type":"preseason", "status":"final", "score1":100, "score2":90}]
    state = features.build_state(rows)
    assert not state.elo
    for field, value in [("status", "live"), ("score2", 100), ("team1", None)]:
        state = features.build_state([{**rows[0], "season_type":"regular", field:value}])
        assert not state.elo


def test_season_regression_is_applied_before_first_feature():
    state = features.LeagueState()
    state.record({"team1":"BOS", "team2":"LAL", "date":"2025-01-01", "season":"2024-25", "score1":100, "score2":90})
    old_difference = state.elo["BOS"] - state.elo["LAL"]
    state.prepare_season("2025-26")
    vector = state.feature_vector("BOS", "LAL", date(2025,10,1))
    assert vector[3] == pytest.approx(old_difference * .75)


def test_nba_period_scores_are_normalized_without_invention():
    from app.services.clients.nba import parse_period_scores
    assert parse_period_scores({"periods":[{"period":1,"score":20}]}, {"periods":[{"period":1,"score":25}]}) == [{"period":1,"score1":20,"score2":25}]
    assert parse_period_scores({}, {}) is None
    assert parse_period_scores({"periods":[{"period":1,"score":-1}]}, {"periods":[{"period":1,"score":25}]}) is None


def test_home_and_rest_features_use_only_known_past_dates():
    state = features.LeagueState()
    state.record({"team1":"BOS","team2":"NYK","date":"2025-01-01","season":"2024-25","score1":100,"score2":90})
    state.record({"team1":"LAL","team2":"NYK","date":"2025-01-03","season":"2024-25","score1":100,"score2":90})
    vector = state.feature_vector("BOS","LAL",date(2025,1,5), home_team="LAL")
    assert vector[-2:] == [-1.0, 2.0]
    assert state.feature_vector("BOS","LAL",date(2025,2,1), home_team="BOS")[-2:] == [1.0,0.0]
    assert state.feature_vector("UNKNOWN","LAL",date(2025,1,5))[-2:] == [0.0,0.0]


def test_legacy_artifact_is_rejected_and_replacement_reloaded(tmp_path, monkeypatch):
    import joblib
    from app.ml import predict
    path = tmp_path / "model.joblib"
    monkeypatch.setattr(predict, "MODEL_PATH", path)
    monkeypatch.setattr(predict, "_bundle", None)
    joblib.dump({"model":"old","features":["d_elo"]},path)
    with pytest.raises(predict.ModelUnavailableError, match="retrain"):
        predict.load_model()
    joblib.dump({"model":ArtifactModel("new"),"features":features.FEATURE_NAMES,"feature_version":features.FEATURE_VERSION},path)
    assert predict.load_model()["model"].label == "new"
    joblib.dump({"model":ArtifactModel("replacement"),"features":features.FEATURE_NAMES,"feature_version":features.FEATURE_VERSION},path)
    assert predict.load_model()["model"].label == "replacement"


def training_games():
    from datetime import timedelta
    rows = []
    for season, year in [("2023-24",2023),("2024-25",2024)]:
        for i in range(120):
            rows.append({"id":f"{year}-{i}","team1":"BOS","team2":"LAL","date":(date(year,10,1)+timedelta(days=i)).isoformat(),"season":season,"season_type":"regular","status":"final","score1":100 if i%3 else 90,"score2":95,"home_team":"LAL"})
    return rows


def test_training_report_is_held_out_and_has_calibration(tmp_path, monkeypatch):
    import json
    from app.ml import train
    monkeypatch.setattr(train, "MODEL_PATH",tmp_path / "model.joblib")
    metrics = train.train(training_games())
    report = json.loads((tmp_path / "evaluation.json").read_text())
    assert report["test_season"] == "2024-25"
    assert report["n_train"] > 0 and report["n_test"] == 120
    assert len(report["calibration"]) == 10
    assert sum(bin["count"] for bin in report["calibration"]) == report["n_test"]
    assert 0 <= report["metrics"]["brier"] <= 1
    assert len(report["games"]) == report["n_test"]
    assert "elo" in report["baselines"] and "home" in report["baselines"]
    assert metrics["n_total"] > 200


def test_home_advantage_is_learnable_with_away_first_provider_rows(tmp_path, monkeypatch):
    import joblib
    from app.ml import train
    monkeypatch.setattr(train, "MODEL_PATH", tmp_path / "model.joblib")
    rows = training_games()
    for i,row in enumerate(rows):
        # Home wins 80% of games while both teams have enough history.
        row["score1"] = 100 if i%5 == 0 else 90
        row["score2"] = 95
    train.train(rows)
    model = joblib.load(tmp_path / "model.joblib")["model"]
    home = [0.0]*len(features.FEATURE_NAMES)
    away = home.copy()
    home[-2], away[-2] = 1.0,-1.0
    p_home = model.predict_proba([home])[0][1]
    p_away = model.predict_proba([away])[0][1]
    assert p_home > p_away
    assert p_home + p_away == pytest.approx(1.0, abs=.01)


def test_future_results_do_not_change_earlier_training_features():
    rows = training_games()
    x,y,seasons = features.build_training_rows(rows)
    changed = [dict(row) for row in rows]
    changed[-1]["score1"] = 120
    other_x,other_y,_ = features.build_training_rows(changed)
    assert x == other_x
    assert y[:-1] == other_y[:-1]


def test_period_scores_migration_preserves_data_and_reverses():
    import importlib.util
    from pathlib import Path
    from sqlalchemy import create_engine, text, inspect
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    path = Path(__file__).parents[1] / "alembic/versions/20261006_game_period_scores.py"
    spec = importlib.util.spec_from_file_location("period_migration",path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE games (id VARCHAR PRIMARY KEY, score1 INTEGER, team2 VARCHAR)"))
        connection.execute(text("INSERT INTO games VALUES ('g',100,'LAL')"))
        with Operations.context(MigrationContext.configure(connection)):
            module.upgrade()
        assert connection.execute(text("SELECT score1,period_scores FROM games")).one() == (100,None)
        with Operations.context(MigrationContext.configure(connection)):
            module.downgrade()
        assert {column["name"] for column in inspect(connection).get_columns("games")} == {"id","score1","team2"}
    engine.dispose()


@pytest.mark.asyncio
async def test_prediction_sync_uses_only_results_before_fixture_date(db_session, monkeypatch):
    from app.models import Game
    from app.services import predictions
    records = []
    for id,day,status in [("before","2025-01-01","final"),("after","2025-01-03","final"),("fixture","2025-01-02","scheduled")]:
        db_session.add(Game(id=id,team1="BOS",team2="LAL",date=day,time="",venue="",season="2024-25",season_type="regular",status=status,score1=100 if status=="final" else None,score2=90 if status=="final" else None))
    await db_session.commit()
    def predict(state,*args):
        records.append(state.hist["BOS"].count)
        return 55.0,"Prediction"
    monkeypatch.setattr(predictions,"predict_game",predict)
    await predictions.sync_predictions(db_session)
    assert records == [1]


def test_ambiguous_legacy_home_team_is_not_guessed():
    from types import SimpleNamespace
    row = SimpleNamespace(id="0022500001",team1="BOS",team2="LAL",home_abbr=None)
    assert features.verified_home(row) is None
    row.home_abbr = "BOS"
    assert features.verified_home(row) == "BOS"


@pytest.mark.parametrize("invalid_field",["auc","calibration"])
def test_invalid_evaluation_shape_is_unavailable(tmp_path, monkeypatch, invalid_field):
    import json
    from app.ml import train
    from app.ml.evaluation import read_report
    monkeypatch.setattr(train, "MODEL_PATH", tmp_path / "model.joblib")
    train.train(training_games())
    path = tmp_path / "evaluation.json"
    report = json.loads(path.read_text())
    assert read_report(path) is not None
    if invalid_field == "auc":
        report["metrics"]["auc"] = "invalid"
    else:
        report["calibration"] = [None] * 10
    path.write_text(json.dumps(report))
    assert read_report(path) is None


def test_prediction_explanation_mentions_verified_home_and_real_sample_size():
    from app.ml.predict import _explain
    state = features.LeagueState()
    for i in range(2):
        state.record({"team1":"BOS","team2":"LAL","date":f"2025-01-0{i+1}","season":"2024-25","score1":100,"score2":90})
    text = _explain("BOS","LAL",60,state,home_team="BOS",game_date=date(2025,1,5))
    assert "home court" in text
    assert "2-0 vs 0-2 last 2" in text
    assert "L10" not in text


def test_corrupt_model_bundle_is_rejected_before_prediction(tmp_path,monkeypatch):
    import joblib
    from app.ml import predict
    path=tmp_path / "model.joblib"
    monkeypatch.setattr(predict,"MODEL_PATH",path)
    joblib.dump({"features":features.FEATURE_NAMES,"feature_version":features.FEATURE_VERSION,"model":None},path)
    with pytest.raises(predict.ModelUnavailableError):
        predict.load_model()


@pytest.mark.asyncio
async def test_training_command_uses_one_event_loop_for_database_operations(monkeypatch, capsys):
    import asyncio
    from scripts import train_model
    loops = []
    async def load():
        loops.append(asyncio.get_running_loop())
        return [{"id": "fixture"}]
    async def refresh():
        loops.append(asyncio.get_running_loop())
        return 1
    monkeypatch.setattr(train_model, "load_played_games", load)
    monkeypatch.setattr(train_model, "refresh_predictions", refresh)
    monkeypatch.setattr(train_model, "train", lambda rows: {"n_total": len(rows)})
    await train_model.main()
    assert loops == [asyncio.get_running_loop(), asyncio.get_running_loop()]
    assert "Refreshed 1 predictions" in capsys.readouterr().out
