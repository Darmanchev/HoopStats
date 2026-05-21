"""Обучение модели прогнозирования исходов матчей.

Модель — логистическая регрессия. Зависимость Elo→вероятность победы по
своей природе логистическая, поэтому LR здесь точнее градиентного бустинга
(бустинг на этих признаках переобучается). Признаки масштабируются
StandardScaler — у них очень разный масштаб (d_elo ~±300, d_winpct ~±0.5).

Оценка — на последнем сезоне (out-of-sample по времени).
"""
from pathlib import Path

import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .features import FEATURE_NAMES, build_training_rows

MODEL_PATH = Path(__file__).parent / "model.joblib"


def _make_model():
    """Пайплайн: масштабирование признаков + логистическая регрессия."""
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(C=1.0, max_iter=1000),
    )


def train(games: list[dict]) -> dict:
    """Обучает модель на сыгранных играх, сохраняет в model.joblib.

    Возвращает метрики на тесте (последний сезон).
    """
    X, y, seasons = build_training_rows(games)
    if len(X) < 200:
        raise ValueError(f"Слишком мало данных для обучения: {len(X)} строк")

    test_season = sorted(set(seasons))[-1]
    Xtr = [x for x, s in zip(X, seasons) if s != test_season]
    ytr = [v for v, s in zip(y, seasons) if s != test_season]
    Xte = [x for x, s in zip(X, seasons) if s == test_season]
    yte = [v for v, s in zip(y, seasons) if s == test_season]

    # --- оценка: учим на прошлых сезонах, проверяем на последнем ---
    metrics: dict = {"test_season": test_season, "n_train": len(Xtr), "n_test": len(Xte)}
    if Xtr and Xte:
        evaluator = _make_model()
        evaluator.fit(Xtr, ytr)
        proba = evaluator.predict_proba(Xte)[:, 1]
        preds = [int(p >= 0.5) for p in proba]
        # бейзлайны — простое правило "кто сильнее по одному признаку"
        winpct_idx = FEATURE_NAMES.index("d_winpct")
        elo_idx = FEATURE_NAMES.index("d_elo")
        base_winpct = [int(x[winpct_idx] > 0) for x in Xte]
        base_elo = [int(x[elo_idx] > 0) for x in Xte]
        metrics.update(
            accuracy=round(accuracy_score(yte, preds), 4),
            log_loss=round(log_loss(yte, proba), 4),
            auc=round(roc_auc_score(yte, proba), 4),
            baseline_winpct=round(accuracy_score(yte, base_winpct), 4),
            baseline_elo=round(accuracy_score(yte, base_elo), 4),
        )

    # --- финальная модель: на ВСЕХ данных, для прода ---
    model = _make_model()
    model.fit(X, y)
    joblib.dump({"model": model, "features": FEATURE_NAMES}, MODEL_PATH)
    metrics["model_path"] = str(MODEL_PATH)
    metrics["n_total"] = len(X)
    return metrics
