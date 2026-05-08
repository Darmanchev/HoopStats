from sqlalchemy import String, Integer, Float, Boolean, Date
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base
import datetime

class Game(Base):
    __tablename__ = "games"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    team1: Mapped[str] = mapped_column(String(5))
    team2: Mapped[str] = mapped_column(String(5))
    date: Mapped[datetime.date] = mapped_column(Date)
    time: Mapped[str] = mapped_column(String(20))
    venue: Mapped[str] = mapped_column(String(100))
    is_today: Mapped[bool] = mapped_column(Boolean, default=False)
    win1: Mapped[float] = mapped_column(Float, nullable=True)
    score1: Mapped[int] = mapped_column(Integer, nullable=True)
    score2: Mapped[int] = mapped_column(Integer, nullable=True)
    prediction: Mapped[str] = mapped_column(String(1000), nullable=True)