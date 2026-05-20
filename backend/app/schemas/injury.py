from typing import Literal
from pydantic import field_validator
from .base import CamelModel


class InjurySchema(CamelModel):
    id: int
    team_abbr: str
    player_name: str
    position: str
    injury: str
    status: Literal["Out", "Doubtful", "Questionable", "Day-to-Day"]
    team_name: str | None = None

    @field_validator("team_abbr")
    @classmethod
    def validate_team_abbr(cls, v: str) -> str:
        if not v or len(v) > 5:
            raise ValueError("Team abbreviation must be 1-5 characters")
        return v.upper()

    @field_validator("player_name")
    @classmethod
    def validate_player_name(cls, v: str) -> str:
        if not v or len(v) > 100:
            raise ValueError("Player name must be 1-100 characters")
        return v.strip()

    @field_validator("position")
    @classmethod
    def validate_position(cls, v: str) -> str:
        if not v or len(v) > 15:
            raise ValueError("Position must be 1-15 characters")
        return v

    @field_validator("injury")
    @classmethod
    def validate_injury(cls, v: str) -> str:
        if len(v) > 100:
            raise ValueError("Injury description must be under 100 characters")
        return v
