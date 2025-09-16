import os
from functools import lru_cache
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings loaded from environment variables."""
    # Supabase config
    SUPABASE_URL: str = Field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    SUPABASE_ANON_KEY: str = Field(default_factory=lambda: os.getenv("SUPABASE_ANON_KEY", ""))
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default_factory=lambda: os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""))

    # JWT config
    JWT_SECRET_KEY: str = Field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", "change-me"))
    JWT_ALGORITHM: str = Field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # CORS
    CORS_ALLOW_ORIGINS: list[str] = Field(
        default_factory=lambda: os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
    )

    # App
    ENV: str = Field(default_factory=lambda: os.getenv("ENV", "development"))
    SITE_URL: str = Field(default_factory=lambda: os.getenv("SITE_URL", "http://localhost:8000"))


# PUBLIC_INTERFACE
@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
