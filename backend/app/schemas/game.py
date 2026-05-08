from pydantic import BaseModel
from datetime import date

class GameBase(BaseModel):
    id: str
    team1: str
    team2: str
    date: date
    time: str
    venue: str

class UpcomingGameSchema(GameBase):
    is_today: bool
    win1: float
    prediction: str | None

    class Config:
        from_attributes = True

class PastGameSchema(GameBase):
    score1: int
    score2: int

    class Config:
        from_attributes = True