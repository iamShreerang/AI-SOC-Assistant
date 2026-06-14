"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings — override via .env file or environment."""

    app_name: str = "AI SOC Assistant"
    debug: bool = False

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/soc_db"

    # Kafka
    kafka_broker: str = "localhost:9092"
    kafka_topic_raw_logs: str = "raw-logs"

    # Elasticsearch
    elasticsearch_url: str = "http://localhost:9200"

    class Config:
        env_file = ".env"


settings = Settings()
