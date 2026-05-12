from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base

class Team(Base):
    __tablename__ = "teams"

    abbr: Mapped[str] = mapped_column(String(5), primary_key=True)
    nba_id: Mapped[int] = mapped_column(Integer, nullable=True)  # ← новое
    name: Mapped[str] = mapped_column(String(50))
    city: Mapped[str] = mapped_column(String(50))
    color: Mapped[str] = mapped_column(String(10))
    accent: Mapped[str] = mapped_column(String(10))
    record: Mapped[str] = mapped_column(String(10))