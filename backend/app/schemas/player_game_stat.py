from .base import CamelModel


class PlayerGameStatSchema(CamelModel):
    nba_id: int
    name: str
    team_abbr: str
    points: int
    rebounds: int
    assists: int
    steals: int
    blocks: int
    minutes: float
