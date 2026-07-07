"""Visualization utilities — saves plots to the artifacts directory."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from ml.config import PLOT_DIR
from ml.utils.logger import get_logger

logger = get_logger(__name__)


def _get_matplotlib():
    """Import matplotlib with non-interactive backend."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def plot_training_history(
    history: Dict[str, List[float]],
    save_dir: Path = PLOT_DIR,
    prefix: str = "",
) -> List[Path]:
    """Plot and save loss and accuracy curves from training history."""
    plt = _get_matplotlib()
    saved = []
    save_dir.mkdir(parents=True, exist_ok=True)

    # Loss curve
    if "loss" in history:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(history["loss"], label="Train Loss")
        if "val_loss" in history:
            ax.plot(history["val_loss"], label="Val Loss")
        ax.set_title("Training & Validation Loss")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Loss")
        ax.legend()
        ax.grid(True, alpha=0.3)
        path = save_dir / f"{prefix}loss_curve.png"
        fig.savefig(path, dpi=100, bbox_inches="tight")
        plt.close(fig)
        saved.append(path)
        logger.info("Loss curve saved → %s", path)

    # Accuracy curve
    acc_key = "accuracy" if "accuracy" in history else "acc"
    val_acc_key = "val_accuracy" if "val_accuracy" in history else "val_acc"
    if acc_key in history:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(history[acc_key], label="Train Accuracy")
        if val_acc_key in history:
            ax.plot(history[val_acc_key], label="Val Accuracy")
        ax.set_title("Training & Validation Accuracy")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Accuracy")
        ax.legend()
        ax.grid(True, alpha=0.3)
        path = save_dir / f"{prefix}accuracy_curve.png"
        fig.savefig(path, dpi=100, bbox_inches="tight")
        plt.close(fig)
        saved.append(path)
        logger.info("Accuracy curve saved → %s", path)

    return saved


def plot_confusion_matrix(
    cm: List[List[int]],
    class_names: List[str],
    save_dir: Path = PLOT_DIR,
    prefix: str = "",
) -> Path:
    """Plot and save a confusion matrix heatmap."""
    plt = _get_matplotlib()
    save_dir.mkdir(parents=True, exist_ok=True)

    cm_arr = np.array(cm)
    fig, ax = plt.subplots(figsize=(max(6, len(class_names)), max(5, len(class_names))))
    im = ax.imshow(cm_arr, interpolation="nearest", cmap="Blues")
    plt.colorbar(im, ax=ax)

    ax.set_xticks(range(len(class_names)))
    ax.set_yticks(range(len(class_names)))
    ax.set_xticklabels(class_names, rotation=45, ha="right")
    ax.set_yticklabels(class_names)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Confusion Matrix")

    thresh = cm_arr.max() / 2.0
    for i in range(cm_arr.shape[0]):
        for j in range(cm_arr.shape[1]):
            ax.text(j, i, str(cm_arr[i, j]),
                    ha="center", va="center",
                    color="white" if cm_arr[i, j] > thresh else "black")

    path = save_dir / f"{prefix}confusion_matrix.png"
    fig.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    logger.info("Confusion matrix saved → %s", path)
    return path


def plot_roc_curve(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    save_dir: Path = PLOT_DIR,
    prefix: str = "",
) -> Optional[Path]:
    """Plot and save ROC curve (binary classification only)."""
    try:
        from sklearn.metrics import roc_curve, auc
        plt = _get_matplotlib()
        save_dir.mkdir(parents=True, exist_ok=True)

        fpr, tpr, _ = roc_curve(y_true, y_scores)
        roc_auc = auc(fpr, tpr)

        fig, ax = plt.subplots(figsize=(7, 6))
        ax.plot(fpr, tpr, color="darkorange", lw=2,
                label=f"ROC curve (AUC = {roc_auc:.4f})")
        ax.plot([0, 1], [0, 1], color="navy", lw=1, linestyle="--")
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel("False Positive Rate")
        ax.set_ylabel("True Positive Rate")
        ax.set_title("Receiver Operating Characteristic")
        ax.legend(loc="lower right")
        ax.grid(True, alpha=0.3)

        path = save_dir / f"{prefix}roc_curve.png"
        fig.savefig(path, dpi=100, bbox_inches="tight")
        plt.close(fig)
        logger.info("ROC curve saved → %s", path)
        return path
    except Exception as exc:
        logger.warning("Could not plot ROC curve: %s", exc)
        return None
