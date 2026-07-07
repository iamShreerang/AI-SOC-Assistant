"""BETH dataset loader.

Handles two cases:
  1. A single pre-merged beth.csv
  2. The BETH/ directory containing multiple labelled_*.csv files

Label column: 'sus' (0 = benign, 1 = suspicious/attack).
'evil' is dropped to prevent label leakage.
Text/identifier columns are dropped; numeric features are kept.
"""

from pathlib import Path

import pandas as pd

from ml.config import DATASET_MAX_ROWS, RANDOM_STATE
from ml.datasets.base import BaseDatasetLoader
from ml.utils.logger import get_logger

logger = get_logger(__name__)

_DROP_COLS = [
    "evil", "timestamp",
    "processName", "hostName", "eventName",
    "stackAddresses", "args",
]


class BETHLoader(BaseDatasetLoader):

    def get_label_column(self) -> str:
        return "label"

    def load(self, path: str) -> pd.DataFrame:
        p = Path(path)

        if p.is_dir():
            csv_files = [
                f for f in sorted(p.glob("labelled_*.csv"))
                if "dns" not in f.name
            ]
            if not csv_files:
                raise FileNotFoundError(f"No labelled_*.csv files found in {p}")
            logger.info("BETH: loading %d CSV files from %s", len(csv_files), p)
            frames = []
            for f in csv_files:
                try:
                    chunk = pd.read_csv(f, low_memory=False)
                    frames.append(chunk)
                    logger.info("  Loaded %s: %d rows", f.name, len(chunk))
                except Exception as exc:
                    logger.warning("  Skipping %s: %s", f.name, exc)
            df = pd.concat(frames, ignore_index=True)
        else:
            logger.info("BETH: loading single file %s", p)
            df = pd.read_csv(path, low_memory=False)

        if "sus" in df.columns:
            df = df.rename(columns={"sus": "label"})
        elif "sus_label" in df.columns:
            df = df.rename(columns={"sus_label": "label"})

        drop = [c for c in _DROP_COLS if c in df.columns]
        df = df.drop(columns=drop)
        df = df.replace([float("inf"), float("-inf")], pd.NA)
        df = df.dropna(subset=["label"])
        df["label"] = df["label"].astype(int)

        max_rows = DATASET_MAX_ROWS.get("beth")
        if max_rows and len(df) > max_rows:
            df = df.sample(n=max_rows, random_state=RANDOM_STATE).reset_index(drop=True)
            logger.info("BETH sampled to %d rows", len(df))

        logger.info("BETH loaded: %d rows, %d cols, label dist: %s",
                    len(df), df.shape[1], df["label"].value_counts().to_dict())
        return df
