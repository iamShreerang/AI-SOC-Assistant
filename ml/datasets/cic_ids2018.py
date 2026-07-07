"""CSE-CIC-IDS2018 dataset loader.

Handles two cases:
  1. A single pre-merged cic_ids2018.csv
  2. The CSE-CIC-IDS2018/ directory containing multiple .parquet files

Label column: 'Label' (string attack names).
'Benign' -> 0, everything else -> 1 for binary classification.
"""

from pathlib import Path

import pandas as pd

from ml.config import DATASET_MAX_ROWS, RANDOM_STATE
from ml.datasets.base import BaseDatasetLoader
from ml.utils.logger import get_logger

logger = get_logger(__name__)

_DROP_COLS = ["Timestamp", "Dst Port", "Src Port"]
_BENIGN_LABEL = "Benign"


class CICIds2018Loader(BaseDatasetLoader):

    def get_label_column(self) -> str:
        return "label"

    def load(self, path: str) -> pd.DataFrame:
        p = Path(path)

        if p.is_dir():
            parquet_files = sorted(p.glob("*.parquet"))
            if not parquet_files:
                raise FileNotFoundError(f"No .parquet files found in {p}")
            logger.info("CIC-IDS2018: loading %d parquet files from %s", len(parquet_files), p)
            frames = []
            for f in parquet_files:
                try:
                    chunk = pd.read_parquet(f)
                    frames.append(chunk)
                    logger.info("  Loaded %s: %d rows", f.name, len(chunk))
                except Exception as exc:
                    logger.warning("  Skipping %s: %s", f.name, exc)
            df = pd.concat(frames, ignore_index=True)
        else:
            logger.info("CIC-IDS2018: loading single file %s", p)
            df = pd.read_csv(path, low_memory=False)

        df.columns = df.columns.str.strip()
        drop = [c for c in _DROP_COLS if c in df.columns]
        df = df.drop(columns=drop)

        if "Label" in df.columns:
            df["label"] = df["Label"].astype(str).str.strip().apply(
                lambda x: 0 if x == _BENIGN_LABEL else 1
            )
            df = df.drop(columns=["Label"])

        df = df.replace([float("inf"), float("-inf")], pd.NA)
        df = df.dropna(subset=["label"])
        df["label"] = df["label"].astype(int)

        max_rows = DATASET_MAX_ROWS.get("cic_ids2018")
        if max_rows and len(df) > max_rows:
            df = df.sample(n=max_rows, random_state=RANDOM_STATE).reset_index(drop=True)
            logger.info("CIC-IDS2018 sampled to %d rows", len(df))

        logger.info("CIC-IDS2018 loaded: %d rows, %d cols, label dist: %s",
                    len(df), df.shape[1], df["label"].value_counts().to_dict())
        return df
