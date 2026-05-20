from sqlalchemy import String, Integer, Float, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

class Game(Base):
    __tablename__ = "games"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    team1: Mapped[str | None] = mapped_column(String(5), ForeignKey("teams.abbr", ondelete="SET NULL"), nullable=True)
    team2: Mapped[str | None] = mapped_column(String(5), ForeignKey("teams.abbr", ondelete="SET NULL"), nullable=True)
    date: Mapped[str] = mapped_column(String(10))
    time: Mapped[str] = mapped_column(String(50))
    venue: Mapped[str] = mapped_column(String(100))
    is_today: Mapped[bool] = mapped_column(Boolean, default=False)
    season_type: Mapped[str] = mapped_column(String(20), default="regular")  # "regular" or "playoffs"
    season: Mapped[str] = mapped_column(String(7), server_default="2025-26", index=True)  # "2025-26"
    win1: Mapped[float] = mapped_column(Float, nullable=True)
    score1: Mapped[int] = mapped_column(Integer, nullable=True)
    score2: Mapped[int] = mapped_column(Integer, nullable=True)
    prediction: Mapped[str] = mapped_column(String(1000), nullable=True)

# relationship
    home_team = relationship("Team", back_populates="home_games", foreign_keys=[team1])
    away_team = relationship("Team", back_populates="away_games", foreign_keys=[team2])