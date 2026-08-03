"""
Spark Structured Streaming job.

Pipeline:
    Kafka (unsw-logs) → parse JSON → feature mapping → CNN-LSTM inference
                      → Threat Rules Engine → FastAPI backend ingest

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
import os
import sys
import time
import threading
from pathlib import Path

# ── Windows Environment Setup (JDK 17 & Hadoop winutils) ────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Check for project-local JDK 17
_local_jdk = REPO_ROOT / "tools" / "jdk-17.0.10+7"
if _local_jdk.exists():
    os.environ["JAVA_HOME"] = str(_local_jdk)
    _jdk_bin = _local_jdk / "bin"
    if str(_jdk_bin) not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{_jdk_bin}{os.pathsep}{os.environ.get('PATH', '')}"

# Check for project-local Hadoop winutils
_local_hadoop = REPO_ROOT / "tools" / "hadoop"
if _local_hadoop.exists():
    os.environ["HADOOP_HOME"] = str(_local_hadoop)
    _hadoop_bin = _local_hadoop / "bin"
    if str(_hadoop_bin) not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{_hadoop_bin}{os.pathsep}{os.environ.get('PATH', '')}"

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType, IntegerType, LongType, StringType, StructField, StructType,
)

from streaming.config import (
    BATCH_INTERVAL_SECS, HEARTBEAT_INTERVAL_SECS, KAFKA_BROKER, KAFKA_INPUT_TOPIC,
    KAFKA_OUTPUT_TOPIC, METRICS_PUBLISH_SECS, MODEL_DIR, SAMPLE_LOGS_DIR,
    SPARK_APP_NAME, SPARK_CHECKPOINT_DIR, SPARK_MASTER,
)
from streaming import backend_client
from streaming.spark.metrics import metrics
from streaming.spark.threat_rules import threat_rules

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Heartbeat interval in seconds (from config, overridable via env)
_HEARTBEAT_INTERVAL_SECS: int = HEARTBEAT_INTERVAL_SECS

# Module-level singletons — survive across foreachBatch calls in local[*] mode
_SINGLETONS: dict = {}

# Wall-clock timestamp of the last /ingest/metrics POST
_last_metrics_publish: float = 0.0

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
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1")
        .config("spark.sql.streaming.checkpointLocation", SPARK_CHECKPOINT_DIR)
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )


def _get_predictor():
    """Lazy-load predictor once per driver process."""
    if "predictor" not in _SINGLETONS:
        from ml.inference import Predictor
        from streaming.spark.feature_mapper import FeatureMapper
        logger.info("Loading CNN-LSTM predictor from %s", MODEL_DIR)
        p = Predictor.load(MODEL_DIR)
        _SINGLETONS["predictor"] = p
        _SINGLETONS["feature_mapper"] = FeatureMapper(p.pipeline)
        logger.info(
            "Predictor loaded — n_features=%d seq_len=%d threshold=%.2f device=%s",
            p.pipeline.n_features, p.seq_len, p.threshold, p.device,
        )
    return _SINGLETONS["predictor"]


def _get_predictions_producer():
    """Return a module-level Kafka producer singleton for publishing predictions.

    Creates on first call; returns cached instance on subsequent calls.
    All errors are swallowed so prediction publishing never crashes the job.
    """
    if "predictions_producer" not in _SINGLETONS:
        try:
            from kafka import KafkaProducer
            _SINGLETONS["predictions_producer"] = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks=0,  # fire-and-forget for best-effort output topic
            )
            logger.info("Predictions Kafka producer initialised (topic=%s)", KAFKA_OUTPUT_TOPIC)
        except Exception as e:
            logger.warning(
                "Could not initialise predictions producer — output topic disabled: %s", e
            )
            _SINGLETONS["predictions_producer"] = None
    return _SINGLETONS.get("predictions_producer")


def _process_batch(batch_df: DataFrame, batch_id: int) -> None:
    """foreachBatch handler — runs inference, evaluates threat rules, and
    persists results into the FastAPI backend. Used by both Kafka and local-test modes."""
    global _last_metrics_publish

    if batch_df.isEmpty():
        return

    rows = [row.asDict() for row in batch_df.collect()]
    logger.info("Spark received batch %d: processing %d records", batch_id, len(rows))

    predictor = _get_predictor()
    feature_mapper = _SINGLETONS["feature_mapper"]

    # ── Normalise raw field aliases before ML inference ─────────────────────
    # FeatureMapper._normalise_record() translates heterogeneous field names
    # (e.g. "Src IP", "Flow Duration") into the unified UNSW-NB15 schema that
    # the trained pipeline expects.  Without this step, non-UNSW fields get
    # zeroed out, producing inaccurate predictions.
    try:
        normalised_for_ml = feature_mapper.map_records(rows)
        # predict_batch expects a list[dict] with FEATURE_COLS keys;
        # we pass the normalised array via a thin DataFrame-backed wrapper.
        import pandas as pd
        from ml.preprocessing import FEATURE_COLS
        normalised_df_rows = [
            dict(zip(FEATURE_COLS, row.tolist())) for row in normalised_for_ml
        ]
        predictions = predictor.predict_batch(normalised_df_rows)
    except Exception as e:
        logger.error("ML inference failed on batch %d: %s", batch_id, e)
        return

    logger.info("ML model inference completed — %d predictions produced", len(predictions))

    # ── Align predictions back to source rows ───────────────────────────────
    # predict_batch() uses a sliding window of length seq_len, so it returns
    # (len(records) - seq_len + 1) results, each corresponding to the *last*
    # row of the window it consumed.  We align by mapping prediction[i] to
    # rows[i + seq_len - 1] (the anchor row for that window).
    seq_len = predictor.seq_len
    offset = max(0, seq_len - 1)  # first prediction corresponds to rows[offset]

    enriched = []
    for i, pred in enumerate(predictions):
        src_idx = min(i + offset, len(rows) - 1)
        src = rows[src_idx]
        enriched.append({
            **pred,
            "srcip":  src.get("srcip")  or src.get("Src IP")  or "",
            "dstip":  src.get("dstip")  or src.get("Dst IP")  or "",
            "sport":  src.get("sport")  or src.get("Src Port") or 0,
            "dsport": src.get("dsport") or src.get("Dst Port") or 0,
            "proto":  src.get("proto")  or src.get("Protocol") or "",
            "sbytes": src.get("sbytes") or src.get("TotLen Fwd Pkts") or 0,
            "dbytes": src.get("dbytes") or src.get("TotLen Bwd Pkts") or 0,
            "attack_cat": src.get("attack_cat") or "",
            "timestamp":  src.get("timestamp") or "",
        })

    attack_count = sum(1 for r in enriched if r.get("label") == 1)
    normal_count = len(enriched) - attack_count
    logger.info(
        "Batch %d results: %d anomalies detected, %d normal",
        batch_id, attack_count, normal_count,
    )

    metrics.update(enriched)

    # Threat detection rules
    alerts = threat_rules.evaluate(enriched)
    metrics.record_alerts(alerts)

    if alerts:
        logger.info("%d threat rules triggered in batch %d", len(alerts), batch_id)

    snap = metrics.snapshot()
    logger.info(
        "Metrics | total=%d rps=%.1f attacks=%d normal=%d avg_latency=%.2fms alerts=%d",
        snap["total_requests"], snap["requests_per_second"],
        snap["attack_count"], snap["normal_count"],
        snap["avg_inference_latency_ms"], len(alerts),
    )

    # ── Persist stream records into the backend database ────────────────────
    log_count = 0
    for rec in enriched:
        is_attack = rec.get("label") == 1 or (rec.get("attack_cat") and rec.get("attack_cat") != "Normal")
        if is_attack:
            severity = "critical" if rec.get("confidence", 0) >= 0.8 else "warning"
            msg = f"ML Attack Detected [{rec.get('attack_cat') or 'Threat'}]: {rec.get('srcip')}:{rec.get('sport')} -> {rec.get('dstip')}:{rec.get('dsport')} ({rec.get('proto')})"
        else:
            severity = "info"
            msg = f"Network Traffic: {rec.get('srcip')}:{rec.get('sport')} -> {rec.get('dstip')}:{rec.get('dsport')} ({rec.get('proto')})"

        ok = backend_client.post_log(
            source="spark-streaming",
            severity=severity,
            message=msg,
            timestamp=rec.get("timestamp") or None,
            raw=json.dumps({
                k: rec[k] for k in
                ("srcip", "dstip", "sport", "dsport", "proto",
                 "label", "confidence", "attack_probability", "attack_cat")
                if k in rec
            }),
        )
        if ok:
            log_count += 1

    if log_count:
        logger.info("Sent %d stream logs to backend /ingest/logs", log_count)

    # ── Persist generated alerts into the backend ────────────────────────────
    alert_count = 0
    for alert in alerts:
        ok = backend_client.post_alert(
            title=alert["title"],
            severity=alert["severity"],
            source=alert["source"],
            description=alert.get("description"),
        )
        if ok:
            alert_count += 1

    if alert_count:
        logger.info("Sent %d alerts to backend /ingest/alerts", alert_count)

    # ── Publish metrics on a slower cadence ─────────────────────────────────
    now = time.time()
    if now - _last_metrics_publish >= METRICS_PUBLISH_SECS:
        backend_client.post_metrics(snap)
        _last_metrics_publish = now

    # ── Publish predictions to output Kafka topic (best-effort) ─────────────
    _publish_predictions(enriched)


def _publish_predictions(predictions: list[dict]) -> None:
    """Best-effort publish to the predictions Kafka topic.

    Uses a module-level producer singleton so we don't create a new
    TCP connection on every micro-batch.
    """
    producer = _get_predictions_producer()
    if producer is None:
        return
    try:
        for p in predictions:
            producer.send(KAFKA_OUTPUT_TOPIC, p)
        producer.flush()
    except Exception as e:
        logger.warning(
            "Could not publish predictions to Kafka topic '%s': %s",
            KAFKA_OUTPUT_TOPIC, e,
        )
        # Invalidate cached producer so a fresh one is created next batch
        _SINGLETONS.pop("predictions_producer", None)


def _kafka_stream(spark: SparkSession) -> DataFrame:
    raw = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BROKER)
        .option("subscribe", KAFKA_INPUT_TOPIC)
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()
    )
    parsed = raw.select(F.from_json(F.col("value").cast("string"), _LOG_SCHEMA, {"mode": "PERMISSIVE"}).alias("data"))
    return parsed.filter(F.col("data").isNotNull()).select("data.*")


def _file_stream(spark: SparkSession) -> DataFrame:
    """Local-test mode: read JSONL files as a streaming source (no Kafka needed).

    PERMISSIVE mode ensures that records with unexpected/missing fields are
    parsed with nulls rather than causing the entire micro-batch to fail.
    """
    return (
        spark.readStream
        .schema(_LOG_SCHEMA)
        .option("maxFilesPerTrigger", 1)
        .option("mode", "PERMISSIVE")
        .json(SAMPLE_LOGS_DIR)
    )


def _heartbeat_loop() -> None:
    """Background thread: POST /ingest/heartbeat every _HEARTBEAT_INTERVAL_SECS."""
    logger.info("Heartbeat thread started (interval=%ds)", _HEARTBEAT_INTERVAL_SECS)
    # Send immediate heartbeat on startup so health check turns green instantly
    try:
        backend_client.post_heartbeat(service="spark", status="running")
    except Exception as e:
        logger.warning("Initial heartbeat POST failed: %s", e)

    while True:
        time.sleep(_HEARTBEAT_INTERVAL_SECS)
        try:
            backend_client.post_heartbeat(service="spark", status="running")
        except Exception as e:
            logger.warning("Heartbeat POST failed: %s", e)


def main(local_test: bool = False) -> None:
    spark = _build_spark()
    spark.sparkContext.setLogLevel("WARN")

    # Pre-load predictor so first batch doesn't pay the load cost
    try:
        _get_predictor()
    except Exception as e:
        logger.error("Failed to load ML predictor: %s", e)
        sys.exit(1)

    # Start heartbeat background thread
    hb_thread = threading.Thread(target=_heartbeat_loop, daemon=True)
    hb_thread.start()

    parsed = _file_stream(spark) if local_test else _kafka_stream(spark)

    query = (
        parsed.writeStream
        .foreachBatch(_process_batch)
        .trigger(processingTime=f"{BATCH_INTERVAL_SECS} seconds")
        .start()
    )

    mode = "file (local-test)" if local_test else f"Kafka '{KAFKA_INPUT_TOPIC}'"
    logger.info(
        "Spark Structured Streaming started — source=%s  output-topic=%s  batch=%ds",
        mode, KAFKA_OUTPUT_TOPIC, BATCH_INTERVAL_SECS,
    )
    query.awaitTermination()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-test", action="store_true",
                        help="Read from sample_logs/ instead of Kafka (no Docker needed)")
    args = parser.parse_args()
    main(local_test=args.local_test)
