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

# Backend API integration (POST /ingest/logs, /ingest/alerts, /ingest/metrics)
BACKEND_API_URL: str = os.getenv("BACKEND_API_URL", "http://localhost:8000")
BACKEND_API_TIMEOUT_SECS: float = float(os.getenv("BACKEND_API_TIMEOUT_SECS", "5"))
METRICS_PUBLISH_SECS: int = int(os.getenv("METRICS_PUBLISH_SECS", "15"))
HEARTBEAT_INTERVAL_SECS: int = int(os.getenv("HEARTBEAT_INTERVAL_SECS", "30"))

# Spark checkpoint (Linux/Docker default; override on native Windows)
SPARK_CHECKPOINT_DIR: str = os.getenv(
    "SPARK_CHECKPOINT_DIR",
    str(Path(__file__).parent / "checkpoint") if os.name == "nt" else "/tmp/soc-checkpoint",
)

# Threat detection rule thresholds
REPEAT_ATTACK_THRESHOLD: int = int(os.getenv("REPEAT_ATTACK_THRESHOLD", "3"))
REPEAT_ATTACK_WINDOW_SECS: int = int(os.getenv("REPEAT_ATTACK_WINDOW_SECS", "60"))
HIGH_RATE_THRESHOLD_PER_SEC: float = float(os.getenv("HIGH_RATE_THRESHOLD_PER_SEC", "20"))
LARGE_TRANSFER_BYTES: int = int(os.getenv("LARGE_TRANSFER_BYTES", "1000000"))
PORT_SCAN_DISTINCT_PORTS: int = int(os.getenv("PORT_SCAN_DISTINCT_PORTS", "6"))
PORT_SCAN_WINDOW_SECS: int = int(os.getenv("PORT_SCAN_WINDOW_SECS", "60"))
