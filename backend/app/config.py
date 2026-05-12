from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    database_url: str
    nba_api_key: str
    secret_key: str
    redis_url: str

    class Config:
        env_file = str(BASE_DIR / ".env")

settings = Settings()