"""Train a versioned logistic model and publish chronological evaluation."""
import json
from pathlib import Path
import os
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .features import FEATURE_NAMES, FEATURE_VERSION, build_training_rows
from .evaluation import atomic_write, build_report, unavailable_report

MODEL_PATH = Path(os.environ.get("HOOPSTATS_MODEL_DIR", str(Path(__file__).parent))) / "model.joblib"


def _make_model():
    return make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=1000))


def fit_symmetric(model, x, y):
    # All provider rows are away-first. Mirroring gives the home indicator
    # both signs and ensures swapping the teams complements the prediction.
    mirrored = [[-value for value in row] for row in x]
    model.fit(x + mirrored, y + [1 - outcome for outcome in y])
    return model


def train(games: list[dict]) -> dict:
    x, y, seasons, metadata = build_training_rows(games, with_metadata=True)
    if len(x) < 200:
        raise ValueError(f"At least 200 eligible training rows required; found {len(x)}")
    if len(set(y)) < 2:
        raise ValueError("Training requires both winning and losing outcomes")
    test_season = sorted(set(seasons))[-1]
    train_indices = [i for i, season in enumerate(seasons) if season != test_season]
    test_indices = [i for i, season in enumerate(seasons) if season == test_season]
    reports = {}
    for season in sorted(set(seasons)):
        earlier = [i for i, value in enumerate(seasons) if value < season]
        held_out = [i for i, value in enumerate(seasons) if value == season]
        if earlier and held_out and len({y[i] for i in earlier}) == 2:
            evaluator = _make_model()
            fit_symmetric(evaluator, [x[i] for i in earlier], [y[i] for i in earlier])
            reports[season] = build_report(
                evaluator, [x[i] for i in held_out], [y[i] for i in held_out],
                [metadata[i] for i in held_out], len(earlier), season,
            )
    report = reports.get(test_season) or unavailable_report(test_season, len(train_indices), len(test_indices))
    model = _make_model()
    fit_symmetric(model, x, y)
    bundle = {"model": model, "features": FEATURE_NAMES, "feature_version": FEATURE_VERSION, "trained_at": report["trained_at"]}
    atomic_write(MODEL_PATH, lambda file: joblib.dump(bundle, file))
    for season, season_report in reports.items():
        atomic_write(MODEL_PATH.with_name(f"evaluation-{season}.json"),
            lambda file, value=season_report: Path(file).write_text(json.dumps(value, allow_nan=False)))
    atomic_write(MODEL_PATH.with_name("evaluation.json"), lambda file: Path(file).write_text(json.dumps(report, allow_nan=False)))
    return {"test_season": test_season, "n_train": len(train_indices), "n_test": len(test_indices),
        "n_total": len(x), "evaluation_available": report["available"], **(report["metrics"] or {}), "model_path": str(MODEL_PATH)}
