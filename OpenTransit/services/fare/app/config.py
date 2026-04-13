"""Fare service configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "fare"
    database_url: str = "postgresql+asyncpg://opentransit:opentransit_dev@localhost/opentransit_fare"
    redis_url: str = "redis://localhost:6379/2"
    auth_service_url: str = "http://localhost:8001"
    agency_service_url: str = "http://localhost:8004"


settings = Settings()
