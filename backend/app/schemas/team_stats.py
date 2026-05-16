from pydantic import field_validator
from .base import CamelModel


class TeamStatsSchema(CamelModel):
    team_abbr: str
    form: list[str]
    last_scores: list[int]

    @field_validator("team_abbr")
    @classmethod
    def validate_team_abbr(cls, v: str) -> str:
        if not v or len(v) > 5:
            raise ValueError("Team abbreviation must be 1-5 characters")
        return v.upper()

    @field_validator("form")
    @classmethod
    def validate_form(cls, v: list[str]) -> list[str]:
        valid_results = {"W", "L"}
        for result in v:
            if result not in valid_results:
                raise ValueError(f"Form result must be 'W' or 'L', got '{result}'")
        return v

    @field_validator("last_scores")
    @classmethod
    def validate_scores(cls, v: list[int]) -> list[int]:
        for score in v:
            if score < 0:
                raise ValueError("Score cannot be negative")
        return v
