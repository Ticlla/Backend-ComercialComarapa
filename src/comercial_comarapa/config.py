"""Application configuration using pydantic-settings.

This module loads configuration from environment variables and .env files.
All settings are validated at startup.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        app_name: Name of the application
        app_env: Environment (development, staging, production)
        debug: Enable debug mode
        api_version: API version string

        host: Server host address
        port: Server port number

        supabase_url: Supabase project URL
        supabase_key: Supabase anonymous key
        supabase_service_key: Supabase service role key (optional)

        cors_origins: List of allowed CORS origins
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="comercial-comarapa-api")
    app_env: str = Field(default="development")
    debug: bool = Field(default=True)
    api_version: str = Field(default="v1")

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # Database Mode: "local" or "supabase"
    database_mode: str = Field(default="local")

    # Local PostgreSQL (when database_mode=local)
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/comercial_comarapa"
    )

    # Supabase (when database_mode=supabase)
    supabase_url: str = Field(default="")
    supabase_key: str = Field(default="")
    supabase_service_key: str = Field(default="")

    # CORS
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:5173")

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"

    @property
    def is_local_db(self) -> bool:
        """Check if using local PostgreSQL database."""
        return self.database_mode.lower() == "local"

    @property
    def is_supabase_db(self) -> bool:
        """Check if using Supabase cloud database."""
        return self.database_mode.lower() == "supabase"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.

    Returns:
        Settings instance with loaded configuration.
    """
    return Settings()


# Convenience export
settings = get_settings()
