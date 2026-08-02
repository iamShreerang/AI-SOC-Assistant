"""
Kafka producer — reads JSONL files from sample_logs/ and publishes to Kafka.

Usage:
    py streaming/kafka/producer.py
    py streaming/kafka/producer.py --continuous   # loop forever
"""
from __future__ import annotations

import argparse
import json
import logging
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from streaming.config import KAFKA_BROKER, KAFKA_INPUT_TOPIC, PRODUCER_DELAY_SECS, SAMPLE_LOGS_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_shutdown_requested = False

_REQUIRED_ANY_KEYS = ("srcip", "Src IP", "timestamp", "Timestamp")

_CONNECT_RETRY_SECS = 5
_CONNECT_MAX_RETRIES = 12  # ~60 s total before giving up


def _validate_record(record: dict) -> bool:
    if not isinstance(record, dict) or not record:
        return False
    return any(key in record for key in _REQUIRED_ANY_KEYS)


def _install_shutdown_handler() -> None:
    def _handler(signum, frame):
        global _shutdown_requested
        logger.info("Received signal %s — shutting down after current file", signum)
        _shutdown_requested = True

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)


def get_producer(broker: str):
    """Create KafkaProducer with retries on connection failure."""
    from kafka import KafkaProducer
    from kafka.errors import NoBrokersAvailable

    for attempt in range(1, _CONNECT_MAX_RETRIES + 1):
        try:
            producer = KafkaProducer(
                bootstrap_servers=[broker],
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                retries=5,
                retry_backoff_ms=500,
                request_timeout_ms=30000,
            )
            logger.info("Kafka producer connected to %s", broker)
            return producer
        except NoBrokersAvailable:
            if attempt == _CONNECT_MAX_RETRIES:
                logger.error(
                    "Kafka broker %s unreachable after %d attempts — aborting",
                    broker, _CONNECT_MAX_RETRIES,
                )
                raise
            logger.warning(
                "Kafka broker %s not available (attempt %d/%d) — retrying in %ds",
                broker, attempt, _CONNECT_MAX_RETRIES, _CONNECT_RETRY_SECS,
            )
            time.sleep(_CONNECT_RETRY_SECS)


def publish_file(producer, path: Path, topic: str, delay: float) -> int:
    count = 0
    skipped = 0
    with open(path) as f:
        for line in f:
            if _shutdown_requested:
                break
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning("Skipping malformed line in %s: %s", path.name, e)
                skipped += 1
                continue
            if not _validate_record(record):
                logger.warning("Skipping record missing required fields: %s", list(record.keys())[:5])
                skipped += 1
                continue
            producer.send(topic, record)
            count += 1
            if delay > 0:
                time.sleep(delay)
    producer.flush()
    if skipped:
        logger.info("Skipped %d invalid/malformed records in %s", skipped, path.name)
    return count


def run(broker: str, topic: str, logs_dir: str, delay: float, continuous: bool) -> None:
    _install_shutdown_handler()

    try:
        producer = get_producer(broker)
    except Exception as e:
        logger.error("Failed to connect to Kafka: %s", e)
        sys.exit(1)

    logs_path = Path(logs_dir)

    try:
        while not _shutdown_requested:
            files = sorted(logs_path.glob("*.jsonl"))
            if not files:
                logger.warning(
                    "No .jsonl files found in %s — run: py streaming/sample_logs/generate.py",
                    logs_path,
                )
                if not continuous:
                    break
                time.sleep(5)
                continue

            for f in files:
                if _shutdown_requested:
                    break
                logger.info("Publishing %s → topic=%s", f.name, topic)
                n = publish_file(producer, f, topic, delay)
                logger.info("Published %d records from %s to topic '%s'", n, f.name, topic)

            if not continuous or _shutdown_requested:
                break
            logger.info("Completed pass — sleeping 2s before next loop")
            time.sleep(2)
    finally:
        logger.info("Flushing and closing Kafka producer...")
        try:
            producer.flush()
            producer.close()
            logger.info("Kafka producer closed cleanly")
        except Exception as e:
            logger.warning("Error closing producer: %s", e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--broker", default=KAFKA_BROKER)
    parser.add_argument("--topic", default=KAFKA_INPUT_TOPIC)
    parser.add_argument("--logs-dir", default=SAMPLE_LOGS_DIR)
    parser.add_argument("--delay", type=float, default=PRODUCER_DELAY_SECS)
    parser.add_argument("--continuous", action="store_true")
    args = parser.parse_args()

    run(args.broker, args.topic, args.logs_dir, args.delay, args.continuous)
