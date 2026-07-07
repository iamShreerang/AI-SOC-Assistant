"""
Spark Structured Streaming job.

Pipeline:
    Kafka (unsw-logs) → parse JSON → feature mapping → CNN-LSTM inference
                      → predictions topic + console metrics

Usage:
    py streaming/spark/streaming_job.py                  # Kafka mode
    py streaming/spark/streaming_job.py --local-test     # file source, no Docker needed

Environment variables (see streaming/config.py):
    KAFKA_BROKER, KAFKA_INPUT_TOPIC, KAFKA_OUTPUT_TOPIC,
    SPARK_MASTER, MODEL_DIR, BATCH_INTERVAL_SECS
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType, IntegerType, LongType, StringType, StructField, StructType,
)

from streaming.config import (
    BATCH_INTERVAL_SECS, KAFKA_BROKER, KAFKA_INPUT_TOPIC, KAFKA_OUTPUT_TOPIC,
    MODEL_DIR, SAMPLE_LOGS_DIR, SPARK_APP_NAME, SPARK_MASTER,
)
from streaming.spark.metrics import metrics

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Module-level singleton — survives across foreachBatch calls in local[*] mode
_SINGLETONS: dict = {}

# ── Kafka message schema ────────────────────────────────────────────────────
_LOG_SCHEMA = StructType([
    StructField("timestamp", StringType()),
    StructField("srcip", StringType()),
    StructField("dstip", StringType()),
    StructField("sport", IntegerType()),
    StructField("dsport", IntegerType()),
    StructField("proto", StringType()),
    StructField("service", StringType()),
    StructField("state", StringType()),
    StructField("dur", DoubleType()),
    StructField("sbytes", LongType()),
    StructField("dbytes", LongType()),
    StructField("rate", DoubleType()),
    StructField("sttl", IntegerType()),
    StructField("dttl", IntegerType()),
    StructField("sload", DoubleType()),
    StructField("dload", DoubleType()),
    StructField("sloss", IntegerType()),
    StructField("dloss", IntegerType()),
    StructField("spkts", IntegerType()),
    StructField("dpkts", IntegerType()),
    StructField("sinpkt", DoubleType()),
    StructField("dinpkt", DoubleType()),
    StructField("sjit", DoubleType()),
    StructField("djit", DoubleType()),
    StructField("swin", IntegerType()),
    StructField("dwin", IntegerType()),
    StructField("stcpb", LongType()),
    StructField("dtcpb", LongType()),
    StructField("tcprtt", DoubleType()),
    StructField("synack", DoubleType()),
    StructField("ackdat", DoubleType()),
    StructField("smean", IntegerType()),
    StructField("dmean", IntegerType()),
    StructField("trans_depth", IntegerType()),
    StructField("response_body_len", LongType()),
    StructField("ct_srv_src", IntegerType()),
    StructField("ct_state_ttl", IntegerType()),
    StructField("ct_dst_ltm", IntegerType()),
    StructField("ct_src_dport_ltm", IntegerType()),
    StructField("ct_dst_sport_ltm", IntegerType()),
    StructField("ct_dst_src_ltm", IntegerType()),
    StructField("is_ftp_login", IntegerType()),
    StructField("ct_ftp_cmd", IntegerType()),
    StructField("ct_flw_http_mthd", IntegerType()),
    StructField("ct_src_ltm", IntegerType()),
    StructField("ct_srv_dst", IntegerType()),
    StructField("is_sm_ips_ports", IntegerType()),
    StructField("attack_cat", StringType()),
    StructField("label", IntegerType()),
    # Backend log_generator fields (mapped by FeatureMapper)
    StructField("Dst IP", StringType()),
    StructField("Src IP", StringType()),
    StructField("Dst Port", IntegerType()),
    StructField("Protocol", StringType()),
    StructField("Flow Duration", LongType()),
    StructField("Tot Fwd Pkts", IntegerType()),
    StructField("Tot Bwd Pkts", IntegerType()),
    StructField("TotLen Fwd Pkts", LongType()),
    StructField("TotLen Bwd Pkts", LongType()),
    StructField("Flow Byts/s", DoubleType()),
    StructField("Flow Pkts/s", DoubleType()),
])


def _build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .master(SPARK_MASTER)
        .appName(SPARK_APP_NAME)
        .config("spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0")
        .config("spark.sql.streaming.checkpointLocation", "/tmp/soc-checkpoint")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )


def _get_predictor():
    """Lazy-load predictor once per driver process."""
    if "predictor" not in _SINGLETONS:
        from ml.inference import Predictor
        from streaming.spark.feature_mapper import FeatureMapper
        p = Predictor.load(MODEL_DIR)
        _SINGLETONS["predictor"] = p
        _SINGLETONS["feature_mapper"] = FeatureMapper(p.pipeline)
        logger.info("Predictor loaded from %s", MODEL_DIR)
    return _SINGLETONS["predictor"]


def _process_batch(batch_df: DataFrame, batch_id: int) -> None:
    """foreachBatch handler — runs inference and publishes predictions."""
    if batch_df.isEmpty():
        return

    rows = [row.asDict() for row in batch_df.collect()]
    logger.info("Batch %d: %d records", batch_id, len(rows))

    predictor = _get_predictor()
    try:
        predictions = predictor.predict_batch(rows)
    except Exception as e:
        logger.error("Inference failed: %s", e)
        return

    # Merge predictions back with source IPs for metrics
    enriched = []
    for i, pred in enumerate(predictions):
        src = rows[min(i, len(rows) - 1)]
        enriched.append({
            **pred,
            "srcip": src.get("srcip", src.get("Src IP", "")),
            "dstip": src.get("dstip", src.get("Dst IP", "")),
            "sbytes": src.get("sbytes", src.get("TotLen Fwd Pkts", 0)) or 0,
            "dbytes": src.get("dbytes", src.get("TotLen Bwd Pkts", 0)) or 0,
        })

    metrics.update(enriched)
    snap = metrics.snapshot()
    logger.info(
        "Metrics | total=%d rps=%.1f attacks=%d normal=%d avg_latency=%.2fms",
        snap["total_requests"], snap["requests_per_second"],
        snap["attack_count"], snap["normal_count"],
        snap["avg_inference_latency_ms"],
    )

    # Publish predictions to output Kafka topic
    _publish_predictions(enriched)


def _publish_predictions(predictions: list[dict]) -> None:
    try:
        from kafka import KafkaProducer
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        for p in predictions:
            producer.send(KAFKA_OUTPUT_TOPIC, p)
        producer.flush()
        producer.close()
    except Exception as e:
        logger.warning("Could not publish predictions to Kafka: %s", e)


def _kafka_stream(spark: SparkSession) -> DataFrame:
    raw = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BROKER)
        .option("subscribe", KAFKA_INPUT_TOPIC)
        .option("startingOffsets", "latest")
        .option("failOnDataLoss", "false")
        .load()
    )
    return (
        raw
        .select(F.from_json(F.col("value").cast("string"), _LOG_SCHEMA).alias("data"))
        .select("data.*")
    )


def _file_stream(spark: SparkSession) -> DataFrame:
    """Local-test mode: read JSONL files as a streaming source (no Kafka needed)."""
    return (
        spark.readStream
        .schema(_LOG_SCHEMA)
        .option("maxFilesPerTrigger", 1)
        .json(SAMPLE_LOGS_DIR)
    )


def main(local_test: bool = False) -> None:
    spark = _build_spark()
    spark.sparkContext.setLogLevel("WARN")

    parsed = _file_stream(spark) if local_test else _kafka_stream(spark)

    query = (
        parsed.writeStream
        .foreachBatch(_process_batch)
        .trigger(processingTime=f"{BATCH_INTERVAL_SECS} seconds")
        .start()
    )

    mode = "file (local-test)" if local_test else f"Kafka '{KAFKA_INPUT_TOPIC}'"
    logger.info("Streaming job started — source=%s  output-topic=%s", mode, KAFKA_OUTPUT_TOPIC)
    query.awaitTermination()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-test", action="store_true",
                        help="Read from sample_logs/ instead of Kafka (no Docker needed)")
    args = parser.parse_args()
    main(local_test=args.local_test)
