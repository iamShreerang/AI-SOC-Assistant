"""Central configuration — all values overridable via environment variables."""
from __future__ import annotations

import os
from pathlib import Path

# Kafka
KAFKA_BROKER: str = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_INPUT_TOPIC: str = os.getenv("KAFKA_INPUT_TOPIC", "unsw-logs")
KAFKA_OUTPUT_TOPIC: str = os.getenv("KAFKA_OUTPUT_TOPIC", "predictions")

# Spark
SPARK_MASTER: str = os.getenv("SPARK_MASTER", "local[*]")
SPARK_APP_NAME: str = os.getenv("SPARK_APP_NAME", "AI-SOC-Streaming")

# ML artifacts
_REPO_ROOT = Path(__file__).parent.parent
MODEL_DIR: str = os.getenv("MODEL_DIR", str(_REPO_ROOT / "ml" / "saved_models"))
PIPELINE_DIR: str = os.getenv("PIPELINE_DIR", MODEL_DIR)

# Streaming
BATCH_INTERVAL_SECS: int = int(os.getenv("BATCH_INTERVAL_SECS", "5"))
SEQUENCE_LENGTH: int = int(os.getenv("SEQUENCE_LENGTH", "10"))

# Producer
PRODUCER_DELAY_SECS: float = float(os.getenv("PRODUCER_DELAY_SECS", "0.5"))
SAMPLE_LOGS_DIR: str = os.getenv("SAMPLE_LOGS_DIR", str(Path(__file__).parent / "sample_logs"))
