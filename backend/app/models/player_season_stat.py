from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class PlayerSeasonStat(Base):
    __tablename__ = "player_season_stats"
    __table_args__ = (
        UniqueConstraint(
            "player_id",
            "season",
            name="uq_player_season_stats_player_season",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        index=True,
    )
    season: Mapped[str] = mapped_column(String(7), index=True)
    primary_team_abbr: Mapped[str] = mapped_column(
        ForeignKey("teams.abbr"),
        index=True,
    )
    games_played: Mapped[int] = mapped_column(Integer)
    pts: Mapped[float] = mapped_column(Float)
    reb: Mapped[float] = mapped_column(Float)
    ast: Mapped[float] = mapped_column(Float)
    stl: Mapped[float] = mapped_column(Float)
    blk: Mapped[float] = mapped_column(Float)
    fg_pct: Mapped[float] = mapped_column(Float)
    fg3_pct: Mapped[float] = mapped_column(Float)
    ft_pct: Mapped[float] = mapped_column(Float)
    mins: Mapped[float] = mapped_column(Float)
    recent_games: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    player = relationship("Player", back_populates="season_stats")
