"""Прогноз исхода матча обученной моделью."""
from pathlib import Path

import joblib

from .features import LeagueState, parse_date

MODEL_PATH = Path(__file__).parent / "model.joblib"

_bundle = None  # ленивый кэш загруженной модели


def load_model() -> dict:
    """Загружает {"model", "features"}; кэширует. Бросает FileNotFoundError,
    если модель ещё не обучена."""
    global _bundle
    if _bundle is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                "Модель не обучена — запустите backend/train_model.py"
            )
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def _explain(team1: str, team2: str, win1: float, state: LeagueState) -> str:
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
    if fav_elo - dog_elo >= 25:
        factors.append(f"higher Elo ({round(fav_elo)} vs {round(dog_elo)})")
    if ff["winpct"] - df["winpct"] >= 0.05:
        factors.append(
            f"better record ({round(ff['winpct'] * 100)}% vs {round(df['winpct'] * 100)}%)"
        )
    fw, dw = round(ff["form"] * 10), round(df["form"] * 10)
    if fw - dw >= 2:
        factors.append(f"hotter form ({fw}-{10 - fw} vs {dw}-{10 - dw} L10)")
    fnet, dnet = ff["off"] - ff["def"], df["off"] - df["def"]
    if fnet - dnet >= 2:
        factors.append(f"net-rating edge ({fnet:+.1f} vs {dnet:+.1f})")

    if factors:
        parts.append("Key factors: " + ", ".join(factors) + ".")
    elif pct != 50:
        parts.append("The edge is marginal.")
    return " ".join(parts)


def predict_game(state: LeagueState, team1: str, team2: str,
                 game_date: str) -> tuple[float, str]:
    """Возвращает (win1, prediction_text) для матча team1 vs team2.

    win1 — вероятность победы team1 в процентах, один знак после запятой.
    """
    bundle = load_model()
    model = bundle["model"]
    feats = state.feature_vector(team1, team2, parse_date(game_date))
    prob1 = float(model.predict_proba([feats])[0][1])
    win1 = round(prob1 * 100, 1)  # процент с одним знаком после запятой
    return win1, _explain(team1, team2, win1, state)
