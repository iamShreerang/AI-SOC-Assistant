"""
Rule-based threat detection layer, applied on top of the CNN-LSTM ML
predictions produced by streaming_job.py.

The ML model only outputs a binary label (attack / normal) + confidence —
it does not classify attack type. This module adds the SOC-analyst-style
rules that catch patterns a single-flow classifier can't see on its own:
repeated attacks from one source, abnormal request rates, oversized
transfers, and port-scan-shaped traffic. It operates on network-flow
fields (srcip/dstip/dsport/bytes) since that's the shape of the underlying
UNSW-NB15-style data — the nearest faithful analogue of HTTP-log rules
like "repeated failed logins" or "requests by endpoint" for this dataset.

Thread-safe: state is shared across `foreachBatch` calls in local[*] mode,
same pattern as streaming/spark/metrics.py.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Any

from streaming.config import (
    HIGH_RATE_THRESHOLD_PER_SEC,
    LARGE_TRANSFER_BYTES,
    PORT_SCAN_DISTINCT_PORTS,
    PORT_SCAN_WINDOW_SECS,
    REPEAT_ATTACK_THRESHOLD,
    REPEAT_ATTACK_WINDOW_SECS,
)

# Confidence bands -> alert severity for a single ML-flagged attack record.
_CONFIDENCE_SEVERITY = (
    (0.90, "critical"),
    (0.75, "high"),
    (0.0, "medium"),
)

# Minimum gap before the same (srcip, rule) pair can re-fire, to avoid
# flooding /ingest/alerts with duplicate alerts every micro-batch.
_RULE_COOLDOWN_SECS = 60.0


def _confidence_severity(confidence: float) -> str:
    for threshold, severity in _CONFIDENCE_SEVERITY:
        if confidence >= threshold:
            return severity
    return "low"


class ThreatRuleEngine:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        # srcip -> deque[timestamp] of ML-flagged attack events (repeat-attack rule)
        self._attack_events: dict[str, deque[float]] = defaultdict(deque)
        # srcip -> deque[timestamp] of all events (rate / DDoS rule)
        self._all_events: dict[str, deque[float]] = defaultdict(deque)
        # srcip -> deque[(timestamp, dsport)] (port-scan rule)
        self._port_events: dict[str, deque[tuple[float, int]]] = defaultdict(deque)
        # (srcip, rule_name) -> last time that rule fired for that srcip
        self._last_fired: dict[tuple[str, str], float] = {}

    def _on_cooldown(self, srcip: str, rule: str, now: float) -> bool:
        last = self._last_fired.get((srcip, rule))
        return last is not None and (now - last) < _RULE_COOLDOWN_SECS

    def _fire(self, srcip: str, rule: str, now: float) -> None:
        self._last_fired[(srcip, rule)] = now

    def evaluate(self, batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Args:
            batch: enriched prediction records — each must contain
                srcip, dstip, label, confidence, sbytes, dbytes, dsport.
        Returns:
            list of alert dicts: {title, severity, source, description, srcip}
            (srcip is metadata for the caller's metrics tracking; strip it
            before posting to /ingest/alerts, which doesn't accept it).
        """
        alerts: list[dict[str, Any]] = []
        now = time.time()

        with self._lock:
            for rec in batch:
                srcip = rec.get("srcip") or "unknown"
                dstip = rec.get("dstip") or "unknown"
                label = rec.get("label", 0)
                confidence = float(rec.get("confidence", 0.0))
                sbytes = int(rec.get("sbytes", 0) or 0)
                dbytes = int(rec.get("dbytes", 0) or 0)
                dsport = rec.get("dsport") or rec.get("dstport") or 0

                self._all_events[srcip].append(now)

                # ── Rule 1: ML-flagged attack ──────────────────────────────
                if label == 1:
                    self._attack_events[srcip].append(now)
                    severity = _confidence_severity(confidence)
                    alerts.append({
                        "title": f"Anomalous traffic detected from {srcip}",
                        "severity": severity,
                        "source": "spark-ml-detector",
                        "description": (
                            f"CNN-LSTM flagged flow {srcip} -> {dstip} as an attack "
                            f"(confidence={confidence:.2f})"
                        ),
                        "srcip": srcip,
                    })

                # ── Rule 2: large data transfer ─────────────────────────────
                total_bytes = sbytes + dbytes
                if total_bytes >= LARGE_TRANSFER_BYTES:
                    alerts.append({
                        "title": f"Large data transfer from {srcip}",
                        "severity": "high",
                        "source": "spark-threat-rules",
                        "description": (
                            f"Flow {srcip} -> {dstip} transferred {total_bytes} bytes "
                            f"(threshold={LARGE_TRANSFER_BYTES}) — possible exfiltration"
                        ),
                        "srcip": srcip,
                    })

                # ── Rule 3: port scan ────────────────────────────────────────
                if dsport:
                    ports = self._port_events[srcip]
                    ports.append((now, dsport))
                    while ports and now - ports[0][0] > PORT_SCAN_WINDOW_SECS:
                        ports.popleft()
                    distinct_ports = {p for _, p in ports}
                    if (
                        len(distinct_ports) >= PORT_SCAN_DISTINCT_PORTS
                        and not self._on_cooldown(srcip, "port_scan", now)
                    ):
                        self._fire(srcip, "port_scan", now)
                        alerts.append({
                            "title": f"Port scan pattern from {srcip}",
                            "severity": "medium",
                            "source": "spark-threat-rules",
                            "description": (
                                f"{srcip} touched {len(distinct_ports)} distinct destination "
                                f"ports within {PORT_SCAN_WINDOW_SECS}s — reconnaissance pattern"
                            ),
                            "srcip": srcip,
                        })

                # ── Rule 4: repeated attack escalation (brute-force-like) ───
                attacks = self._attack_events[srcip]
                while attacks and now - attacks[0] > REPEAT_ATTACK_WINDOW_SECS:
                    attacks.popleft()
                if (
                    len(attacks) >= REPEAT_ATTACK_THRESHOLD
                    and not self._on_cooldown(srcip, "repeat_attack", now)
                ):
                    self._fire(srcip, "repeat_attack", now)
                    alerts.append({
                        "title": f"Repeated attack pattern from {srcip}",
                        "severity": "critical",
                        "source": "spark-threat-rules",
                        "description": (
                            f"{srcip} triggered {len(attacks)} ML-flagged attacks within "
                            f"{REPEAT_ATTACK_WINDOW_SECS}s — brute-force-like pattern"
                        ),
                        "srcip": srcip,
                    })

                # ── Rule 5: high request rate (DDoS-like) ───────────────────
                events = self._all_events[srcip]
                while events and now - events[0] > 1.0:
                    events.popleft()
                if (
                    len(events) >= HIGH_RATE_THRESHOLD_PER_SEC
                    and not self._on_cooldown(srcip, "high_rate", now)
                ):
                    self._fire(srcip, "high_rate", now)
                    alerts.append({
                        "title": f"High request rate from {srcip}",
                        "severity": "critical",
                        "source": "spark-threat-rules",
                        "description": (
                            f"{srcip} generated {len(events)} requests/sec "
                            f"(threshold={HIGH_RATE_THRESHOLD_PER_SEC}) — potential DDoS indicator"
                        ),
                        "srcip": srcip,
                    })

        return alerts


# Module-level singleton, mirroring streaming/spark/metrics.py
threat_rules = ThreatRuleEngine()
