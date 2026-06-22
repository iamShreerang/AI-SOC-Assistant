"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings — override via .env file or environment."""

    app_name: str = "AI SOC Assistant"
    debug: bool = False

    # Security / Authentication
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    allowed_algorithms: list[str] = ["HS256"]
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    refresh_secret_key: str = "change-this-refresh-secret-in-production"
    token_url: str = "/auth/login"

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/soc_db"

    # Kafka
    kafka_broker: str = "localhost:9092"
    kafka_topic_raw_logs: str = "raw-logs"

    # Elasticsearch
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_enabled: bool = True  # Set to False to use in-memory storage

    # LLM
    groq_api_key: str = ""

    # OAuth2 Providers
    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    oauth_redirect_uri: str = "http://localhost:8000/auth/callback"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"]

    class Config:
        env_file = ".env"


settings = Settings()               