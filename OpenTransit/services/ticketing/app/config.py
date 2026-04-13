"""Ticketing service configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "ticketing"
    database_url: str = "postgresql+asyncpg://opentransit:opentransit_dev@localhost/opentransit_ticketing"
    redis_url: str = "redis://localhost:6379/1"
    auth_service_url: str = "http://localhost:8001"
    fare_service_url: str = "http://localhost:8003"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"

    # QR code signing key (separate from JWT secret)
    qr_secret_key: str = "change-me-qr-in-production"

    # Ticket validity window in minutes
    single_ticket_validity_minutes: int = 90


settings = Settings()
