from typing import Optional 
from datetime import date
from pydantic import field_validator
from .base import CamelModel
from .team import TeamSchema

class GameBase(CamelModel):
    id: str
    team1: str
    team2: str
    date: date
    time: str
    venue: str
    season_type: str = "regular"

    @field_validator("team1", "team2")
    @classmethod
    def validate_team_abbr(cls, v: str) -> str:
        if not v or len(v) > 5:
            raise ValueError("Team abbreviation must be 1-5 characters")
        return v.upper()

    @field_validator("venue")
    @classmethod
    def validate_venue(cls, v: str) -> str:
        if len(v) > 100:
            raise ValueError("Venue name must be under 100 characters")
        return v

    @field_validator("season_type")
    @classmethod
    def validate_season_type(cls, v: str) -> str:
        if v not in ("regular", "playoffs"):
            raise ValueError("Season type must be 'regular' or 'playoffs'")
        return v


class UpcomingGameSchema(GameBase):
    is_today: bool
    win1: float | None = None
    prediction: str | None = None
    # НОВЫЕ ПОЛЯ
    home_team: Optional[TeamSchema] = None
    away_team: Optional[TeamSchema] = None
    @field_validator("win1")
    @classmethod
    def validate_win_probability(cls, v: float | None) -> float | None:
        if v is not None and not (0 <= v <= 100):
            raise ValueError("Win probability must be between 0 and 100")
        return v
    @field_validator("prediction")
    @classmethod
    def validate_prediction(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 1000:
            raise ValueError("Prediction must be under 1000 characters")
        return v

class PastGameSchema(GameBase):
    score1: int
    score2: int

    @field_validator("score1", "score2")
    @classmethod
    def validate_score(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Score cannot be negative")
        return v
