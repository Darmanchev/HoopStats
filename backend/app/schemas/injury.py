from pydantic import BaseModel
from typing import Literal

class InjurySchema(BaseModel):
    id: str
    team_abbr: str
    player_name: str
    position: str
    injury: str
    status: Literal["Out", "Doubtful", "Questionable", "Day-to-Day"]

    class Config:
        from_attribute = True