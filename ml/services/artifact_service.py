"""Artifact service — stable interface for querying and managing ML artifacts."""

from pathlib import Path
from typing import Dict, List, Optional

from ml.artifacts.manager import ArtifactManager
from ml.config import ARTIFACT_DIR, MODEL_VERSION
from ml.utils.logger import get_logger

logger = get_logger(__name__)


class ArtifactService:
    """Provides a stable API for FastAPI to inspect and manage artifacts.

    TODO (external/fastapi): Import and use this service in the
    /model/status and /model/metrics endpoints.
    """

    def __init__(self, artifact_dir: Path = ARTIFACT_DIR) -> None:
        self.artifact_dir = artifact_dir

    def list_versions(self) -> List[str]:
        return ArtifactManager.list_versions(self.artifact_dir)

    def get_metadata(self, version: str = MODEL_VERSION) -> Dict:
        am = ArtifactManager(version=version, base_dir=self.artifact_dir)
        return am.load_metadata()

    def get_history(self, version: str = MODEL_VERSION) -> Dict:
        am = ArtifactManager(version=version, base_dir=self.artifact_dir)
        return am.load_history()

    def model_exists(self, version: str = MODEL_VERSION) -> bool:
        am = ArtifactManager(version=version, base_dir=self.artifact_dir)
        return am.exists()

    def list_artifacts(self, version: str = MODEL_VERSION) -> List[str]:
        am = ArtifactManager(version=version, base_dir=self.artifact_dir)
        return am.list_artifacts()

    def get_metrics(self, version: str = MODEL_VERSION) -> Optional[Dict]:
        meta = self.get_metadata(version)
        return meta.get("eval_metrics")
