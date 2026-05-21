"""Признаки для модели прогнозирования исходов матчей.

Без обращения к БД — работаем со списком игр (dict-ами):
    {"id", "team1", "team2", "date", "score1", "score2", "season"}

Главный принцип — нет утечки будущего: признаки игры считаются по
состоянию лиги СТРОГО до её даты.
"""
from collections import defaultdict, deque
from datetime import date

# порядок признаков фиксирован — модель обучается и предсказывает по нему
FEATURE_NAMES = ["d_form", "d_winpct", "d_net", "d_elo"]

FORM_WINDOW = 10        # окно "формы" (последние N игр)
WINPCT_WINDOW = 30      # окно для общего % побед
MIN_HISTORY = 8         # минимум прошлых игр у каждой команды для обучающей строки

# --- Elo ---
ELO_BASE = 1500.0       # стартовый рейтинг
ELO_K = 20.0            # скорость изменения рейтинга
ELO_REGRESS = 0.75      # к началу сезона рейтинги тянутся к среднему


def parse_date(d: str) -> date:
    """'2025-10-21' / '2025-10-21T..' → date."""
    return date.fromisoformat(d[:10])


class TeamHistory:
    """Скользящая история результатов одной команды."""

    def __init__(self) -> None:
        self.results: deque[bool] = deque(maxlen=WINPCT_WINDOW)
        self.scores: deque[tuple[int, int]] = deque(maxlen=FORM_WINDOW)
        self.last_date: date | None = None
        self.count = 0

    def metrics(self) -> dict:
        n = len(self.results)
        winpct = sum(self.results) / n if n else 0.5
        last10 = list(self.results)[-FORM_WINDOW:]
        form = sum(last10) / len(last10) if last10 else 0.5
        if self.scores:
            off = sum(s[0] for s in self.scores) / len(self.scores)
            deff = sum(s[1] for s in self.scores) / len(self.scores)
        else:
            off = deff = 112.0
        return {"winpct": winpct, "form": form, "off": off, "def": deff}

    def record(self, won: bool, pts_for: int, pts_against: int, game_date: date) -> None:
        self.results.append(won)
        self.scores.append((pts_for, pts_against))
        self.last_date = game_date
        self.count += 1


def _elo_expected(elo_a: float, elo_b: float) -> float:
    """Ожидаемая доля очков команды A (вероятность победы)."""
    return 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / 400.0))


def _elo_delta(winner_elo: float, loser_elo: float, margin: int) -> float:
    """Прирост рейтинга победителя (= убыли проигравшего).

    Учитывает разницу в счёте (margin-of-victory) и поправку на
    автокорреляцию — формула в духе FiveThirtyEight.
    """
    expected = _elo_expected(winner_elo, loser_elo)
    elo_diff = winner_elo - loser_elo  # с точки зрения победителя
    mov = ((margin + 3) ** 0.8) / (7.5 + 0.006 * elo_diff)
    return ELO_K * mov * (1.0 - expected)


def _diff_vector(h1: TeamHistory, h2: TeamHistory,
                 elo1: float, elo2: float, game_date: date) -> list[float]:
    """Вектор признаков как разница метрик team1 − team2 (порядок = FEATURE_NAMES)."""
    m1, m2 = h1.metrics(), h2.metrics()
    net1, net2 = m1["off"] - m1["def"], m2["off"] - m2["def"]
    return [
        m1["form"] - m2["form"],
        m1["winpct"] - m2["winpct"],
        net1 - net2,
        elo1 - elo2,
    ]


class LeagueState:
    """Состояние лиги: история и Elo-рейтинг всех команд.

    Обновляется игра за игрой в хронологическом порядке.
    """

    def __init__(self) -> None:
        self.hist: dict[str, TeamHistory] = defaultdict(TeamHistory)
        self.elo: dict[str, float] = defaultdict(lambda: ELO_BASE)
        self._season: str | None = None

    def feature_vector(self, team1: str, team2: str, game_date: date) -> list[float]:
        """Признаки матча по ТЕКУЩЕМУ состоянию (до игры)."""
        return _diff_vector(
            self.hist[team1], self.hist[team2],
            self.elo[team1], self.elo[team2], game_date,
        )

    def record(self, g: dict) -> None:
        """Вносит результат сыгранной игры в историю и Elo."""
        season = g.get("season")
        if self._season is not None and season != self._season:
            self._regress_season()
        self._season = season

        t1, t2 = g["team1"], g["team2"]
        s1, s2 = g["score1"], g["score2"]
        gd = parse_date(g["date"])
        won1 = s1 > s2
        margin = abs(s1 - s2)

        e1, e2 = self.elo[t1], self.elo[t2]
        if won1:
            d = _elo_delta(e1, e2, margin)
            self.elo[t1], self.elo[t2] = e1 + d, e2 - d
        else:
            d = _elo_delta(e2, e1, margin)
            self.elo[t2], self.elo[t1] = e2 + d, e1 - d

        self.hist[t1].record(won1, s1, s2, gd)
        self.hist[t2].record(not won1, s2, s1, gd)

    def _regress_season(self) -> None:
        """Межсезонная регрессия рейтингов к среднему."""
        for team in list(self.elo):
            self.elo[team] = ELO_REGRESS * self.elo[team] + (1 - ELO_REGRESS) * ELO_BASE


def build_training_rows(games: list[dict]):
    """Хронологический проход: признаки игры считаем ДО внесения её
    результата в состояние. Возвращает (X, y, seasons)."""
    games_sorted = sorted(games, key=lambda g: g["date"])
    state = LeagueState()
    X: list[list[float]] = []
    y: list[int] = []
    seasons: list[str] = []

    for g in games_sorted:
        s1, s2 = g["score1"], g["score2"]
        if s1 is None or s2 is None:
            continue
        t1, t2 = g["team1"], g["team2"]
        if state.hist[t1].count >= MIN_HISTORY and state.hist[t2].count >= MIN_HISTORY:
            X.append(state.feature_vector(t1, t2, parse_date(g["date"])))
            y.append(1 if s1 > s2 else 0)
            seasons.append(g.get("season", "?"))
        state.record(g)

    return X, y, seasons


def build_state(games: list[dict]) -> LeagueState:
    """Финальное состояние лиги по всем сыгранным играм."""
    state = LeagueState()
    for g in sorted(games, key=lambda g: g["date"]):
        if g["score1"] is None or g["score2"] is None:
            continue
        state.record(g)
    return state
