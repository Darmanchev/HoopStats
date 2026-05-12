import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import asyncio
import sys
from pathlib import Path

sys.path.append('../backend')

from app.database import SessionLocal
from app.models.team import Team
from app.models.game import Game
from app.models.team_stats import TeamStats
from sqlalchemy import select

async def load_data():
    async with SessionLocal() as db:
        # берём все завершённые игры
        games_result = await db.execute(
            select(Game).where(Game.score1 != None)
        )
        games = games_result.scalars().all()

        # команды
        teams_result = await db.execute(select(Team))
        teams = {t.abbr: t for t in teams_result.scalars().all()}

        # статистика
        stats_result = await db.execute(select(TeamStats))
        stats = {s.team_abbr: s for s in stats_result.scalars().all()}

        return games, teams, stats

def parse_record(record: str) -> float:
    """52-28 → 0.65"""
    try:
        w, l = record.split("-")
        total = int(w) + int(l)
        return int(w) / total if total > 0 else 0.5
    except:
        return 0.5

def form_to_score(form: list) -> float:
    """['W','L','W','W','L'] → 0.6"""
    if not form:
        return 0.5
    return sum(1 for r in form if r == 'W') / len(form)

def avg_score(scores: list) -> float:
    if not scores:
        return 100.0
    return sum(scores) / len(scores)

def build_features(game, teams, stats):
    t1 = teams.get(game.team1)
    t2 = teams.get(game.team2)
    s1 = stats.get(game.team1)
    s2 = stats.get(game.team2)

    if not t1 or not t2:
        return None

    return [
        parse_record(t1.record),                          # win% team1
        parse_record(t2.record),                          # win% team2
        form_to_score(s1.form if s1 else []),             # форма team1
        form_to_score(s2.form if s2 else []),             # форма team2
        avg_score(s1.last_scores if s1 else []),          # avg pts team1
        avg_score(s2.last_scores if s2 else []),          # avg pts team2
    ]

async def main():
    games, teams, stats = await load_data()

    X, y = [], []
    for game in games:
        features = build_features(game, teams, stats)
        if features is None:
            continue
        label = 1 if game.score1 > game.score2 else 0  # 1 = team1 победила
        X.append(features)
        y.append(label)

    if len(X) < 10:
        print(f"Мало данных для обучения: {len(X)} игр")
        return

    X = np.array(X)
    y = np.array(y)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    acc = accuracy_score(y_test, model.predict(X_test))
    print(f"Точность модели: {acc:.2%}")
    
    MODEL_PATH = Path(__file__).parent / "model.pkl"
    joblib.dump(model, MODEL_PATH)
    print(f"Модель сохранена в {MODEL_PATH}")

asyncio.run(main())