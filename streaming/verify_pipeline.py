"""
verify_pipeline.py -- end-to-end smoke test for the streaming pipeline.
No Docker or Kafka required.

Checks:
  1. ML artifacts exist and load correctly
  2. Feature mapper normalises raw records to correct shape
  3. Predictor runs inference and returns valid predictions
  4. Streaming metrics accumulate correctly
  5. Mock log generator produces valid UNSW-NB15-compatible records
  6. Measures end-to-end latency

Usage:
    py streaming/verify_pipeline.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def check(name: str, condition: bool, detail: str = "") -> bool:
    status = "[PASS]" if condition else "[FAIL]"
    suffix = f" -- {detail}" if detail else ""
    print(f"  {status} {name}{suffix}")
    return condition


def section(title: str) -> None:
    print(f"\n{'-' * 55}")
    print(f"  {title}")
    print(f"{'-' * 55}")


def main() -> None:
    all_passed = True

    # 1. Artifacts
    section("1. ML Artifacts")
    from streaming.config import MODEL_DIR
    model_pt = Path(MODEL_DIR) / "cnn_lstm.pt"
    pipeline_pkl = Path(MODEL_DIR) / "pipeline.pkl"
    all_passed &= check("cnn_lstm.pt exists", model_pt.exists(), str(model_pt))
    all_passed &= check("pipeline.pkl exists", pipeline_pkl.exists(), str(pipeline_pkl))

    # 2. Predictor load
    section("2. Predictor Load")
    try:
        from ml.inference import Predictor
        predictor = Predictor.load(MODEL_DIR)
        all_passed &= check(
            "Predictor.load()", True,
            f"n_features={predictor.pipeline.n_features} seq_len={predictor.seq_len}",
        )
    except Exception as e:
        all_passed &= check("Predictor.load()", False, str(e))
        print("  Cannot continue without predictor.")
        sys.exit(1)

    # 3. Feature mapper
    section("3. Feature Mapper")
    from streaming.spark.feature_mapper import FeatureMapper
    mapper = FeatureMapper(predictor.pipeline)
    expected_features = predictor.pipeline.n_features

    unsw_record = {
        "proto": "tcp", "service": "http", "state": "CON",
        "dur": 0.5, "sbytes": 500, "dbytes": 200, "rate": 100.0,
        "sttl": 64, "dttl": 64, "sload": 1000.0, "dload": 500.0,
        "sloss": 0, "dloss": 0, "spkts": 5, "dpkts": 3,
        "sinpkt": 10.0, "dinpkt": 10.0, "sjit": 1.0, "djit": 1.0,
        "swin": 255, "dwin": 255, "stcpb": 0, "dtcpb": 0,
        "tcprtt": 0.01, "synack": 0.005, "ackdat": 0.005,
        "smean": 100, "dmean": 80, "trans_depth": 0, "response_body_len": 0,
        "ct_srv_src": 5, "ct_state_ttl": 2, "ct_dst_ltm": 3,
        "ct_src_dport_ltm": 2, "ct_dst_sport_ltm": 2, "ct_dst_src_ltm": 2,
        "is_ftp_login": 0, "ct_ftp_cmd": 0, "ct_flw_http_mthd": 1,
        "ct_src_ltm": 3, "ct_srv_dst": 4, "is_sm_ips_ports": 0,
    }
    cic_record = {
        "Src IP": "192.168.1.10", "Dst IP": "10.0.0.5",
        "Protocol": "TCP", "Dst Port": 80,
        "Flow Duration": 300000, "Tot Fwd Pkts": 8, "Tot Bwd Pkts": 4,
        "TotLen Fwd Pkts": 600, "TotLen Bwd Pkts": 300,
        "Flow Byts/s": 2000.0, "Flow Pkts/s": 40.0,
    }

    X_unsw = mapper.map_records([unsw_record])
    X_cic = mapper.map_records([cic_record])

    all_passed &= check(
        "UNSW record -> correct shape",
        X_unsw.shape == (1, expected_features),
        f"got {X_unsw.shape}, expected (1, {expected_features})",
    )
    all_passed &= check(
        "CIC record -> correct shape",
        X_cic.shape == (1, expected_features),
        f"got {X_cic.shape}, expected (1, {expected_features})",
    )
    all_passed &= check("Feature dtype is float32", str(X_unsw.dtype) == "float32")

    # 4. Inference
    section("4. CNN-LSTM Inference")
    records_15 = [unsw_record] * 15

    t0 = time.perf_counter()
    results = predictor.predict_batch(records_15)
    total_ms = (time.perf_counter() - t0) * 1000

    all_passed &= check("predict_batch returns list", isinstance(results, list))
    all_passed &= check(
        "Correct number of predictions",
        len(results) == len(records_15) - predictor.seq_len + 1,
        f"got {len(results)}",
    )
    all_passed &= check(
        "Each result has required keys",
        all({"label", "label_name", "confidence", "latency_ms"} <= set(r.keys()) for r in results),
    )
    all_passed &= check("Labels are 0 or 1", all(r["label"] in (0, 1) for r in results))
    all_passed &= check(
        "Confidence in [0, 1]",
        all(0.0 <= r["confidence"] <= 1.0 for r in results),
    )
    avg_ms = total_ms / len(results) if results else 0
    print(f"  [INFO] Latency: {total_ms:.1f}ms total, {avg_ms:.2f}ms/prediction")

    # 5. Mock log generator
    section("5. Mock Log Generator")
    from streaming.sample_logs.generate import generate_record
    sample = generate_record()
    required_keys = {"srcip", "dstip", "proto", "service", "state",
                     "dur", "sbytes", "dbytes", "label", "attack_cat"}
    missing = required_keys - set(sample.keys())
    all_passed &= check("generate_record() has required keys", not missing, f"missing: {missing}")
    all_passed &= check("label is 0 or 1", sample["label"] in (0, 1))

    gen_records = [generate_record() for _ in range(20)]
    X_gen = mapper.map_records(gen_records)
    all_passed &= check(
        "Generated records map to correct shape",
        X_gen.shape == (20, expected_features),
        f"got {X_gen.shape}",
    )

    # 6. Streaming metrics
    section("6. Streaming Metrics")
    from streaming.spark.metrics import StreamingMetrics
    m = StreamingMetrics()
    batch = [
        {"label": 1, "srcip": "1.1.1.1", "dstip": "2.2.2.2",
         "sbytes": 500, "dbytes": 200, "latency_ms": 1.5},
        {"label": 0, "srcip": "3.3.3.3", "dstip": "4.4.4.4",
         "sbytes": 100, "dbytes": 50, "latency_ms": 0.8},
        {"label": 1, "srcip": "1.1.1.1", "dstip": "5.5.5.5",
         "sbytes": 800, "dbytes": 400, "latency_ms": 1.2},
    ]
    m.update(batch)
    snap = m.snapshot()

    all_passed &= check("total_requests == 3", snap["total_requests"] == 3)
    all_passed &= check("attack_count == 2", snap["attack_count"] == 2)
    all_passed &= check("normal_count == 1", snap["normal_count"] == 1)
    all_passed &= check("unique_src_ips == 2", snap["unique_src_ips"] == 2)
    all_passed &= check("unique_dst_ips == 3", snap["unique_dst_ips"] == 3)
    all_passed &= check("total_bytes_transferred == 2050", snap["total_bytes_transferred"] == 2050)
    all_passed &= check(
        "avg_inference_latency_ms > 0",
        snap["avg_inference_latency_ms"] > 0,
        f"{snap['avg_inference_latency_ms']}ms",
    )

    # 7. Sample logs file
    section("7. Sample Logs File")
    logs_dir = Path(__file__).parent / "sample_logs"
    jsonl_files = sorted(logs_dir.glob("*.jsonl"))
    all_passed &= check(
        "At least one .jsonl file exists",
        len(jsonl_files) > 0,
        "run: py streaming/sample_logs/generate.py",
    )
    if jsonl_files:
        lines = [l for l in jsonl_files[0].read_text().splitlines() if l.strip()]
        all_passed &= check("File has records", len(lines) > 0, f"{len(lines)} lines")
        try:
            json.loads(lines[0])
            all_passed &= check("Records are valid JSON", True)
        except Exception as e:
            all_passed &= check("Records are valid JSON", False, str(e))

    # Summary
    print(f"\n{'=' * 55}")
    if all_passed:
        print("  ALL CHECKS PASSED -- pipeline is ready")
        print("\n  Next steps:")
        print("    1. cd streaming && docker compose up -d")
        print("    2. py streaming/kafka/producer.py --continuous")
        print("    3. py streaming/spark/streaming_job.py")
        print("\n  Or test without Docker:")
        print("    py streaming/spark/streaming_job.py --local-test")
    else:
        print("  SOME CHECKS FAILED -- see above")
    print(f"{'=' * 55}\n")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
