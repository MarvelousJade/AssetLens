import os
from dataclasses import dataclass


def normalize_database_url(value: str) -> str:
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


@dataclass(frozen=True)
class Settings:
    database_url: str = normalize_database_url(
        os.getenv("DATABASE_URL", "sqlite:///./assetlens.db")
    )
    demo_token: str = os.getenv("DEMO_TOKEN", "assetlens-demo-token")
    web_origin: str = os.getenv("WEB_ORIGIN", "http://localhost:3000")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    task_mode: str = os.getenv("TASK_MODE", "local")
    copilot_provider: str = os.getenv("COPILOT_PROVIDER", "auto")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5.6-sol")
    otel_endpoint: str | None = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or None
    service_name: str = os.getenv("OTEL_SERVICE_NAME", "assetlens-api")


settings = Settings()
