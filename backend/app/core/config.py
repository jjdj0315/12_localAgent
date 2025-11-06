"""Application configuration"""

import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # App
    APP_NAME: str = "Local LLM Web Application"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "llm_app")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "changeme")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "llm_webapp")

    # Security
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "your-secret-key-change-in-production-please"
    )
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    MAX_CONCURRENT_SESSIONS: int = int(os.getenv("MAX_CONCURRENT_SESSIONS", "3"))  # T316
    BCRYPT_ROUNDS: int = int(os.getenv("BCRYPT_ROUNDS", "12"))

    # Environment-based cookie security (FR-112)
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # development, production

    @property
    def cookie_secure(self) -> bool:
        """Enable secure flag only in production (HTTPS required)"""
        return self.ENVIRONMENT == "production"

    @property
    def cookie_samesite(self) -> str:
        """Use strict SameSite in production, lax in development"""
        return "strict" if self.ENVIRONMENT == "production" else "lax"

    def is_default_secret_key(self) -> bool:
        """Check if using default/weak SECRET_KEY (T315)"""
        weak_keys = [
            "your-secret-key-change-in-production-please",
            "changeme",
            "secret",
            "password",
            "12345",
        ]
        return (
            self.SECRET_KEY in weak_keys
            or len(self.SECRET_KEY) < 32
            or self.SECRET_KEY.lower() == self.SECRET_KEY  # All lowercase
            or self.SECRET_KEY.upper() == self.SECRET_KEY  # All uppercase
        )

    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:80,http://localhost")

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string into list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # LLM Service
    MAX_RESPONSE_LENGTH: int = 4000  # characters

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/uploads")
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "txt", "docx"]

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Metrics (Feature 002)
    METRICS_HOURLY_RETENTION_DAYS: int = int(os.getenv("METRICS_HOURLY_RETENTION_DAYS", "30"))
    METRICS_DAILY_RETENTION_DAYS: int = int(os.getenv("METRICS_DAILY_RETENTION_DAYS", "90"))
    METRICS_FAILURES_RETENTION_DAYS: int = int(os.getenv("METRICS_FAILURES_RETENTION_DAYS", "30"))
    METRICS_EXPORT_RETENTION_HOURS: int = int(os.getenv("METRICS_EXPORT_RETENTION_HOURS", "1"))

    class Config:
        case_sensitive = True


settings = Settings()
