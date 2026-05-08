from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base

class Team(Base):
    __tablename__ = "teams"

    abbr: Mapped[str] = mapped_column(String(5), primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    city: Mapped[str] = mapped_column(String(50))
    color: Mapped[str] = mapped_column(String(10))
    accent: Mapped[str] = mapped_column(String(10))
    record: Mapped[str] = mapped_column(String(10))