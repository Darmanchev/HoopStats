"""Обучение ML-модели прогнозирования матчей.

Загружает сыгранные игры из БД, обучает модель, сохраняет model.joblib.
Запуск:  docker compose exec backend python train_model.py
"""
import asyncio

from sqlalchemy import select

from app.database import SessionLocal
from app.models.game import Game
from app.ml.train import train


async def load_played_games() -> list[dict]:
    async with SessionLocal() as db:
        rows = (await db.execute(select(Game))).scalars().all()
        return [
            {
                "id": g.id,
                "team1": g.team1,
                "team2": g.team2,
                "date": g.date,
                "score1": g.score1,
                "score2": g.score2,
                "season": g.season,
            }
            for g in rows
            if g.score1 is not None and g.score2 is not None
        ]


def main() -> None:
    games = asyncio.run(load_played_games())
    print(f"Загружено {len(games)} сыгранных игр")
    metrics = train(games)
    print("\n=== Результат обучения ===")
    for k, v in metrics.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
