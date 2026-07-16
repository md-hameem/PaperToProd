"""
Application configuration loaded from environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_env: str = "development"
    debug: bool = True
    log_level: str = "debug"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]

    # Database
    database_url: str = "postgresql+asyncpg://papertoprod:changeme@localhost:5432/papertoprod"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_use_ssl: bool = False

    # JWT
    jwt_secret_key: str = "changeme"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # GitHub OAuth
    github_client_id: str = ""
    github_client_secret: str = ""

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # LLM Providers
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    primary_model: str = "claude-sonnet-4-20250514"
    fallback_model: str = "gpt-4o"
    cheap_model: str = "gpt-4o-mini"

    # Sandbox
    sandbox_service_url: str = "http://localhost:8001"
    sandbox_max_execution_time_seconds: int = 600
    sandbox_max_memory_mb: int = 4096
    sandbox_max_retries: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
