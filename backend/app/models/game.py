from datetime import datetime

from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, DateTime, JSON
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
    season_type: Mapped[str] = mapped_column(String(20), default="regular")  # preseason, regular or playoffs
    season: Mapped[str] = mapped_column(String(7), index=True)  # Explicit provider season, e.g. "2026-27"
    win1: Mapped[float] = mapped_column(Float, nullable=True)
    score1: Mapped[int] = mapped_column(Integer, nullable=True)
    score2: Mapped[int] = mapped_column(Integer, nullable=True)
    prediction: Mapped[str] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(
        String(12),
        default="scheduled",
        server_default="scheduled",
    )
    status_text: Mapped[str] = mapped_column(
        String(50),
        default="",
        server_default="",
    )
    home_abbr: Mapped[str | None] = mapped_column(String(5), nullable=True)
    period_scores: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    period: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clock: Mapped[str | None] = mapped_column(String(30), nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

# team1 is away; team2 is home in all normalized imports.
    home_team = relationship("Team", back_populates="home_games", foreign_keys=[team2])
    away_team = relationship("Team", back_populates="away_games", foreign_keys=[team1])
