from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base

class Injury(Base):
    __tablename__ = "injuries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_abbr: Mapped[str] = mapped_column(String(5))
    player_name: Mapped[str] = mapped_column(String(100))
    position: Mapped[str] = mapped_column(String(15))
    injury: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20))