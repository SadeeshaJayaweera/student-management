"""
NSBM EduSphere — Application Configuration
Pydantic Settings with environment variable support
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyUrl


class Settings(BaseSettings):
    # Application
    app_name: str = "NSBM EduSphere"
    app_version: str = "1.0.0"
    debug: bool = True
    secret_key: str = "change-this-super-secret-key-in-production-min-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    # Database
    database_url: str = "sqlite+aiosqlite:///./edusphere.db"

    # AI / Gemini
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    ai_enabled: bool = True

    # Vector Database
    chroma_persist_dir: str = "./chroma_db"

    # Redis
    redis_enabled: bool = False
    redis_url: str = "redis://localhost:6379/0"

    # File Uploads
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 50

    # CORS
    allowed_origins: List[str] = [
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
    ]

    # Email
    mail_enabled: bool = False
    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = "noreply@nsbm.ac.lk"
    mail_server: str = "smtp.gmail.com"
    mail_port: int = 587

    # Institution
    institution_name: str = "NSBM Green University"
    institution_short: str = "NSBM"
    institution_website: str = "https://www.nsbm.ac.lk"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
