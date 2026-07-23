from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    database_url: str | None = None
    db_user: str | None = None
    db_password: str | None = None
    db_host: str = "db"
    db_port: int = 5432
    db_name: str = "hoopstats"

    nba_api_key: str = ""
    secret_key: str
    redis_url: str = "redis://redis:6379/0"
    allowed_hosts: str = "localhost,127.0.0.1,testserver"
    api_docs_enabled: bool = False
    elo_cache_ttl_seconds: int = 86_400
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    elo_rate_limit_requests: int = 10

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        extra="ignore",
    )

    def allowed_host_list(self) -> list[str]:
        """Return normalized hosts for Starlette's TrustedHostMiddleware."""
        hosts = [host.strip() for host in self.allowed_hosts.split(",")]
        return [host for host in hosts if host]

    def sqlalchemy_url(self) -> str | URL:
        """Build a URL without requiring URL-escaped passwords in Compose."""
        if self.database_url:
            # SQLAlchemy otherwise selects the synchronous psycopg2 driver for
            # the common postgresql:// form, while this application is async.
            if self.database_url.startswith("postgresql://"):
                return self.database_url.replace(
                    "postgresql://",
                    "postgresql+asyncpg://",
                    1,
                )
            return self.database_url
        if not self.db_user or not self.db_password:
            raise ValueError(
                "Set DATABASE_URL or both DB_USER and DB_PASSWORD"
            )
        return URL.create(
            "postgresql+asyncpg",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


settings = Settings()
