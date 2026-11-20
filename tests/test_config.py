"""
NSBM EduSphere — Configuration & Environment Validation Tests
Tests multi-environment settings, security validations, and redaction
"""
import pytest
from pydantic import ValidationError
from backend.core.config import Settings, AppEnvironment


def test_default_development_settings():
    """Verify default development configuration loads with sensible defaults"""
    settings = Settings()
    assert settings.environment == AppEnvironment.DEVELOPMENT
    assert settings.is_development is True
    assert settings.is_production is False
    assert settings.access_token_expire_minutes == 60
    assert len(settings.allowed_origins) >= 2


def test_production_environment_rejects_weak_secret():
    """Verify production environment throws ValidationError on weak or default secret key"""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            environment=AppEnvironment.PRODUCTION,
            secret_key="insecure-dev-key",
            allowed_origins=["https://lms.nsbm.ac.lk"],
        )
    assert "SECRET_KEY" in str(exc_info.value)


def test_production_environment_rejects_wildcard_cors():
    """Verify production environment throws ValidationError if CORS contains wildcard '*'"""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            environment=AppEnvironment.PRODUCTION,
            secret_key="prod-crypto-random-token-secure-32chars-xyz987",
            allowed_origins=["*"],
        )
    assert "wildcard" in str(exc_info.value)


def test_valid_production_settings():
    """Verify valid production settings succeed validation"""
    valid_prod = Settings(
        environment=AppEnvironment.PRODUCTION,
        secret_key="prod-crypto-random-token-secure-32chars-xyz987",
        allowed_origins=["https://lms.nsbm.ac.lk"],
    )
    assert valid_prod.is_production is True
    assert valid_prod.secret_key == "prod-crypto-random-token-secure-32chars-xyz987"


def test_masked_dict_redacts_secrets():
    """Verify sensitive keys are redacted in diagnostic exports"""
    settings = Settings(
        secret_key="sample-secret-key-at-least-32-chars-long",
        google_api_key="AIzaSySampleKey12345",
    )
    masked = settings.get_masked_dict()
    assert "sample-secret" not in masked["secret_key"]
    assert "***REDACTED" in masked["secret_key"]
    assert "***REDACTED" in masked["google_api_key"]
