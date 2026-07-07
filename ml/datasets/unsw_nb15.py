"""UNSW-NB15 dataset loader.

Handles two cases:
  1. A single pre-merged unsw_nb15.csv
  2. The UNSW-NB15/ directory — uses UNSW_NB15_training-set.csv and
     UNSW_NB15_testing-set.csv (preferred over the raw UNSW-NB15_1..4.csv
     which have no header row).

Label column: 'label' (0 = benign, 1 = attack). Binary.
'attack_cat' is dropped (used only for multiclass, not needed here).
"""

from pathlib import Path

import pandas as pd

from ml.datasets.base import BaseDatasetLoader
from ml.utils.logger import get_logger

logger = get_logger(__name__)

_DROP_COLS = [
    "id", "srcip", "dstip", "sport", "dsport",
    "attack_cat",
]


class UNSWNb15Loader(BaseDatasetLoader):

    def get_label_column(self) -> str:
        return "label"

    def load(self, path: str) -> pd.DataFrame:
        p = Path(path)

        if p.is_dir():
            # Prefer the pre-split training + testing sets (they have headers)
            train_f = p / "UNSW_NB15_training-set.csv"
            test_f  = p / "UNSW_NB15_testing-set.csv"
            frames = []
            for f in [train_f, test_f]:
                if f.exists():
                    try:
                        df = pd.read_csv(f, low_memory=False)
                        frames.append(df)
                        logger.info("  Loaded %s: %d rows", f.name, len(df))
                    except Exception as exc:
                        logger.warning("  Skipping %s: %s", f.name, exc)
            if not frames:
                raise FileNotFoundError(
                    f"No UNSW_NB15_training-set.csv or testing-set.csv found in {p}"
                )
            df = pd.concat(frames, ignore_index=True)
        else:
            logger.info("UNSW-NB15: loading single file %s", p)
            df = pd.read_csv(path, low_memory=False)

        # Normalise column names
        df.columns = df.columns.str.strip().str.lower()

        drop = [c for c in _DROP_COLS if c in df.columns]
        df = df.drop(columns=drop)

        # Drop remaining string columns (proto, service, state)
        str_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
        if "label" in str_cols:
            str_cols.remove("label")
        df = df.drop(columns=str_cols)

        df = df.replace([float("inf"), float("-inf")], pd.NA)
        df = df.dropna(subset=["label"])
        df["label"] = df["label"].astype(int)

        logger.info("UNSW-NB15 loaded: %d rows, %d cols, label dist: %s",
                    len(df), df.shape[1],
                    df["label"].value_counts().to_dict())
        return df
