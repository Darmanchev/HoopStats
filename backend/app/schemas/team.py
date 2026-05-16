from pydantic import field_validator
from .base import CamelModel


class TeamSchema(CamelModel):
    abbr: str
    name: str
    city: str
    color: str
    accent: str
    record: str

    @field_validator("abbr")
    @classmethod
    def validate_abbr(cls, v: str) -> str:
        if not v or len(v) > 5:
            raise ValueError("Team abbreviation must be 1-5 characters")
        return v.upper()

    @field_validator("color", "accent")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        if not v.startswith("#") or len(v) not in (4, 7):
            raise ValueError("Color must be a valid hex code (e.g. #FFF or #FFFFFF)")
        return v

    @field_validator("record")
    @classmethod
    def validate_record(cls, v: str) -> str:
        parts = v.split("-")
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            raise ValueError("Record must be in 'W-L' format (e.g. '52-28')")
        return v
