"""DSRL-APT-2023 dataset loader.

Label column: 'Activity' (string attack type names).
'Benign' -> 0, all other activities -> 1 for binary classification.

Drops identifier columns: Flow ID, Src IP, Dst IP, Src Port, Dst Port,
Timestamp, Activity, Stage.
"""

from pathlib import Path

import pandas as pd

from ml.datasets.base import BaseDatasetLoader
from ml.utils.logger import get_logger

logger = get_logger(__name__)

_DROP_COLS = [
    "Flow ID", "Src IP", "Dst IP", "Src Port", "Dst Port",
    "Timestamp", "Stage",
]

_BENIGN_LABEL = "Benign"


class DSRLApi2023Loader(BaseDatasetLoader):

    def get_label_column(self) -> str:
        return "label"

    def load(self, path: str) -> pd.DataFrame:
        p = Path(path)
        if p.is_dir():
            csv_files = sorted(p.glob("*.csv"))
            if not csv_files:
                raise FileNotFoundError(f"No CSV files found in {p}")
            frames = [pd.read_csv(f, low_memory=False) for f in csv_files]
            df = pd.concat(frames, ignore_index=True)
        else:
            logger.info("DSRL-APT-2023: loading %s", p)
            df = pd.read_csv(path, low_memory=False)

        # Normalise column names
        df.columns = df.columns.str.strip()

        # Build binary label from Activity column
        if "Activity" in df.columns:
            df["label"] = df["Activity"].astype(str).str.strip().apply(
                lambda x: 0 if x == _BENIGN_LABEL else 1
            )
            drop = [c for c in _DROP_COLS + ["Activity"] if c in df.columns]
        elif "label" in df.columns:
            drop = [c for c in _DROP_COLS if c in df.columns]
        else:
            raise ValueError("DSRL-APT-2023: no 'Activity' or 'label' column found")

        df = df.drop(columns=drop)
        df = df.replace([float("inf"), float("-inf")], pd.NA)
        df = df.dropna(subset=["label"])
        df["label"] = df["label"].astype(int)

        logger.info("DSRL-APT-2023 loaded: %d rows, %d cols, label dist: %s",
                    len(df), df.shape[1],
                    df["label"].value_counts().to_dict())
        return df
