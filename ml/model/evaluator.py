"""Model evaluator — classification metrics including ROC-AUC and latency."""

import time
from typing import Dict, List

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, classification_report, confusion_matrix, roc_auc_score,
)

from ml.utils.logger import get_logger

logger = get_logger(__name__)


class Evaluator:
    """Evaluate a trained PyTorch model on (X_seq, y_true) numpy arrays.

    Metrics returned
    ----------------
    accuracy, precision, recall, f1_score, roc_auc (binary only),
    confusion_matrix, classification_report, prediction_latency_ms
    """

    def __init__(self, model: torch.nn.Module, classes: List[str]) -> None:
        self.model = model
        self.classes = classes
        self._binary = len(classes) == 2

    def evaluate(self, X_seq: np.ndarray, y_true: np.ndarray) -> Dict:
        """Run inference and return a full metrics dict."""
        self.model.eval()
        device = next(self.model.parameters()).device

        t0 = time.perf_counter()
        with torch.no_grad():
            tensor = torch.tensor(X_seq, dtype=torch.float32).to(device)
            raw = self.model(tensor).cpu().numpy()
        elapsed_ms = (time.perf_counter() - t0) * 1000

        if self._binary:
            import torch.nn.functional as F
            probs = 1 / (1 + np.exp(-raw.squeeze()))  # sigmoid
            y_pred = (probs >= 0.5).astype(int)
        else:
            import torch.nn.functional as F
            exp = np.exp(raw - raw.max(axis=1, keepdims=True))
            probs = exp / exp.sum(axis=1, keepdims=True)  # softmax
            y_pred = np.argmax(probs, axis=1)

        avg = "binary" if self._binary else "weighted"
        metrics: Dict = {
            "accuracy":              float(accuracy_score(y_true, y_pred)),
            "precision":             float(precision_score(y_true, y_pred, average=avg, zero_division=0)),
            "recall":                float(recall_score(y_true, y_pred, average=avg, zero_division=0)),
            "f1_score":              float(f1_score(y_true, y_pred, average=avg, zero_division=0)),
            "prediction_latency_ms": round(elapsed_ms / max(len(X_seq), 1), 4),
            "total_samples":         len(X_seq),
        }

        if self._binary:
            try:
                metrics["roc_auc"] = float(roc_auc_score(y_true, probs))
            except Exception:
                metrics["roc_auc"] = None

        target_names = ["benign", "attack"] if self._binary else self.classes
        report = classification_report(y_true, y_pred, target_names=target_names, zero_division=0)
        logger.info("Evaluation report:\n%s", report)

        cm = confusion_matrix(y_true, y_pred)
        metrics["confusion_matrix"] = cm.tolist()
        metrics["classification_report"] = report
        return metrics
