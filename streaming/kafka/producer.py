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
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from streaming.config import KAFKA_BROKER, KAFKA_INPUT_TOPIC, PRODUCER_DELAY_SECS, SAMPLE_LOGS_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def get_producer(broker: str):
    from kafka import KafkaProducer
    return KafkaProducer(
        bootstrap_servers=[broker],
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",
        retries=3,
    )


def publish_file(producer, path: Path, topic: str, delay: float) -> int:
    count = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                producer.send(topic, record)
                count += 1
                if delay > 0:
                    time.sleep(delay)
            except json.JSONDecodeError as e:
                logger.warning("Skipping malformed line: %s", e)
    producer.flush()
    return count


def run(broker: str, topic: str, logs_dir: str, delay: float, continuous: bool) -> None:
    producer = get_producer(broker)
    logs_path = Path(logs_dir)

    while True:
        files = sorted(logs_path.glob("*.jsonl"))
        if not files:
            logger.warning("No .jsonl files found in %s — run generate.py first", logs_path)
            if not continuous:
                break
            time.sleep(5)
            continue

        for f in files:
            logger.info("Publishing %s → topic=%s", f.name, topic)
            n = publish_file(producer, f, topic, delay)
            logger.info("Published %d records from %s", n, f.name)

        if not continuous:
            break
        logger.info("Looping — sleeping 2s before next pass")
        time.sleep(2)

    producer.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--broker", default=KAFKA_BROKER)
    parser.add_argument("--topic", default=KAFKA_INPUT_TOPIC)
    parser.add_argument("--logs-dir", default=SAMPLE_LOGS_DIR)
    parser.add_argument("--delay", type=float, default=PRODUCER_DELAY_SECS)
    parser.add_argument("--continuous", action="store_true")
    args = parser.parse_args()

    run(args.broker, args.topic, args.logs_dir, args.delay, args.continuous)
