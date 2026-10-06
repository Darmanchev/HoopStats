"""Probability metrics and calibration for a chronological holdout."""
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import os
import tempfile

from sklearn.metrics import accuracy_score, log_loss, roc_auc_score, brier_score_loss
from .features import FEATURE_NAMES, FEATURE_VERSION

REPORT_VERSION = 1


def atomic_write(path: Path, writer) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    os.close(fd)
    try:
        writer(temporary)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def metrics(y, probabilities):
    return {
        "accuracy": round(float(accuracy_score(y, [int(p >= .5) for p in probabilities])), 4),
        "log_loss": round(float(log_loss(y, probabilities, labels=[0, 1])), 4),
        "brier": round(float(brier_score_loss(y, probabilities)), 4),
        "auc": round(float(roc_auc_score(y, probabilities)), 4) if len(set(y)) == 2 else None,
    }


def build_report(model, x, y, metadata, n_train, test_season):
    probabilities = [float(p) for p in model.predict_proba(x)[:, 1]]
    elo_index = FEATURE_NAMES.index("d_elo")
    elo = [1 / (1 + 10 ** (-row[elo_index] / 400)) for row in x]
    # A fixed, unfitted home preference baseline; uncertain venues remain even.
    home_index = FEATURE_NAMES.index("home")
    home = [.6 if row[home_index] > 0 else .4 if row[home_index] < 0 else .5 for row in x]
    bins = []
    for i in range(10):
        indices = [j for j, p in enumerate(probabilities) if min(9, int(p * 10)) == i]
        bins.append({"lower": i / 10, "upper": (i + 1) / 10, "count": len(indices),
            "predicted": sum(probabilities[j] for j in indices) / len(indices) if indices else None,
            "observed": sum(y[j] for j in indices) / len(indices) if indices else None})
    return {"report_version": REPORT_VERSION, "feature_version": FEATURE_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(), "available": True,
        "test_season": test_season, "n_train": n_train, "n_test": len(y),
        "metrics": metrics(y, probabilities), "baselines": {"elo": metrics(y, elo), "home": metrics(y, home)},
        "calibration": bins,
        "games": [{**g, "probability": p, "actual": actual, "correct": int(p >= .5) == actual}
            for g, p, actual in zip(metadata, probabilities, y)]}


def unavailable_report(test_season, n_train, n_test):
    return {"report_version": REPORT_VERSION, "feature_version": FEATURE_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(), "available": False,
        "reason": "At least two eligible seasons and two training outcome classes are required for held-out evaluation.",
        "test_season": test_season, "n_train": n_train, "n_test": n_test,
        "metrics": None, "baselines": {}, "calibration": [], "games": []}


def read_report(path: Path) -> dict | None:
    """Reject every malformed field consumed by the evaluation interface."""
    def number(value, low=None, high=None):
        return (type(value) in (int, float) and math.isfinite(value)
                and (low is None or value >= low) and (high is None or value <= high))
    def metric_set(values):
        return (isinstance(values, dict) and number(values.get("accuracy"), 0, 1)
                and number(values.get("log_loss"), 0) and number(values.get("brier"), 0, 1)
                and (values.get("auc") is None or number(values["auc"], 0, 1)))
    try:
        report = json.loads(path.read_text())
        if (not isinstance(report, dict) or report.get("report_version") != REPORT_VERSION
                or report.get("feature_version") != FEATURE_VERSION
                or type(report.get("available")) is not bool):
            return None
        if not report["available"]:
            return report if isinstance(report.get("reason"), str) and report.get("games") == [] else None
        if (not isinstance(report.get("test_season"), str)
                or not isinstance(report.get("trained_at"), str)
                or type(report.get("n_train")) is not int or report["n_train"] < 1
                or type(report.get("n_test")) is not int or report["n_test"] < 1
                or not isinstance(report.get("games"), list)
                or report["n_test"] != len(report["games"])
                or not metric_set(report.get("metrics"))
                or not isinstance(report.get("baselines"), dict)
                or set(report["baselines"]) != {"elo", "home"}
                or not all(metric_set(values) for values in report["baselines"].values())
                or not isinstance(report.get("calibration"), list) or len(report["calibration"]) != 10):
            return None
        datetime.fromisoformat(report["trained_at"])
        count = 0
        for i, bin in enumerate(report["calibration"]):
            if (not isinstance(bin, dict) or bin.get("lower") != i / 10
                    or bin.get("upper") != (i + 1) / 10
                    or type(bin.get("count")) is not int or bin["count"] < 0):
                return None
            count += bin["count"]
            for key in ("predicted", "observed"):
                if bin["count"] and not number(bin.get(key), 0, 1):
                    return None
                if not bin["count"] and bin.get(key) is not None:
                    return None
        if count != report["n_test"]:
            return None
        for game in report["games"]:
            if (not isinstance(game, dict)
                    or not all(isinstance(game.get(k), str) and game[k] for k in ("id", "date", "team1", "team2"))
                    or not number(game.get("probability"), 0, 1)
                    or type(game.get("actual")) is not int or game["actual"] not in (0, 1)
                    or type(game.get("correct")) is not bool):
                return None
        return report
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return None
