"""Inference predictor — loads saved artifacts and runs predictions.

Single integration point for external services:
  - FastAPI routes call predict_single() / predict_batch()
  - Spark streaming job calls predict_batch()
  - Kafka consumer calls predict_single()
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import torch

from ml.config import ARTIFACT_DIR, MODEL_VERSION, SEQUENCE_LENGTH, BENIGN_LABELS
from ml.artifacts.manager import ArtifactManager
from ml.model.architecture import build_cnn_lstm
from ml.preprocessing.pipeline import PreprocessingPipeline
from ml.preprocessing.sequences import create_inference_sequence
from ml.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PredictionResult:
    attack_type: str
    confidence: float
    is_attack: bool
    model_version: str
    raw_scores: List[float] = field(default_factory=list)


class Predictor:
    """Load-once, predict-many inference engine.

    Usage
    -----
    predictor = Predictor.load()
    result = predictor.predict_single({"feature_a": 1.2, ...})
    results = predictor.predict_batch([{...}, {...}])
    """

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
    ) -> "Predictor":
        """Load model + pipeline from artifact directory."""
        predictor = cls()
        predictor._model_version = version
        am = ArtifactManager(version=version, base_dir=artifact_dir)

        predictor._pipeline = am.load_pipeline()
        predictor._metadata = am.load_metadata()
        predictor._sequence_length = predictor._metadata.get("sequence_length", SEQUENCE_LENGTH)

        # Rebuild architecture from metadata and load weights
        meta = predictor._metadata
        model = build_cnn_lstm(
            sequence_length=predictor._sequence_length,
            n_features=meta.get("n_features", predictor._pipeline.n_features),
            n_classes=len(meta.get("classes", predictor._pipeline.classes)),
        )
        predictor._model = am.load_model(model_arch=model, best=True)
        predictor._model.eval()
        predictor._loaded = True

        logger.info(
            "Predictor loaded — version=%s, features=%d, classes=%s",
            version, predictor._pipeline.n_features, predictor._pipeline.classes,
        )
        return predictor

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def classes(self) -> List[str]:
        return self._pipeline.classes if self._pipeline else []

    @property
    def metadata(self) -> dict:
        return self._metadata

    def predict_single(self, features: Dict) -> PredictionResult:
        self._check_loaded()
        X = self._pipeline.transform_single(features)
        X_seq = create_inference_sequence(X, self._sequence_length)
        return self._run_inference(X_seq)[0]

    def predict_batch(self, samples: List[Dict]) -> List[PredictionResult]:
        self._check_loaded()
        return [self.predict_single(s) for s in samples]

    def predict_array(self, X_seq: np.ndarray) -> List[PredictionResult]:
        """Predict directly on a pre-built (n, seq_len, n_features) array."""
        self._check_loaded()
        return self._run_inference(X_seq)

    def _run_inference(self, X_seq: np.ndarray) -> List[PredictionResult]:
        self._model.eval()
        with torch.no_grad():
            tensor = torch.tensor(X_seq, dtype=torch.float32).to(self._device)
            raw = self._model(tensor).cpu().numpy()

        classes = self._pipeline.classes
        binary = len(classes) == 2
        results = []

        for i in range(len(X_seq)):
            scores = raw[i]
            if binary:
                prob_attack = float(1 / (1 + np.exp(-scores.squeeze())))
                is_atk = prob_attack >= 0.5
                attack_type = "attack" if is_atk else "benign"
                confidence = prob_attack if is_atk else 1.0 - prob_attack
                raw_scores = [round(1.0 - prob_attack, 4), round(prob_attack, 4)]
            else:
                exp = np.exp(scores - scores.max())
                probs = exp / exp.sum()
                idx = int(np.argmax(probs))
                attack_type = self._pipeline.decode_label(idx)
                confidence = float(probs[idx])
                is_atk = self._pipeline.is_attack(attack_type)
                raw_scores = [round(float(p), 4) for p in probs]

            results.append(PredictionResult(
                attack_type=attack_type,
                confidence=round(confidence, 4),
                is_attack=is_atk,
                model_version=self._model_version,
                raw_scores=raw_scores,
            ))
        return results

    def _check_loaded(self) -> None:
        if not self._loaded:
            raise RuntimeError("Predictor is not loaded. Call Predictor.load() first.")
