from pydantic import BaseModel

class TeamStatsSchema(BaseModel):
    team_abbr: str
    form: list[str]
    last_scores: list[int]

    class Config:
        from_attributes = True