from typing import Literal, TypedDict


class StandingData(TypedDict):
    record: str
    conference: Literal["East", "West"]
    conference_rank: int
    last_ten: str
    streak: str


class LiveGameData(TypedDict):
    game_id: str
    away_abbr: str
    home_abbr: str
    date: str
    start_time: str
    status: Literal["scheduled", "live", "final"]
    status_text: str
    period: int | None
    clock: str | None
    away_score: int | None
    home_score: int | None
    venue: str


class LivePlayerStatData(TypedDict):
    game_id: str
    nba_id: int
    name: str
    team_abbr: str
    points: int
    rebounds: int
    assists: int
    steals: int
    blocks: int
    minutes: float
