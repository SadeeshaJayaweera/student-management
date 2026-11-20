"""
NSBM EduSphere — Core Configuration & Environment Management
Enterprise Pydantic Settings with multi-environment validation and secure defaults
"""
import enum
from functools import lru_cache
from typing import List, Dict, Any, Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(str, enum.Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    # Application & Environment
    app_name: str = Field(default="NSBM EduSphere", description="Display application name")
    app_version: str = Field(default="1.0.0", description="SemVer application version")
    environment: AppEnvironment = Field(
        default=AppEnvironment.DEVELOPMENT,
        description="Deployment environment (development, testing, staging, production)",
    )
    debug: bool = Field(default=False, description="Enable verbose debug mode")

    # Security & Cryptography
    secret_key: str = Field(
        default="development-insecure-secret-key-min-32-chars-for-dev-only",
        description="Cryptographic secret key for JWT signing",
    )
    algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    access_token_expire_minutes: int = Field(default=60, description="Access token expiry in minutes")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiry in days")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./edusphere.db",
        description="Async SQLAlchemy database connection string",
    )

    # AI & Knowledge Services
    google_api_key: str = Field(default="", description="Google Gemini API key")
    gemini_model: str = Field(default="gemini-2.0-flash", description="Gemini model identifier")
    ai_enabled: bool = Field(default=True, description="Enable AI subsystem")
    chroma_persist_dir: str = Field(default="./chroma_db", description="ChromaDB persistence path")

    # Cache & PubSub
    redis_enabled: bool = Field(default=False, description="Enable Redis cache and state store")
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")

    # Storage & Uploads
    upload_dir: str = Field(default="./uploads", description="Base upload directory")
    max_file_size_mb: int = Field(default=50, description="Maximum permitted upload size in MB")

    # CORS
    allowed_origins: List[str] = Field(
        default=[
            "http://localhost:8000",
            "http://localhost:5173",
            "http://127.0.0.1:8000",
            "http://127.0.0.1:5173",
        ],
        description="Allowed CORS origin domains",
    )

    # Email & SMTP Notifications
    mail_enabled: bool = Field(default=False, description="Enable SMTP notifications")
    mail_username: str = Field(default="", description="SMTP username")
    mail_password: str = Field(default="", description="SMTP password")
    mail_from: str = Field(default="noreply@nsbm.ac.lk", description="Sender email address")
    mail_server: str = Field(default="smtp.gmail.com", description="SMTP server host")
    mail_port: int = Field(default=587, description="SMTP server port")

    # Institution
    institution_name: str = Field(default="NSBM Green University", description="Default institution name")
    institution_short: str = Field(default="NSBM", description="Institutional acronym")
    institution_website: str = Field(default="https://www.nsbm.ac.lk", description="Institutional website")

    # Model Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: Any) -> List[str]:
        if isinstance(value, str):
            import json
            try:
                return json.loads(value)
            except Exception:
                return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_environment_security(self) -> "Settings":
        """Enforce strict cryptographic and CORS requirements in production and staging"""
        if self.environment in (AppEnvironment.PRODUCTION, AppEnvironment.STAGING):
            # Insecure secret check
            insecure_markers = ["dev-only", "change-this", "insecure", "default-secret", "placeholder"]
            if any(marker in self.secret_key.lower() for marker in insecure_markers) or len(self.secret_key) < 32:
                raise ValueError(
                    f"Production environment requires a strong, random SECRET_KEY of at least 32 characters. Found: '{self.secret_key[:6]}...'"
                )
            # Wildcard CORS rejection in production
            if "*" in self.allowed_origins:
                raise ValueError("CORS allowed_origins cannot contain wildcard '*' in production or staging environments.")

        return self

    @property
    def is_production(self) -> bool:
        return self.environment == AppEnvironment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.environment == AppEnvironment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        return self.environment == AppEnvironment.TESTING

    def get_masked_dict(self) -> Dict[str, Any]:
        """Return configuration dictionary with sensitive fields redacted for safe diagnostics"""
        data = self.model_dump()
        sensitive_keys = {"secret_key", "google_api_key", "mail_password"}
        for k in sensitive_keys:
            if k in data and data[k]:
                data[k] = f"***REDACTED({len(data[k])} chars)***"
        return data


@lru_cache()
def get_settings() -> Settings:
    return Settings()
