"""
Preprocessing pipeline for multi-dataset training.
Supports: UNSW-NB15, DSRL-APT-2023, BETH, CSE-CIC-IDS2018.
All datasets are mapped to a unified numeric feature set before scaling.
"""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# ── Feature set the currently-saved model (ml/saved_models/) was fit on ────
# Must match ml/saved_models/pipeline.pkl's scaler.feature_names_in_ exactly —
# retrain (py ml/scripts/train.py) and re-save before changing this list.
FEATURE_COLS: list[str] = [
    "dur", "spkts", "dpkts", "sbytes", "dbytes", "rate",
    "sttl", "dttl", "sload", "dload", "sloss", "dloss",
    "sinpkt", "dinpkt", "sjit", "djit", "swin", "stcpb", "dtcpb", "dwin",
    "tcprtt", "synack", "ackdat", "smean", "dmean",
    "trans_depth", "response_body_len",
    "ct_srv_src", "ct_state_ttl", "ct_dst_ltm", "ct_src_dport_ltm",
    "ct_dst_sport_ltm", "ct_dst_src_ltm", "is_ftp_login", "ct_ftp_cmd",
    "ct_flw_http_mthd", "ct_src_ltm", "ct_srv_dst", "is_sm_ips_ports",
]

SEQUENCE_LENGTH: int = 10


# ── Per-dataset loaders ────────────────────────────────────────────────────

def load_unsw(data_dir: Path) -> pd.DataFrame:
    train = pd.read_csv(data_dir / "UNSW-NB15" / "UNSW_NB15_training-set.csv")
    test = pd.read_csv(data_dir / "UNSW-NB15" / "UNSW_NB15_testing-set.csv")
    df = pd.concat([train, test], ignore_index=True)
    out = pd.DataFrame(0.0, index=df.index, columns=FEATURE_COLS)
    for col in ["dur","spkts","dpkts","sbytes","dbytes","rate","sttl","dttl",
                "sload","dload","sloss","dloss","sinpkt","dinpkt","sjit","djit",
                "smean","dmean","tcprtt","synack"]:
        if col in df.columns:
            out[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    out["label"] = df["label"].astype(int).values
    return out


def load_dsrl(data_dir: Path) -> pd.DataFrame:
    df = pd.read_csv(data_dir / "DSRL-APT-2023" / "DSRL-APT-2023.csv")
    out = pd.DataFrame(0.0, index=df.index, columns=FEATURE_COLS)
    for col in ["dur","spkts","dpkts","sbytes","dbytes","rate","sttl","dttl",
                "sload","dload","sloss","dloss","sinpkt","dinpkt","sjit","djit",
                "smean","dmean","tcprtt","synack"]:
        if col in df.columns:
            out[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    # DSRL-APT-2023 has no 'label' column — it uses an 'Activity' column
    # ("Benign" vs named attack stages, e.g. "Account Bruteforce", "SQL Injection").
    out["label"] = (df["Activity"].astype(str).str.strip().str.lower() != "benign").astype(int).values
    return out


def load_beth(data_dir: Path) -> pd.DataFrame:
    frames = []
    for f in (data_dir / "BETH").glob("labelled_*.csv"):
        frames.append(pd.read_csv(f, low_memory=False))
    df = pd.concat(frames, ignore_index=True)
    out = pd.DataFrame(0.0, index=df.index, columns=FEATURE_COLS)
    for col in ["processId","threadId","parentProcessId","userId",
                "eventId","argsNum","returnValue"]:
        if col in df.columns:
            out[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    # evil=1 → attack, sus alone is not definitive
    out["label"] = (df["evil"].fillna(0).astype(int) > 0).astype(int).values
    return out


def load_cic(data_dir: Path) -> pd.DataFrame:
    import pyarrow.parquet as pq
    frames = []
    for f in (data_dir / "CSE-CIC-IDS2018").glob("*.parquet"):
        frames.append(pq.read_table(f).to_pandas())
    df = pd.concat(frames, ignore_index=True)
    col_map = {
        "Flow Duration": "flow_duration",
        "Total Fwd Packets": "total_fwd_pkts",
        "Total Backward Packets": "total_bwd_pkts",
        "Fwd Packet Length Mean": "fwd_pkt_len_mean",
        "Bwd Packet Length Mean": "bwd_pkt_len_mean",
        "Flow Bytes/s": "flow_bytes_s",
        "Flow Packets/s": "flow_pkts_s",
        "Packet Length Mean": "pkt_len_mean",
        "Packet Length Std": "pkt_len_std",
        "FIN Flag Count": "fin_flag",
        "SYN Flag Count": "syn_flag",
        "RST Flag Count": "rst_flag",
        "PSH Flag Count": "psh_flag",
        "ACK Flag Count": "ack_flag",
    }
    out = pd.DataFrame(0.0, index=df.index, columns=FEATURE_COLS)
    for src, dst in col_map.items():
        if src in df.columns:
            out[dst] = pd.to_numeric(df[src], errors="coerce").fillna(0)
    out["label"] = (df["Label"].astype(str).str.strip().str.lower() != "benign").astype(int).values
    return out


def load_all_datasets(data_dir: Path) -> pd.DataFrame:
    loaders = [load_unsw, load_dsrl, load_beth, load_cic]
    frames = []
    for loader in loaders:
        try:
            df = loader(data_dir)
            frames.append(df)
            print(f"  Loaded {loader.__name__}: {len(df):,} rows | attack={df['label'].mean()*100:.1f}%")
        except Exception as e:
            print(f"  WARNING: {loader.__name__} failed — {e}")
    combined = pd.concat(frames, ignore_index=True)
    print(f"  Combined: {len(combined):,} rows | attack={combined['label'].mean()*100:.1f}%")
    return combined


# ── Pipeline ───────────────────────────────────────────────────────────────

class PreprocessingPipeline:
    """Fit/transform pipeline: scales unified numeric features."""

    def __init__(self) -> None:
        self.scaler = MinMaxScaler()
        self.n_features: int = len(FEATURE_COLS)
        self._fitted = False

    def fit(self, df: pd.DataFrame) -> "PreprocessingPipeline":
        self.scaler.fit(df[FEATURE_COLS].fillna(0).astype(float))
        self._fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        X = df[FEATURE_COLS].fillna(0).astype(float)
        return self.scaler.transform(X).astype(np.float32)

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        return self.fit(df).transform(df)

    @staticmethod
    def make_sequences(
        X: np.ndarray, y: np.ndarray, seq_len: int = SEQUENCE_LENGTH
    ) -> Tuple[np.ndarray, np.ndarray]:
        xs, ys = [], []
        for i in range(len(X) - seq_len):
            xs.append(X[i : i + seq_len])
            ys.append(y[i + seq_len])
        return np.array(xs, dtype=np.float32), np.array(ys, dtype=np.int64)

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        with open(path / "pipeline.pkl", "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: str | Path) -> "PreprocessingPipeline":
        with open(Path(path) / "pipeline.pkl", "rb") as f:
            return pickle.load(f)
