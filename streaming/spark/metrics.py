"""
Streaming metrics — maintained in-process across micro-batches.
Thread-safe counters updated by the Spark foreachBatch sink.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StreamingMetrics:
    total_requests: int = 0
    attack_count: int = 0
    normal_count: int = 0
    total_bytes: int = 0
    total_latency_ms: float = 0.0
    inference_count: int = 0
    unique_src_ips: set = field(default_factory=set)
    unique_dst_ips: set = field(default_factory=set)
    severity_counts: dict = field(default_factory=lambda: {"low": 0, "medium": 0, "high": 0, "critical": 0})
    _ip_alert_counts: dict = field(default_factory=dict, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _window_start: float = field(default_factory=time.time, repr=False)
    _window_requests: int = 0

    def update(self, batch: list[dict[str, Any]]) -> None:
        with self._lock:
            now = time.time()
            for rec in batch:
                self.total_requests += 1
                self._window_requests += 1
                label = rec.get("label", 0)
                if label == 1:
                    self.attack_count += 1
                else:
                    self.normal_count += 1
                self.total_bytes += int(rec.get("sbytes", 0)) + int(rec.get("dbytes", 0))
                self.total_latency_ms += float(rec.get("latency_ms", 0))
                self.inference_count += 1
                if rec.get("srcip"):
                    self.unique_src_ips.add(rec["srcip"])
                if rec.get("dstip"):
                    self.unique_dst_ips.add(rec["dstip"])

    def record_alerts(self, alerts: list[dict[str, Any]]) -> None:
        """Feed threat_rules.evaluate() output in so alert-derived stats surface in snapshot()."""
        with self._lock:
            for alert in alerts:
                severity = alert.get("severity", "low")
                if severity in self.severity_counts:
                    self.severity_counts[severity] += 1
                srcip = alert.get("srcip")
                if srcip:
                    self._ip_alert_counts[srcip] = self._ip_alert_counts.get(srcip, 0) + 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            now = time.time()
            elapsed = max(now - self._window_start, 1e-6)
            rps = self._window_requests / elapsed
            # Reset window
            self._window_start = now
            self._window_requests = 0

            avg_latency = (
                self.total_latency_ms / self.inference_count
                if self.inference_count > 0 else 0.0
            )
            avg_bytes = (
                self.total_bytes / self.total_requests
                if self.total_requests > 0 else 0.0
            )
            suspicious_ip_count = sum(1 for c in self._ip_alert_counts.values() if c >= 2)
            return {
                "total_requests": self.total_requests,
                "requests_per_second": round(rps, 2),
                "requests_per_minute": round(rps * 60, 2),
                "attack_count": self.attack_count,
                "normal_count": self.normal_count,
                "total_bytes_transferred": self.total_bytes,
                "avg_packet_size": round(avg_bytes, 2),
                "unique_src_ips": len(self.unique_src_ips),
                "unique_dst_ips": len(self.unique_dst_ips),
                "suspicious_ip_count": suspicious_ip_count,
                "avg_inference_latency_ms": round(avg_latency, 2),
                "alerts_low": self.severity_counts["low"],
                "alerts_medium": self.severity_counts["medium"],
                "alerts_high": self.severity_counts["high"],
                "alerts_critical": self.severity_counts["critical"],
            }


# Module-level singleton
metrics = StreamingMetrics()
