from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

class Team(Base):
    __tablename__ = "teams"

    abbr: Mapped[str] = mapped_column(String(5), primary_key=True)
    nba_id: Mapped[int] = mapped_column(Integer, nullable=True)  # ← новое
    name: Mapped[str] = mapped_column(String(50))
    city: Mapped[str] = mapped_column(String(50))
    record: Mapped[str] = mapped_column(String(10))

# relationships

    players = relationship("Player", back_populates="team")
    stats = relationship("TeamStats", back_populates="team", uselist=False)
    home_games = relationship("Game", back_populates="home_team", foreign_keys="[Game.team1]")
    away_games = relationship("Game", back_populates="away_team", foreign_keys="[Game.team2]")
    injuries = relationship("Injury", back_populates="team")