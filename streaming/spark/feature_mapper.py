"""
Feature mapper — converts raw Kafka JSON records into the exact feature vector
expected by the trained CNN-LSTM model.

Reads feature config from the saved PreprocessingPipeline so feature names
and order are never hardcoded here.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from ml.preprocessing import FEATURE_COLS, PreprocessingPipeline

logger = logging.getLogger(__name__)

# Protocol / state / service maps for normalising raw log field names
# (backend log_generator uses different casing / field names)
_PROTO_ALIASES = {"TCP": "tcp", "UDP": "udp", "ICMP": "icmp", "ARP": "arp"}
_STATE_MAP = {
    "CON": "CON", "FIN": "FIN", "RST": "RST", "INT": "INT",
    "REQ": "REQ", "ACC": "ACC", "CLO": "CLO",
}


def _normalise_record(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Map heterogeneous raw log fields (from backend log_generator or mock generator)
    onto UNSW-NB15 feature names.  Missing fields default to 0 / '-'.
    """
    r: dict[str, Any] = {}

    # ── Numeric features ───────────────────────────────────────────────────
    r["dur"] = raw.get("dur", raw.get("Flow Duration", 0)) or 0
    r["spkts"] = raw.get("spkts", raw.get("Spkts", raw.get("Tot Fwd Pkts", 0))) or 0
    r["dpkts"] = raw.get("dpkts", raw.get("Dpkts", raw.get("Tot Bwd Pkts", 0))) or 0
    r["sbytes"] = raw.get("sbytes", raw.get("TotLen Fwd Pkts", 0)) or 0
    r["dbytes"] = raw.get("dbytes", raw.get("TotLen Bwd Pkts", 0)) or 0
    r["rate"] = raw.get("rate", raw.get("Flow Pkts/s", 0)) or 0
    r["sttl"] = raw.get("sttl", 64)
    r["dttl"] = raw.get("dttl", 64)
    r["sload"] = raw.get("sload", raw.get("Sload", raw.get("Flow Byts/s", 0))) or 0
    r["dload"] = raw.get("dload", raw.get("Dload", 0)) or 0
    r["sloss"] = raw.get("sloss", 0) or 0
    r["dloss"] = raw.get("dloss", 0) or 0
    r["sinpkt"] = raw.get("sinpkt", raw.get("Sintpkt", 0)) or 0
    r["dinpkt"] = raw.get("dinpkt", raw.get("Dintpkt", 0)) or 0
    r["sjit"] = raw.get("sjit", raw.get("Sjit", 0)) or 0
    r["djit"] = raw.get("djit", raw.get("Djit", 0)) or 0
    r["swin"] = raw.get("swin", 0) or 0
    r["dwin"] = raw.get("dwin", 0) or 0
    r["stcpb"] = raw.get("stcpb", 0) or 0
    r["dtcpb"] = raw.get("dtcpb", 0) or 0
    r["tcprtt"] = raw.get("tcprtt", 0) or 0
    r["synack"] = raw.get("synack", 0) or 0
    r["ackdat"] = raw.get("ackdat", 0) or 0
    r["smean"] = raw.get("smean", raw.get("smeansz", 0)) or 0
    r["dmean"] = raw.get("dmean", raw.get("dmeansz", 0)) or 0
    r["trans_depth"] = raw.get("trans_depth", 0) or 0
    r["response_body_len"] = raw.get("response_body_len", raw.get("res_bdy_len", 0)) or 0
    r["ct_srv_src"] = raw.get("ct_srv_src", 1) or 1
    r["ct_state_ttl"] = raw.get("ct_state_ttl", 0) or 0
    r["ct_dst_ltm"] = raw.get("ct_dst_ltm", 1) or 1
    r["ct_src_dport_ltm"] = raw.get("ct_src_dport_ltm", 1) or 1
    r["ct_dst_sport_ltm"] = raw.get("ct_dst_sport_ltm", 1) or 1
    r["ct_dst_src_ltm"] = raw.get("ct_dst_src_ltm", 1) or 1
    r["is_ftp_login"] = int(raw.get("is_ftp_login", 0) or 0)
    r["ct_ftp_cmd"] = raw.get("ct_ftp_cmd", 0) or 0
    r["ct_flw_http_mthd"] = raw.get("ct_flw_http_mthd", 0) or 0
    r["ct_src_ltm"] = raw.get("ct_src_ltm", 1) or 1
    r["ct_srv_dst"] = raw.get("ct_srv_dst", 1) or 1
    r["is_sm_ips_ports"] = int(raw.get("is_sm_ips_ports", 0) or 0)

    # ── Categorical features ───────────────────────────────────────────────
    proto_raw = str(raw.get("proto", raw.get("Protocol", "tcp")) or "tcp")
    r["proto"] = _PROTO_ALIASES.get(proto_raw.upper(), proto_raw.lower())

    service_raw = str(raw.get("service", "-") or "-")
    r["service"] = service_raw.lower() if service_raw else "-"

    state_raw = str(raw.get("state", "CON") or "CON")
    r["state"] = _STATE_MAP.get(state_raw.upper(), "CON")

    return r


class FeatureMapper:
    """Wraps PreprocessingPipeline.transform with raw-record normalisation."""

    def __init__(self, pipeline: PreprocessingPipeline) -> None:
        self.pipeline = pipeline

    def map_records(self, records: list[dict[str, Any]]) -> np.ndarray:
        """
        Args:
            records: list of raw log dicts (any source format)
        Returns:
            float32 array of shape (n_records, n_features)
        """
        normalised = [_normalise_record(r) for r in records]
        df = pd.DataFrame(normalised)
        # _normalise_record only populates the UNSW-style subset of the
        # unified FEATURE_COLS (BETH/CIC-only columns are left out) — zero
        # fill the rest, same convention ml/inference/predictor.py uses.
        for col in FEATURE_COLS:
            if col not in df.columns:
                df[col] = 0
        return self.pipeline.transform(df)
