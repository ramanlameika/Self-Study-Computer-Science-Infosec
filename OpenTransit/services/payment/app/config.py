"""Payment service configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "payment"
    database_url: str = "postgresql+asyncpg://opentransit:opentransit_dev@localhost/opentransit_payment"
    redis_url: str = "redis://localhost:6379/4"
    auth_service_url: str = "http://localhost:8001"
    ticketing_service_url: str = "http://localhost:8002"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    stripe_secret_key: str = "sk_test_placeholder"
    enable_sandbox_mode: bool = True


settings = Settings()
