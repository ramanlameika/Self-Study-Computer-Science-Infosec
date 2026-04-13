"""Agency service configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "agency"
    database_url: str = "postgresql+asyncpg://opentransit:opentransit_dev@localhost/opentransit_agency"
    redis_url: str = "redis://localhost:6379/3"
    auth_service_url: str = "http://localhost:8001"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"


settings = Settings()
