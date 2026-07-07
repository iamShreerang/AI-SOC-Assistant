"""
Preprocessing pipeline for UNSW-NB15 dataset.
Handles encoding, scaling, and sequence creation for CNN-LSTM.
"""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler

# ── Feature configuration (derived from UNSW-NB15 schema) ──────────────────
# Drop: id, attack_cat, label (target), and timestamp-like cols not useful for inference
CATEGORICAL_COLS: list[str] = ["proto", "service", "state"]

NUMERIC_COLS: list[str] = [
    "dur", "spkts", "dpkts", "sbytes", "dbytes", "rate",
    "sttl", "dttl", "sload", "dload", "sloss", "dloss",
    "sinpkt", "dinpkt", "sjit", "djit", "swin", "stcpb", "dtcpb", "dwin",
    "tcprtt", "synack", "ackdat", "smean", "dmean",
    "trans_depth", "response_body_len",
    "ct_srv_src", "ct_state_ttl", "ct_dst_ltm", "ct_src_dport_ltm",
    "ct_dst_sport_ltm", "ct_dst_src_ltm", "is_ftp_login", "ct_ftp_cmd",
    "ct_flw_http_mthd", "ct_src_ltm", "ct_srv_dst", "is_sm_ips_ports",
]

# Final ordered feature columns fed to the model (categorical encoded → appended)
FEATURE_COLS: list[str] = NUMERIC_COLS + CATEGORICAL_COLS  # order matters

SEQUENCE_LENGTH: int = 10  # time-steps for CNN-LSTM


class PreprocessingPipeline:
    """Fit/transform pipeline: encodes categoricals, scales numerics."""

    def __init__(self) -> None:
        self.scaler = MinMaxScaler()
        self.label_encoders: dict[str, LabelEncoder] = {
            col: LabelEncoder() for col in CATEGORICAL_COLS
        }
        self.target_encoder = LabelEncoder()
        self.n_features: int = len(NUMERIC_COLS) + len(CATEGORICAL_COLS)
        self._fitted = False

    # ── Fit ────────────────────────────────────────────────────────────────
    def fit(self, df: pd.DataFrame) -> "PreprocessingPipeline":
        for col in CATEGORICAL_COLS:
            self.label_encoders[col].fit(df[col].astype(str).fillna("-"))
        self.scaler.fit(df[NUMERIC_COLS].fillna(0).astype(float))
        self.target_encoder.fit(df["label"].astype(int))
        self._fitted = True
        return self

    # ── Transform ──────────────────────────────────────────────────────────
    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Return float32 array of shape (n_samples, n_features)."""
        num = self.scaler.transform(df[NUMERIC_COLS].fillna(0).astype(float))
        cats = []
        for col in CATEGORICAL_COLS:
            le = self.label_encoders[col]
            vals = df[col].astype(str).fillna("-")
            # Handle unseen labels gracefully
            encoded = vals.map(
                lambda v, le=le: le.transform([v])[0]
                if v in le.classes_ else 0
            ).values.reshape(-1, 1).astype(float)
            cats.append(encoded)
        return np.hstack([num] + cats).astype(np.float32)

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        return self.fit(df).transform(df)

    # ── Sequence builder ───────────────────────────────────────────────────
    @staticmethod
    def make_sequences(
        X: np.ndarray, y: np.ndarray, seq_len: int = SEQUENCE_LENGTH
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Slide a window of seq_len over X/y."""
        xs, ys = [], []
        for i in range(len(X) - seq_len):
            xs.append(X[i : i + seq_len])
            ys.append(y[i + seq_len])
        return np.array(xs, dtype=np.float32), np.array(ys, dtype=np.int64)

    # ── Persistence ────────────────────────────────────────────────────────
    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        with open(path / "pipeline.pkl", "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: str | Path) -> "PreprocessingPipeline":
        with open(Path(path) / "pipeline.pkl", "rb") as f:
            return pickle.load(f)
