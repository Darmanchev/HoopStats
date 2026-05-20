from sqlalchemy import String, Integer, ARRAY, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base
from typing import List

class TeamStats(Base):
    __tablename__ = "team_stats"

    team_abbr: Mapped[str] = mapped_column(String(5), ForeignKey("teams.abbr"), primary_key=True)
    form: Mapped[List[str]] = mapped_column(ARRAY(String))
    last_scores: Mapped[List[int]] = mapped_column(ARRAY(Integer))

# relationship
    team = relationship("Team", back_populates="stats")