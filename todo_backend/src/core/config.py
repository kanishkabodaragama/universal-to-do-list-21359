import os
from functools import lru_cache
from pydantic import BaseModel, Field
from typing import List, Tuple

# Attempt to load .env if present to support preview/development environments.
# This is safe even if python-dotenv is missing since it's in requirements.
try:
    from dotenv import load_dotenv

    # Load from project root and current working directory
    load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"), override=False)
except Exception:
    # Silently ignore if loading fails; environment variables may be injected by orchestration.
    pass


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

    def validate_required(self) -> List[Tuple[str, bool]]:
        """
        Validate presence of required environment variables.

        Returns:
            List of (name, is_present) for each required variable.
        """
        required = [
            ("SUPABASE_URL", bool(self.SUPABASE_URL)),
            ("SUPABASE_ANON_KEY", bool(self.SUPABASE_ANON_KEY)),
            ("SUPABASE_SERVICE_ROLE_KEY", bool(self.SUPABASE_SERVICE_ROLE_KEY)),
            ("JWT_SECRET_KEY", bool(self.JWT_SECRET_KEY and self.JWT_SECRET_KEY != "change-me")),
            ("JWT_ALGORITHM", bool(self.JWT_ALGORITHM)),
            ("ACCESS_TOKEN_EXPIRE_MINUTES", bool(self.ACCESS_TOKEN_EXPIRE_MINUTES)),
            ("SITE_URL", bool(self.SITE_URL)),
        ]
        return required


# PUBLIC_INTERFACE
@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
