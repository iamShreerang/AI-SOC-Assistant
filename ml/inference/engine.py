"""InferenceEngine — unified inference interface.

Accepts Python dicts, Pandas DataFrames, and NumPy arrays.
Returns structured PredictionOutput objects.

External services import this class:
    from ml.inference import InferenceEngine
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import torch

from ml.config import ARTIFACT_DIR, MODEL_VERSION, SEQUENCE_LENGTH
from ml.artifacts.manager import ArtifactManager
from ml.model.architecture import build_cnn_lstm
from ml.preprocessing.pipeline import PreprocessingPipeline
from ml.preprocessing.sequences import create_inference_sequence
from ml.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PredictionOutput:
    """Structured prediction result returned by InferenceEngine."""
    prediction: str
    confidence: float
    is_attack: bool
    probabilities: Dict[str, float]
    model_version: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class InferenceEngine:
    """Load-once, predict-many engine supporting multiple input formats."""

    def __init__(self) -> None:
        self._model = None
        self._pipeline: Optional[PreprocessingPipeline] = None
        self._metadata: dict = {}
        self._loaded: bool = False
        self._sequence_length: int = SEQUENCE_LENGTH
        self._model_version: str = MODEL_VERSION
        self._device = torch.device("cpu")

    @classmethod
    def load(
        cls,
        version: str = MODEL_VERSION,
        artifact_dir: Path = ARTIFACT_DIR,
    ) -> "InferenceEngine":
        """Load model and pipeline from artifact directory."""
        engine = cls()
        engine._model_version = version
        am = ArtifactManager(version=version, base_dir=artifact_dir)

        engine._pipeline = am.load_pipeline()
        engine._metadata = am.load_metadata()
        engine._sequence_length = engine._metadata.get("sequence_length", SEQUENCE_LENGTH)

        meta = engine._metadata
        model = build_cnn_lstm(
            sequence_length=engine._sequence_length,
            n_features=meta.get("n_features", engine._pipeline.n_features),
            n_classes=len(meta.get("classes", engine._pipeline.classes)),
        )
        engine._model = am.load_model(model_arch=model, best=True)
        engine._model.eval()
        engine._loaded = True

        logger.info(
            "InferenceEngine loaded — version=%s, features=%d, classes=%s",
            version, engine._pipeline.n_features, engine._pipeline.classes,
        )
        return engine

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def classes(self) -> List[str]:
        return self._pipeline.classes if self._pipeline else []

    def predict_dict(self, features: Dict) -> PredictionOutput:
        self._check_loaded()
        X = self._pipeline.transform_single(features)
        X_seq = create_inference_sequence(X, self._sequence_length)
        return self._infer(X_seq)[0]

    def predict_dataframe(self, df: pd.DataFrame) -> List[PredictionOutput]:
        self._check_loaded()
        X, _ = self._pipeline.transform(df)
        results = []
        for i in range(len(X)):
            row = X[i].reshape(1, -1)
            X_seq = create_inference_sequence(row, self._sequence_length)
            results.extend(self._infer(X_seq))
        return results

    def predict_array(self, X: np.ndarray) -> List[PredictionOutput]:
        """Predict from a raw (n_samples, n_features) ndarray (not yet scaled)."""
        self._check_loaded()
        if X.ndim == 1:
            X = X.reshape(1, -1)
        X_scaled = self._pipeline.scaler.transform(X.astype(np.float32))
        results = []
        for i in range(len(X_scaled)):
            row = X_scaled[i].reshape(1, -1)
            X_seq = create_inference_sequence(row, self._sequence_length)
            results.extend(self._infer(X_seq))
        return results

    def predict_sequence(self, X_seq: np.ndarray) -> List[PredictionOutput]:
        """Predict directly on a pre-built (n, seq_len, n_features) array."""
        self._check_loaded()
        return self._infer(X_seq)

    def _infer(self, X_seq: np.ndarray) -> List[PredictionOutput]:
        self._model.eval()
        with torch.no_grad():
            tensor = torch.tensor(X_seq, dtype=torch.float32).to(self._device)
            raw = self._model(tensor).cpu().numpy()

        classes = self._pipeline.classes
        binary = len(classes) == 2
        outputs = []

        for i in range(len(X_seq)):
            scores = raw[i]
            if binary:
                prob_attack = float(1 / (1 + np.exp(-scores.squeeze())))
                is_atk = prob_attack >= 0.5
                label = "attack" if is_atk else "benign"
                confidence = prob_attack if is_atk else 1.0 - prob_attack
                probs = {"benign": round(1.0 - prob_attack, 4), "attack": round(prob_attack, 4)}
            else:
                exp = np.exp(scores - scores.max())
                softmax = exp / exp.sum()
                idx = int(np.argmax(softmax))
                label = self._pipeline.decode_label(idx)
                confidence = float(softmax[idx])
                is_atk = self._pipeline.is_attack(label)
                probs = {cls: round(float(softmax[j]), 4) for j, cls in enumerate(classes)}

            outputs.append(PredictionOutput(
                prediction=label,
                confidence=round(confidence, 4),
                is_attack=is_atk,
                probabilities=probs,
                model_version=self._model_version,
            ))
        return outputs

    def _check_loaded(self) -> None:
        if not self._loaded:
            raise RuntimeError("InferenceEngine not loaded. Call InferenceEngine.load() first.")
