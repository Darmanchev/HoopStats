from pydantic import field_validator
from .base import CamelModel


class PlayerSchema(CamelModel):
    id: int
    nba_id: int
    name: str
    team_abbr: str
    position: str
    jersey_number: str | None = None
    games_played: int
    pts: float
    reb: float
    ast: float
    stl: float
    blk: float
    fg_pct: float
    fg3_pct: float
    ft_pct: float
    mins: float
    recent_games: int

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("team_abbr")
    @classmethod
    def validate_team_abbr(cls, v: str) -> str:
        if not v or len(v) > 5:
            raise ValueError("Team abbreviation must be 1-5 characters")
        return v.upper()


class PlayerDetailSchema(CamelModel):
    id: int
    nba_id: int
    name: str
    team_abbr: str
    position: str
    jersey_number: str | None = None
    games_played: int
    pts: float
    reb: float
    ast: float
    stl: float
    blk: float
    fg_pct: float
    fg3_pct: float
    ft_pct: float
    mins: float
    recent_games: int
    team_name: str | None = None
    team_city: str | None = None
