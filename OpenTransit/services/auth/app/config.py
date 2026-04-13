"""Auth service configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "auth"
    database_url: str = "postgresql+asyncpg://opentransit:opentransit_dev@localhost/opentransit_auth"
    redis_url: str = "redis://localhost:6379/0"

    # JWT settings
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # Password hashing
    bcrypt_rounds: int = 12


settings = Settings()
