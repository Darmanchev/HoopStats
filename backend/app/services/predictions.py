"""ML-прогнозы для предстоящих матчей.

Выделен из nba_service.py — зависит от ML-модуля (app.ml).
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.game import Game
from ..ml.features import build_state
from ..ml.predict import predict_game

logger = logging.getLogger(__name__)


async def sync_predictions(db: AsyncSession) -> None:
    """Считает ML-прогнозы (win1 + текст) для всех предстоящих игр.

    Требует обученную модель (backend/train_model.py). Если её нет —
    функция мягко завершится без изменений.
    """
    rows = (await db.execute(select(Game))).scalars().all()
    played = [
        {
            "id": g.id, "team1": g.team1, "team2": g.team2, "date": g.date,
            "score1": g.score1, "score2": g.score2, "season": g.season,
        }
        for g in rows if g.score1 is not None and g.score2 is not None
    ]
    upcoming = [g for g in rows if g.score1 is None]

    if not upcoming:
        logger.info("Нет предстоящих игр для прогноза")
        return

    state = build_state(played)
    count = 0
    for g in upcoming:
        try:
            win1, text = predict_game(state, g.team1, g.team2, g.date)
            g.win1 = win1
            g.prediction = text
            count += 1
        except FileNotFoundError as e:
            logger.warning("Прогноз пропущен: %s", e)
            return
        except Exception as e:
            logger.error("Прогноз %s: %s: %s", g.id, type(e).__name__, e)

    await db.commit()
    logger.info("Прогнозы обновлены: %d игр", count)
