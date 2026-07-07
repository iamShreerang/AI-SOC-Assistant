"""Artifact manager — versioned saving and loading of all ML artifacts.

Artifacts are stored under:
    ml/artifacts/<version>/
        model_best.pt
        model_final.pt
        preprocessing_pipeline.joblib
        scaler.joblib
        label_encoder.joblib
        feature_columns.json
        metadata.json
        training_history.json
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import joblib

from ml.config import (
    ARTIFACT_DIR, MODEL_VERSION,
    PIPELINE_FILENAME, SCALER_FILENAME, ENCODER_FILENAME,
    FEATURES_FILENAME, METADATA_FILENAME, HISTORY_FILENAME,
)
from ml.utils.logger import get_logger

logger = get_logger(__name__)


class ArtifactManager:
    """Save and load all ML artifacts for a given model version."""

    def __init__(self, version: str = MODEL_VERSION, base_dir: Path = ARTIFACT_DIR) -> None:
        self.version = version
        self.artifact_dir = base_dir / version
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        logger.info("ArtifactManager initialised at %s", self.artifact_dir)

    # ── Saving ────────────────────────────────────────────────────────────────

    def save_model(self, model, best: bool = False) -> Path:
        import torch
        name = "model_best.pt" if best else "model_final.pt"
        path = self.artifact_dir / name
        torch.save(model.state_dict(), str(path))
        logger.info("Model state_dict saved → %s", path)
        return path

    def save_model_full(self, model) -> Path:
        """Save the full model object (architecture + weights) for portability."""
        import torch
        path = self.artifact_dir / "model_full.pt"
        torch.save(model, str(path))
        logger.info("Full model saved → %s", path)
        return path

    def save_pipeline(self, pipeline) -> Path:
        path = self.artifact_dir / PIPELINE_FILENAME
        joblib.dump(pipeline, path)
        logger.info("Pipeline saved → %s", path)
        return path

    def save_scaler(self, scaler) -> Path:
        path = self.artifact_dir / SCALER_FILENAME
        joblib.dump(scaler, path)
        logger.info("Scaler saved → %s", path)
        return path

    def save_label_encoder(self, encoder) -> Path:
        path = self.artifact_dir / ENCODER_FILENAME
        joblib.dump(encoder, path)
        logger.info("LabelEncoder saved → %s", path)
        return path

    def save_feature_columns(self, columns: List[str]) -> Path:
        path = self.artifact_dir / FEATURES_FILENAME
        with open(path, "w") as f:
            json.dump(columns, f, indent=2)
        logger.info("Feature columns saved → %s", path)
        return path

    def save_metadata(self, meta: Dict[str, Any]) -> Path:
        meta["saved_at"] = datetime.utcnow().isoformat()
        meta["version"] = self.version
        path = self.artifact_dir / METADATA_FILENAME
        with open(path, "w") as f:
            json.dump(meta, f, indent=2, default=str)
        logger.info("Metadata saved → %s", path)
        return path

    def save_history(self, history: Dict) -> Path:
        path = self.artifact_dir / HISTORY_FILENAME
        with open(path, "w") as f:
            json.dump(history, f, indent=2, default=str)
        logger.info("Training history saved → %s", path)
        return path

    # ── Loading ───────────────────────────────────────────────────────────────

    def load_model(self, model_arch=None, best: bool = True):
        """Load model weights into model_arch, or load full model if arch is None."""
        import torch
        # Try full model first
        full_path = self.artifact_dir / "model_full.pt"
        if full_path.exists() and model_arch is None:
            model = torch.load(str(full_path), map_location="cpu", weights_only=False)
            logger.info("Full model loaded ← %s", full_path)
            return model

        name = "model_best.pt" if best else "model_final.pt"
        path = self.artifact_dir / name
        if not path.exists():
            alt = "model_final.pt" if best else "model_best.pt"
            path = self.artifact_dir / alt
        if not path.exists():
            raise FileNotFoundError(f"No model found in {self.artifact_dir}")

        if model_arch is None:
            raise ValueError(
                "model_arch must be provided when loading state_dict. "
                "Use load_model_full() or pass the model architecture."
            )
        state = torch.load(str(path), map_location="cpu", weights_only=True)
        model_arch.load_state_dict(state)
        logger.info("Model state_dict loaded ← %s", path)
        return model_arch

    def load_pipeline(self):
        path = self.artifact_dir / PIPELINE_FILENAME
        if not path.exists():
            raise FileNotFoundError(f"Pipeline not found: {path}")
        pipeline = joblib.load(path)
        logger.info("Pipeline loaded ← %s", path)
        return pipeline

    def load_scaler(self):
        path = self.artifact_dir / SCALER_FILENAME
        if not path.exists():
            raise FileNotFoundError(f"Scaler not found: {path}")
        return joblib.load(path)

    def load_label_encoder(self):
        path = self.artifact_dir / ENCODER_FILENAME
        if not path.exists():
            raise FileNotFoundError(f"LabelEncoder not found: {path}")
        return joblib.load(path)

    def load_feature_columns(self) -> List[str]:
        path = self.artifact_dir / FEATURES_FILENAME
        if not path.exists():
            raise FileNotFoundError(f"Feature columns not found: {path}")
        with open(path) as f:
            return json.load(f)

    def load_metadata(self) -> Dict:
        path = self.artifact_dir / METADATA_FILENAME
        if not path.exists():
            return {}
        with open(path) as f:
            return json.load(f)

    def load_history(self) -> Dict:
        path = self.artifact_dir / HISTORY_FILENAME
        if not path.exists():
            return {}
        with open(path) as f:
            return json.load(f)

    # ── Utilities ─────────────────────────────────────────────────────────────

    def exists(self) -> bool:
        return (
            (self.artifact_dir / "model_best.pt").exists()
            or (self.artifact_dir / "model_final.pt").exists()
            or (self.artifact_dir / "model_full.pt").exists()
        )

    def list_artifacts(self) -> List[str]:
        return [p.name for p in self.artifact_dir.iterdir()]

    @classmethod
    def for_version(cls, version: str, base_dir: Path = ARTIFACT_DIR) -> "ArtifactManager":
        return cls(version=version, base_dir=base_dir)

    @classmethod
    def list_versions(cls, base_dir: Path = ARTIFACT_DIR) -> List[str]:
        if not base_dir.exists():
            return []
        return sorted(p.name for p in base_dir.iterdir() if p.is_dir())
