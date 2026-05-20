from sqlalchemy import String, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nba_id: Mapped[int] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(String(100))
    team_abbr: Mapped[str] = mapped_column(String(5), ForeignKey("teams.abbr"))
    position: Mapped[str] = mapped_column(String(5))
    jersey_number: Mapped[str] = mapped_column(String(5), nullable=True)
    games_played: Mapped[int] = mapped_column(Integer, default=0)
    pts: Mapped[float] = mapped_column(Float, default=0.0)
    reb: Mapped[float] = mapped_column(Float, default=0.0)
    ast: Mapped[float] = mapped_column(Float, default=0.0)
    stl: Mapped[float] = mapped_column(Float, default=0.0)
    blk: Mapped[float] = mapped_column(Float, default=0.0)
    fg_pct: Mapped[float] = mapped_column(Float, default=0.0)
    fg3_pct: Mapped[float] = mapped_column(Float, default=0.0)
    ft_pct: Mapped[float] = mapped_column(Float, default=0.0)
    mins: Mapped[float] = mapped_column(Float, default=0.0)
    recent_games: Mapped[int] = mapped_column(Integer, default=0)

    # relationships
    team = relationship("Team", back_populates="players")