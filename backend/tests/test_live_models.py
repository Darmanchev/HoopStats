from sqlalchemy import UniqueConstraint

from app.models.game import Game
from app.models.player_game_stat import PlayerGameStat
from app.models.team import Team


def test_game_exposes_live_state_columns() -> None:
    assert {"status", "status_text", "period", "clock"} <= set(
        Game.__table__.columns.keys()
    )


def test_team_exposes_standing_columns() -> None:
    assert {"conference", "conference_rank", "last_ten", "streak"} <= set(
        Team.__table__.columns.keys()
    )


def test_player_game_stat_is_unique_per_game_and_player() -> None:
    constraints = [
        constraint
        for constraint in PlayerGameStat.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    ]
    assert any(
        {column.name for column in constraint.columns} == {"game_id", "nba_id"}
        for constraint in constraints
    )
