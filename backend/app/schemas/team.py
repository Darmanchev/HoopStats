from pydantic import field_validator
from .base import CamelModel
from typing import Optional
from .team_stats import TeamStatsSchema

class TeamSchema(CamelModel):
    abbr: str
    name: str
    city: str
    record: str

    @field_validator("abbr")
    @classmethod
    def validate_abbr(cls, v: str) -> str:
        if not v or len(v) > 5:
            raise ValueError("Team abbreviation must be 1-5 characters")
        return v.upper()

    @field_validator("record")
    @classmethod
    def validate_record(cls, v: str) -> str:
        parts = v.split("-")
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            raise ValueError("Record must be in 'W-L' format (e.g. '52-28')")
        return v

class TeamDetailSchema(TeamSchema):
    stats: Optional[TeamStatsSchema] = None
    players_count: int = 0