"""
Mock log generator — produces realistic UNSW-NB15-style network flow records.
Writes JSON files to sample_logs/ and optionally streams to Kafka.

Usage:
    py streaming/sample_logs/generate.py            # write files only
    py streaming/sample_logs/generate.py --kafka    # also push to Kafka
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

PROTOS = ["tcp", "udp", "icmp", "arp"]
STATES = ["FIN", "CON", "RST", "INT", "REQ", "ACC", "CLO"]
SERVICES = ["-", "http", "ftp", "smtp", "ssh", "dns", "ssl", "pop3"]
ATTACK_CATS = ["Normal", "Generic", "Exploits", "Fuzzers", "DoS",
               "Reconnaissance", "Analysis", "Backdoor", "Shellcode", "Worms"]

_ATTACK_WEIGHT = [0.45, 0.20, 0.12, 0.07, 0.05, 0.04, 0.03, 0.02, 0.01, 0.01]


def _rand_ip() -> str:
    return f"{random.randint(1,254)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def generate_record() -> dict:
    attack_cat = random.choices(ATTACK_CATS, weights=_ATTACK_WEIGHT)[0]
    label = 0 if attack_cat == "Normal" else 1
    is_attack = label == 1

    if attack_cat == "Normal":
        severity = "info"
    elif attack_cat in ["Reconnaissance", "Analysis", "Generic"]:
        severity = "warning"
    elif attack_cat in ["Exploits", "Fuzzers", "DoS"]:
        severity = "error"
    else:
        severity = "critical"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": severity,
        "srcip": _rand_ip(),
        "dstip": _rand_ip(),
        "sport": random.randint(1024, 65535),
        "dsport": random.choice([22, 80, 443, 21, 53, 3306, 8080, 445, 3389]),
        "proto": random.choice(PROTOS),
        "service": random.choice(SERVICES),
        "state": random.choice(STATES),
        "dur": round(random.uniform(0.0, 10.0) * (5 if is_attack else 1), 6),
        "sbytes": random.randint(40, 50000 if is_attack else 5000),
        "dbytes": random.randint(0, 30000 if is_attack else 3000),
        "rate": round(random.uniform(0, 1000000 if is_attack else 10000), 2),
        "sttl": random.choice([64, 128, 255]),
        "dttl": random.choice([64, 128, 255, 0]),
        "sload": round(random.uniform(0, 1e7), 2),
        "dload": round(random.uniform(0, 1e7), 2),
        "sloss": random.randint(0, 10 if is_attack else 1),
        "dloss": random.randint(0, 10 if is_attack else 1),
        "spkts": random.randint(1, 500 if is_attack else 50),
        "dpkts": random.randint(0, 300 if is_attack else 30),
        "sinpkt": round(random.uniform(0, 1000), 4),
        "dinpkt": round(random.uniform(0, 1000), 4),
        "sjit": round(random.uniform(0, 500), 4),
        "djit": round(random.uniform(0, 500), 4),
        "swin": random.choice([0, 255, 1024, 8192, 65535]),
        "dwin": random.choice([0, 255, 1024, 8192, 65535]),
        "stcpb": random.randint(0, 2**31),
        "dtcpb": random.randint(0, 2**31),
        "tcprtt": round(random.uniform(0, 2), 6),
        "synack": round(random.uniform(0, 1), 6),
        "ackdat": round(random.uniform(0, 1), 6),
        "smean": random.randint(40, 1500),
        "dmean": random.randint(0, 1500),
        "trans_depth": random.randint(0, 5),
        "response_body_len": random.randint(0, 100000),
        "ct_srv_src": random.randint(1, 100),
        "ct_state_ttl": random.randint(0, 6),
        "ct_dst_ltm": random.randint(1, 100),
        "ct_src_dport_ltm": random.randint(1, 500 if is_attack else 10),
        "ct_dst_sport_ltm": random.randint(1, 100),
        "ct_dst_src_ltm": random.randint(1, 100),
        "is_ftp_login": random.randint(0, 1),
        "ct_ftp_cmd": random.randint(0, 5),
        "ct_flw_http_mthd": random.randint(0, 10),
        "ct_src_ltm": random.randint(1, 100),
        "ct_srv_dst": random.randint(1, 100),
        "is_sm_ips_ports": random.randint(0, 1),
        "attack_cat": attack_cat,
        "label": label,
    }


def write_batch(out_dir: Path, n: int = 100) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    out_file = out_dir / f"logs_{ts}.jsonl"
    with open(out_file, "w") as f:
        for _ in range(n):
            f.write(json.dumps(generate_record()) + "\n")
    return out_file


def stream_to_kafka(broker: str, topic: str, delay: float = 0.5) -> None:
    from kafka import KafkaProducer
    producer = KafkaProducer(
        bootstrap_servers=[broker],
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    print(f"Streaming to Kafka {broker} → {topic}  (delay={delay}s | Ctrl+C to stop)")
    try:
        while True:
            record = generate_record()
            producer.send(topic, record)
            print(f"  sent [{record['severity'].upper()}]: {record['srcip']} → {record['dstip']} | {record['attack_cat']}")
            time.sleep(delay)
    except KeyboardInterrupt:
        producer.flush()
        print("Stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--kafka", action="store_true", help="Stream to Kafka")
    parser.add_argument("--broker", default="localhost:9092")
    parser.add_argument("--topic", default="unsw-logs")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between records in seconds")
    parser.add_argument("--rate", type=float, default=None, help="Rate in records/sec (e.g. --rate 5)")
    parser.add_argument("--batch", type=int, default=200, help="Records per file batch")
    args = parser.parse_args()

    delay = args.delay
    if args.rate is not None and args.rate > 0:
        delay = 1.0 / args.rate

    out_dir = Path(__file__).parent
    out_file = write_batch(out_dir, args.batch)
    print(f"Written {args.batch} records to {out_file}")

    if args.kafka:
        stream_to_kafka(args.broker, args.topic, delay)
