"""Shared preprocessing pipeline for training and inference.

The pipeline is fitted once during training and persisted to disk.
At inference time it is loaded and applied to raw feature dicts / DataFrames
without re-fitting, guaranteeing identical transformations.
"""

import json
from pathlib import Path
from typing import List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder

from ml.config import MODEL_DIR, BENIGN_LABELS, RANDOM_STATE
from ml.utils.logger import get_logger

logger = get_logger(__name__)

_PIPELINE_FILE = "preprocessing_pipeline.joblib"
_FEATURES_FILE = "feature_columns.json"


class PreprocessingPipeline:
    """Fit-once, transform-many preprocessing for NIDS features.

    Responsibilities
    ----------------
    - Drop non-numeric / identifier columns
    - Align feature columns across heterogeneous datasets
    - Impute missing values (median)
    - Scale numeric features with StandardScaler
    - Encode string labels to integers with LabelEncoder
    - Expose transform() for inference (no re-fitting)
    """

    def __init__(self) -> None:
        self.scaler: StandardScaler = StandardScaler()
        self.label_encoder: LabelEncoder = LabelEncoder()
        self.feature_columns: List[str] = []
        self._fitted: bool = False
        self._medians: dict = {}

    # ── Fitting ───────────────────────────────────────────────────────────────

    def fit(self, df: pd.DataFrame, label_col: str = "label") -> "PreprocessingPipeline":
        """Fit scaler and label encoder on *df*. Stores feature column order."""
        logger.info("Fitting preprocessing pipeline on %d rows", len(df))

        X, y = self._split_xy(df, label_col)
        X = self._clean(X)

        self.feature_columns = list(X.columns)
        self._medians = X.median().to_dict()

        X_filled = X.fillna(self._medians)
        self.scaler.fit(X_filled.values.astype(np.float32))

        # Encode labels — convert to string first for consistency
        self.label_encoder.fit(y.astype(str).values)

        self._fitted = True
        logger.info("Pipeline fitted. Features: %d, Classes: %s",
                    len(self.feature_columns), list(self.label_encoder.classes_))
        return self

    # ── Transform ─────────────────────────────────────────────────────────────

    def transform(
        self,
        df: pd.DataFrame,
        label_col: Optional[str] = None,
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Transform *df* → (X_scaled, y_encoded | None).

        If *label_col* is provided and present in *df*, labels are also encoded.
        """
        if not self._fitted:
            raise RuntimeError("Pipeline is not fitted. Call fit() first.")

        if label_col and label_col in df.columns:
            X_raw, y_raw = self._split_xy(df, label_col)
            y = self.label_encoder.transform(y_raw.astype(str).values)
        else:
            X_raw = df.copy()
            y = None

        X = self._align_columns(X_raw)
        X = self._clean(X)
        X = X.fillna(self._medians)
        X_scaled = self.scaler.transform(X.values.astype(np.float32))
        return X_scaled, y

    def fit_transform(
        self,
        df: pd.DataFrame,
        label_col: str = "label",
    ) -> Tuple[np.ndarray, np.ndarray]:
        self.fit(df, label_col)
        X, y = self.transform(df, label_col)
        return X, y  # type: ignore[return-value]

    # ── Inference helper ──────────────────────────────────────────────────────

    def transform_single(self, features: dict) -> np.ndarray:
        """Transform a single feature dict → (1, n_features) array."""
        df = pd.DataFrame([features])
        X, _ = self.transform(df)
        return X

    def decode_label(self, encoded: int) -> str:
        return str(self.label_encoder.inverse_transform([encoded])[0])

    def is_attack(self, label: str) -> bool:
        return label not in BENIGN_LABELS

    @property
    def classes(self) -> List[str]:
        return list(self.label_encoder.classes_)

    @property
    def n_features(self) -> int:
        return len(self.feature_columns)

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, directory: Optional[Path] = None) -> None:
        directory = directory or MODEL_DIR
        directory.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, directory / _PIPELINE_FILE)
        with open(directory / _FEATURES_FILE, "w") as f:
            json.dump(self.feature_columns, f)
        logger.info("Pipeline saved to %s", directory)

    @classmethod
    def load(cls, directory: Optional[Path] = None) -> "PreprocessingPipeline":
        directory = directory or MODEL_DIR
        path = directory / _PIPELINE_FILE
        if not path.exists():
            raise FileNotFoundError(f"No pipeline found at {path}")
        pipeline = joblib.load(path)
        logger.info("Pipeline loaded from %s", path)
        return pipeline

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _split_xy(df: pd.DataFrame, label_col: str) -> Tuple[pd.DataFrame, pd.Series]:
        if label_col not in df.columns:
            raise ValueError(f"Label column '{label_col}' not found in DataFrame")
        return df.drop(columns=[label_col]), df[label_col]

    @staticmethod
    def _clean(X: pd.DataFrame) -> pd.DataFrame:
        """Drop non-numeric columns and replace inf values."""
        X = X.select_dtypes(include=[np.number])
        X = X.replace([np.inf, -np.inf], np.nan)
        return X

    def _align_columns(self, X: pd.DataFrame) -> pd.DataFrame:
        """Reindex to the fitted feature columns, filling missing with 0."""
        return X.reindex(columns=self.feature_columns, fill_value=0.0)
