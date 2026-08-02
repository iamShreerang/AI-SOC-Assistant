"""
Pure Python Streaming Simulator — runs the real ML anomaly pipeline on Windows
without requiring Hadoop/winutils or Docker.

Pipeline:
  sample_logs/ -> FeatureMapper -> CNN-LSTM Predictor -> ThreatRuleEngine
               -> FastAPI backend (/ingest/logs, /ingest/alerts, /ingest/heartbeat, /ingest/metrics)

Usage:
  python streaming/run_local_pipeline.py
  python streaming/run_local_pipeline.py --delay 0.5 --loop
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.inference import Predictor
from ml.preprocessing import FEATURE_COLS
from streaming import backend_client
from streaming.spark.feature_mapper import FeatureMapper
from streaming.spark.metrics import metrics
from streaming.spark.threat_rules import threat_rules

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("local_pipeline")

MODEL_DIR = REPO_ROOT / "ml" / "saved_models"
SAMPLE_LOGS = REPO_ROOT / "streaming" / "sample_logs" / "logs_real_unsw_sample.jsonl"


def run_pipeline(batch_size: int = 20, delay: float = 1.0, loop: bool = True):
    logger.info("Initializing AI SOC ML Pipeline...")
    
    if not MODEL_DIR.exists():
        logger.error("Model directory not found: %s", MODEL_DIR)
        return

    predictor = Predictor.load(MODEL_DIR)
    feature_mapper = FeatureMapper(predictor.pipeline)
    logger.info(
        "Predictor loaded — features=%d seq_len=%d threshold=%.2f device=%s",
        predictor.pipeline.n_features, predictor.seq_len, predictor.threshold, predictor.device,
    )

    if not SAMPLE_LOGS.exists():
        logger.error("Sample logs file not found: %s", SAMPLE_LOGS)
        return

    records = []
    with open(SAMPLE_LOGS, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    logger.info("Loaded %d sample security logs from %s", len(records), SAMPLE_LOGS.name)
    logger.info("Starting live log streaming to backend (%s)...", backend_client.BACKEND_API_URL)

    batch_idx = 0
    record_offset = 0

    while True:
        # Fetch batch slice
        if record_offset >= len(records):
            if not loop:
                logger.info("Completed processing all %d sample logs.", len(records))
                break
            record_offset = 0  # Restart loop for continuous streaming simulation

        chunk = records[record_offset : record_offset + batch_size]
        record_offset += batch_size
        batch_idx += 1

        logger.info("Processing micro-batch #%d (%d records)...", batch_idx, len(chunk))

        # Send heartbeat
        backend_client.post_heartbeat(service="spark-local", status="running")

        # Feature normalization & ML Inference
        try:
            normalised = feature_mapper.map_records(chunk)
            normalised_dicts = [dict(zip(FEATURE_COLS, row.tolist())) for row in normalised]
            predictions = predictor.predict_batch(normalised_dicts)
        except Exception as e:
            logger.error("Inference failed on batch #%d: %s", batch_idx, e)
            time.sleep(delay)
            continue

        # Align predictions back to raw chunk records
        seq_len = predictor.seq_len
        offset = max(0, seq_len - 1)
        enriched = []
        for i, pred in enumerate(predictions):
            src_idx = min(i + offset, len(chunk) - 1)
            src = chunk[src_idx]
            enriched.append({
                **pred,
                "srcip": src.get("srcip") or src.get("Src IP") or "192.168.1.100",
                "dstip": src.get("dstip") or src.get("Dst IP") or "10.0.0.1",
                "sport": src.get("sport") or src.get("Src Port") or 0,
                "dsport": src.get("dsport") or src.get("Dst Port") or 80,
                "proto": src.get("proto") or src.get("Protocol") or "tcp",
                "sbytes": src.get("sbytes") or src.get("TotLen Fwd Pkts") or 0,
                "dbytes": src.get("dbytes") or src.get("TotLen Bwd Pkts") or 0,
                "attack_cat": src.get("attack_cat") or "",
                "timestamp": src.get("timestamp") or "",
            })

        # Update pipeline metrics
        metrics.update(enriched)

        # Evaluate Threat Rules
        alerts = threat_rules.evaluate(enriched)
        metrics.record_alerts(alerts)

        snap = metrics.snapshot()
        logger.info(
            "Batch #%d | total=%d anomalies=%d normal=%d latency=%.2fms alerts=%d",
            batch_idx, snap["total_requests"], snap["attack_count"],
            snap["normal_count"], snap["avg_inference_latency_ms"], len(alerts),
        )

        # Ingest attack logs into backend
        logs_sent = 0
        for rec in enriched:
            if rec.get("label") == 1:
                severity = "critical" if rec.get("confidence", 0) >= 0.9 else "warning"
                msg = (
                    f"ML anomaly detected: {rec.get('srcip')} -> {rec.get('dstip')} "
                    f"[{rec.get('attack_cat') or 'unknown'}] conf={rec.get('confidence', 0):.2f}"
                )
                if backend_client.post_log(source="ml-pipeline", severity=severity, message=msg):
                    logs_sent += 1

        if logs_sent:
            logger.info("Ingested %d attack log(s) into backend", logs_sent)

        # Ingest threat alerts into backend
        alerts_sent = 0
        for alert in alerts:
            if backend_client.post_alert(
                title=alert["title"],
                severity=alert["severity"],
                source=alert["source"],
                description=alert.get("description"),
            ):
                alerts_sent += 1

        if alerts_sent:
            logger.info("Ingested %d threat alert(s) into backend", alerts_sent)

        # Publish metrics
        backend_client.post_metrics(snap)

        time.sleep(delay)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run local pure-Python AI SOC streaming pipeline")
    parser.add_argument("--batch-size", type=int, default=20, help="Records per micro-batch")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay in seconds between batches")
    parser.add_argument("--once", action="store_true", help="Run through sample logs once instead of looping")
    args = parser.parse_args()

    run_pipeline(batch_size=args.batch_size, delay=args.delay, loop=not args.once)
