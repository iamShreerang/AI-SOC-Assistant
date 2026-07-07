"""Training service — coordinates training, evaluation, and visualization.

TODO (external/fastapi): Import TrainingService in the /model/train and
/model/retrain route handlers. Call run_training() in a background task.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from ml.artifacts.manager import ArtifactManager
from ml.config import ARTIFACT_DIR, MODEL_VERSION
from ml.model.trainer import Trainer
from ml.visualization.plots import plot_training_history, plot_confusion_matrix
from ml.utils.logger import get_logger

logger = get_logger(__name__)


class TrainingService:
    """High-level training coordinator used by FastAPI and CLI scripts.

    Usage
    -----
    svc = TrainingService()
    result = svc.run_training({"beth": "/data/beth.csv"})
    result = svc.run_training_all()
    """

    def __init__(
        self,
        model_version: str = MODEL_VERSION,
        artifact_dir: Path = ARTIFACT_DIR,
    ) -> None:
        self.model_version = model_version
        self.artifact_dir = artifact_dir

    def run_training(self, dataset_paths: Dict[str, str]) -> Dict:
        """Train on explicit dataset paths and generate all artifacts + plots."""
        trainer = Trainer(model_version=self.model_version, artifact_dir=self.artifact_dir)
        metrics = trainer.train(dataset_paths)
        self._generate_plots(trainer)
        return {"status": "completed", "version": self.model_version, "metrics": metrics}

    def run_training_all(self) -> Dict:
        """Auto-discover datasets and train."""
        trainer = Trainer(model_version=self.model_version, artifact_dir=self.artifact_dir)
        metrics = trainer.train_all()
        self._generate_plots(trainer)
        return {"status": "completed", "version": self.model_version, "metrics": metrics}

    def run_retrain(self, dataset_paths: Dict[str, str]) -> Dict:
        """Retrain with a new timestamped version."""
        trainer = Trainer(artifact_dir=self.artifact_dir)
        metrics = trainer.retrain(dataset_paths)
        self._generate_plots(trainer)
        return {"status": "completed", "version": trainer.model_version, "metrics": metrics}

    def _generate_plots(self, trainer: Trainer) -> None:
        if not trainer.history or not trainer._artifacts:
            return

        version = trainer.model_version
        plot_dir = self.artifact_dir / version / "plots"
        plot_dir.mkdir(parents=True, exist_ok=True)

        try:
            plot_training_history(trainer.history, save_dir=plot_dir, prefix=f"{version}_")
        except Exception as exc:
            logger.warning("Could not generate training history plots: %s", exc)

        try:
            meta = trainer._artifacts.load_metadata()
            cm = meta.get("eval_metrics", {}).get("confusion_matrix")
            classes = meta.get("classes", ["benign", "attack"])
            if cm:
                plot_confusion_matrix(cm, classes, save_dir=plot_dir, prefix=f"{version}_")
        except Exception as exc:
            logger.warning("Could not generate confusion matrix plot: %s", exc)
