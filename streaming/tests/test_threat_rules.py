"""
Unit tests for streaming/spark/threat_rules.py.
Pure Python — no Docker, Kafka, or Spark required.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from streaming.spark.threat_rules import ThreatRuleEngine


def _record(srcip="1.1.1.1", dstip="2.2.2.2", label=0, confidence=0.6,
            sbytes=100, dbytes=50, dsport=80):
    return {
        "srcip": srcip, "dstip": dstip, "label": label, "confidence": confidence,
        "sbytes": sbytes, "dbytes": dbytes, "dsport": dsport,
    }


def test_single_ml_attack_generates_base_alert():
    engine = ThreatRuleEngine()
    alerts = engine.evaluate([_record(label=1, confidence=0.6)])
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "medium"
    assert alerts[0]["srcip"] == "1.1.1.1"


def test_high_confidence_attack_is_critical():
    engine = ThreatRuleEngine()
    alerts = engine.evaluate([_record(label=1, confidence=0.95)])
    assert alerts[0]["severity"] == "critical"


def test_normal_record_generates_no_ml_alert():
    engine = ThreatRuleEngine()
    alerts = engine.evaluate([_record(label=0, confidence=0.1)])
    assert alerts == []


def test_large_transfer_triggers_alert_regardless_of_label():
    engine = ThreatRuleEngine()
    alerts = engine.evaluate([_record(label=0, sbytes=2_000_000, dbytes=0)])
    titles = [a["title"] for a in alerts]
    assert any("Large data transfer" in t for t in titles)


def test_repeated_attacks_from_same_ip_escalate():
    engine = ThreatRuleEngine()
    # Threshold default is 3 within 60s
    batch = [_record(label=1, confidence=0.6) for _ in range(3)]
    alerts = engine.evaluate(batch)
    titles = [a["title"] for a in alerts]
    assert any("Repeated attack pattern" in t for t in titles)


def test_port_scan_detected_across_distinct_ports():
    engine = ThreatRuleEngine()
    batch = [_record(label=0, confidence=0.1, dsport=p) for p in range(1, 8)]
    alerts = engine.evaluate(batch)
    titles = [a["title"] for a in alerts]
    assert any("Port scan pattern" in t for t in titles)


def test_high_request_rate_triggers_ddos_alert():
    engine = ThreatRuleEngine()
    # Default threshold is 20 events/sec from a single srcip
    batch = [_record(label=0, confidence=0.1, dsport=443) for _ in range(25)]
    alerts = engine.evaluate(batch)
    titles = [a["title"] for a in alerts]
    assert any("High request rate" in t for t in titles)


def test_cooldown_prevents_duplicate_repeat_alert_within_window():
    engine = ThreatRuleEngine()
    batch = [_record(label=1, confidence=0.6) for _ in range(3)]
    first = engine.evaluate(batch)
    second = engine.evaluate([_record(label=1, confidence=0.6)])
    first_titles = [a["title"] for a in first]
    second_titles = [a["title"] for a in second]
    assert any("Repeated attack pattern" in t for t in first_titles)
    assert not any("Repeated attack pattern" in t for t in second_titles)


if __name__ == "__main__":
    import inspect
    failures = 0
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_") and inspect.isfunction(obj)]
    for t in tests:
        try:
            t()
            print(f"[PASS] {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"[FAIL] {t.__name__}: {e}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    sys.exit(1 if failures else 0)
