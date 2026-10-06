import pytest
from pydantic import ValidationError

from app.config import Settings


def test_provider_interval_cannot_exceed_free_tier_rate() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            secret_key="test-secret",
            database_url="postgresql+asyncpg://test:test@localhost/test",
            balldontlie_request_interval_seconds=11.99,
        )


def test_deprecated_nba_api_key_setting_is_removed() -> None:
    assert "nba_api_key" not in Settings.model_fields
