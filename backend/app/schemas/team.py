from pydantic import BaseModel

class TeamSchema(BaseModel):
    abbr: str
    name: str
    city: str
    color: str
    accent: str
    record: str

    class Config:
        from_attributes = True

