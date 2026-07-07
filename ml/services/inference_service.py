"""Inference service — stable interface for FastAPI prediction endpoints.

TODO (external/fastapi): Import InferenceService in the /predict and
/predict/batch route handlers.

    from ml.services.inference_service import InferenceService
    _svc = InferenceService()
    result = _svc.predict(features_dict)
    results = _svc.predict_batch(list_of_dicts)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from ml.config import ARTIFACT_DIR, MODEL_VERSION
from ml.inference.engine import InferenceEngine, PredictionOutput
from ml.inference.adapters import JSONAdapter
from ml.utils.logger import get_logger

logger = get_logger(__name__)

# Module-level singleton — loaded once on first use
_engine: Optional[InferenceEngine] = None


def _get_engine(version: str = MODEL_VERSION, artifact_dir: Path = ARTIFACT_DIR) -> InferenceEngine:
    global _engine
    if _engine is None or _engine.model_version != version:
        logger.info("Loading InferenceEngine version=%s", version)
        _engine = InferenceEngine.load(version=version, artifact_dir=artifact_dir)
    return _engine


class InferenceService:
    """Coordinates inference for FastAPI routes.

    Manages a singleton InferenceEngine and exposes clean predict methods.
    """

    def __init__(
        self,
        version: str = MODEL_VERSION,
        artifact_dir: Path = ARTIFACT_DIR,
    ) -> None:
        self.version = version
        self.artifact_dir = artifact_dir
        self._adapter: Optional[JSONAdapter] = None

    def _get_adapter(self) -> JSONAdapter:
        if self._adapter is None:
            engine = _get_engine(self.version, self.artifact_dir)
            self._adapter = JSONAdapter(engine)
        return self._adapter

    def predict(self, features: Dict[str, Any]) -> Optional[PredictionOutput]:
        """Predict on a single feature dict."""
        return self._get_adapter().predict_from_json({"features": features})

    def predict_batch(self, samples: List[Dict[str, Any]]) -> List[Optional[PredictionOutput]]:
        """Predict on a list of feature dicts."""
        return self._get_adapter().predict_from_json_batch({"samples": samples})

    def model_status(self) -> Dict:
        """Return current model status for /model/status endpoint."""
        try:
            engine = _get_engine(self.version, self.artifact_dir)
            return {
                "loaded": engine.is_loaded,
                "model_version": engine.model_version,
                "classes": engine.classes,
            }
        except Exception as exc:
            return {"loaded": False, "error": str(exc)}
