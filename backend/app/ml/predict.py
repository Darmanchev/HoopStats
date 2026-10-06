"""Прогноз исхода матча обученной моделью."""
from pathlib import Path
import os

import joblib

from .features import LeagueState, parse_date, FEATURE_NAMES, FEATURE_VERSION

MODEL_PATH = Path(os.environ.get("HOOPSTATS_MODEL_DIR", str(Path(__file__).parent))) / "model.joblib"

_bundle = None
_bundle_stamp = None


class ModelUnavailableError(FileNotFoundError):
    """Missing or incompatible model; operational callers should retrain."""


def load_model() -> dict:
    global _bundle, _bundle_stamp
    try:
        stat = MODEL_PATH.stat()
    except FileNotFoundError as exc:
        raise ModelUnavailableError("Model unavailable; retrain with make train") from exc
    stamp = (str(MODEL_PATH), stat.st_mtime_ns, stat.st_size, stat.st_ino)
    if _bundle is None or _bundle_stamp != stamp:
        try:
            candidate = joblib.load(MODEL_PATH)
        except Exception as exc:
            raise ModelUnavailableError("Model unreadable; retrain with make train") from exc
        if (not isinstance(candidate, dict) or candidate.get("features") != FEATURE_NAMES
                or candidate.get("feature_version") != FEATURE_VERSION
                or not callable(getattr(candidate.get("model"), "predict_proba", None))):
            raise ModelUnavailableError("Model feature format changed; retrain with make train")
        _bundle, _bundle_stamp = candidate, stamp
    return _bundle


def _explain(team1: str, team2: str, win1: float, state: LeagueState, home_team: str | None = None, game_date=None) -> str:
    """Короткий текст-объяснение прогноза (на английском — язык интерфейса).

    win1 — шанс победы team1 в процентах (0..100, один знак после запятой).
    Перечисляет только те факторы, что реально за фаворита.
    """
    if win1 >= 50:
        fav, dog, pct = team1, team2, win1
    else:
        fav, dog, pct = team2, team1, round(100 - win1, 1)
    ff = state.hist[fav].metrics()
    df = state.hist[dog].metrics()
    fav_elo, dog_elo = state.elo[fav], state.elo[dog]

    if pct == 50:
        parts = ["An even matchup — too close to call."]
    else:
        tier = "a strong" if pct >= 65 else "a slight" if pct < 56 else "a moderate"
        parts = [f"{fav} are {tier} favorite at {pct}%."]

    factors: list[str] = []
    if home_team == fav:
        factors.append("home court")
    if game_date is not None:
        dates = state.hist[fav].last_date, state.hist[dog].last_date
        if all(d is not None and d < game_date for d in dates):
            rest = [min(7, (game_date - d).days) for d in dates]
            if rest[0] > rest[1]:
                factors.append(f"more rest ({rest[0]} vs {rest[1]} days)")
    if fav_elo - dog_elo >= 25:
        factors.append(f"higher Elo ({round(fav_elo)} vs {round(dog_elo)})")
    if ff["winpct"] - df["winpct"] >= 0.05:
        factors.append(
            f"better record ({round(ff['winpct'] * 100)}% vs {round(df['winpct'] * 100)}%)"
        )
    fn, dn = min(10, len(state.hist[fav].results)), min(10, len(state.hist[dog].results))
    fw, dw = round(ff["form"] * fn), round(df["form"] * dn)
    if fn and dn and ff["form"] - df["form"] >= .2:
        window = f"last {fn}" if fn == dn else f"last {fn}/{dn} games"
        factors.append(f"hotter form ({fw}-{fn - fw} vs {dw}-{dn - dw} {window})")
    fnet, dnet = ff["off"] - ff["def"], df["off"] - df["def"]
    if fnet - dnet >= 2:
        factors.append(f"scoring-margin edge ({fnet:+.1f} vs {dnet:+.1f})")

    if factors:
        parts.append("Key factors: " + ", ".join(factors) + ".")
    elif pct != 50:
        parts.append("The edge is marginal.")
    return " ".join(parts)


def predict_game(state: LeagueState, team1: str, team2: str,
                 game_date: str, home_team: str | None = None) -> tuple[float, str]:
    """Возвращает (win1, prediction_text) для матча team1 vs team2.

    win1 — вероятность победы team1 в процентах, один знак после запятой.
    """
    bundle = load_model()
    model = bundle["model"]
    feats = state.feature_vector(team1, team2, parse_date(game_date), home_team)
    prob1 = float(model.predict_proba([feats])[0][1])
    win1 = round(prob1 * 100, 1)  # процент с одним знаком после запятой
    return win1, _explain(team1, team2, win1, state, home_team, parse_date(game_date))
