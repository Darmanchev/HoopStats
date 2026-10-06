"""ML-прогнозы для предстоящих матчей.

Выделен из nba_service.py — зависит от ML-модуля (app.ml).
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.game import Game
from ..ml.features import build_state, verified_home
from ..ml.predict import predict_game

logger = logging.getLogger(__name__)


async def sync_predictions(db: AsyncSession) -> int:
    """Считает ML-прогнозы (win1 + текст) для всех предстоящих игр.

    Requires a trained model. Missing models or incomplete predictions are
    reported to the caller so imports do not claim success.
    """
    rows = (await db.execute(select(Game))).scalars().all()
    played = [
        {
            "id": g.id, "team1": g.team1, "team2": g.team2, "date": g.date,
            "score1": g.score1, "score2": g.score2, "season": g.season,
            "season_type": g.season_type or "regular", "status": g.status,
        }
        for g in rows
        if g.status == "final" and g.score1 is not None and g.score2 is not None
    ]
    upcoming = [g for g in rows if g.status == "scheduled" and (g.season_type or "regular") in {"regular", "playoffs"}]
    for g in rows:
        if g.status == "scheduled" and g.season_type == "preseason":
            g.win1 = None
            g.prediction = None

    if not upcoming:
        await db.commit()
        logger.info("Нет предстоящих игр для прогноза")
        return 0

    states = {}
    count = 0
    failures = 0
    for g in sorted(upcoming, key=lambda game: (game.date, game.id)):
        try:
            key = (g.date, g.season)
            if key not in states:
                states[key] = build_state([past for past in played if past["date"] < g.date])
            state = states[key]
            if hasattr(state, "prepare_season"):
                state.prepare_season(g.season)
            win1, text = predict_game(state, g.team1, g.team2, g.date, verified_home(g))
            g.win1 = win1
            g.prediction = text
            count += 1
        except FileNotFoundError as e:
            for pending in upcoming:
                pending.win1 = None
                pending.prediction = None
            await db.commit()
            logger.warning("Prediction unavailable: %s", e)
            raise
        except Exception as e:
            g.win1 = None
            g.prediction = None
            logger.error("Прогноз %s: %s: %s", g.id, type(e).__name__, e)
            failures += 1

    await db.commit()
    logger.info("Прогнозы обновлены: %d игр", count)
    if failures:
        raise RuntimeError(f"Predictions incomplete: {count} succeeded, {failures} failed")
    return count
