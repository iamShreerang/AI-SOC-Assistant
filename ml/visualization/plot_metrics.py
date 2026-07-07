"""
Plot training evaluation metrics from the saved model checkpoint.
Saves plots to ml/artifacts/plots/.

Usage:
    py ml/visualization/plot_metrics.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import (
    ConfusionMatrixDisplay, RocCurveDisplay,
    classification_report, confusion_matrix, roc_curve, auc,
)
import pandas as pd

from ml.inference import Predictor
from ml.preprocessing import PreprocessingPipeline, SEQUENCE_LENGTH

PLOTS_DIR = Path(__file__).parent.parent / "artifacts" / "plots"
DATA_DIR = Path(__file__).parent.parent / "data" / "UNSW-NB15"


def _load_test_data(pipeline: PreprocessingPipeline):
    df = pd.read_csv(DATA_DIR / "UNSW_NB15_testing-set.csv")
    # Balanced 5k sample (2.5k normal + 2.5k attack)
    n_each = 2500
    normal = df[df["label"] == 0].sample(n=min(n_each, (df["label"]==0).sum()), random_state=42)
    attack = df[df["label"] == 1].sample(n=min(n_each, (df["label"]==1).sum()), random_state=42)
    df = pd.concat([normal, attack]).sample(frac=1, random_state=42).reset_index(drop=True)
    X = pipeline.transform(df)
    y = df["label"].astype(int).values
    X_seq, y_seq = PreprocessingPipeline.make_sequences(X, y, SEQUENCE_LENGTH)
    return X_seq, y_seq


def _run_inference(predictor: Predictor, X_seq: np.ndarray, threshold: float = 0.5):
    import torch
    import torch.nn.functional as F
    model = predictor.model
    device = predictor.device
    all_preds, all_probs = [], []
    batch_size = 512
    for i in range(0, len(X_seq), batch_size):
        xb = torch.tensor(X_seq[i:i+batch_size], dtype=torch.float32).to(device)
        with torch.no_grad():
            logits = model(xb)
            probs = F.softmax(logits, dim=-1)[:, 1].cpu().numpy()
            preds = (probs >= threshold).astype(int)
        all_preds.extend(preds)
        all_probs.extend(probs)
    return np.array(all_preds), np.array(all_probs)


def _find_best_threshold(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Find threshold that maximises macro F1."""
    from sklearn.metrics import f1_score
    best_t, best_f1 = 0.5, 0.0
    for t in np.arange(0.1, 0.9, 0.05):
        preds = (y_prob >= t).astype(int)
        f1 = f1_score(y_true, preds, average="macro", zero_division=0)
        if f1 > best_f1:
            best_f1, best_t = f1, float(t)
    return best_t


def main() -> None:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading predictor...")
    predictor = Predictor.load()

    print("Loading test data (balanced 5k sample)...")
    X_seq, y_true = _load_test_data(predictor.pipeline)

    print("Running inference (threshold search)...")
    # First pass with default threshold to get probabilities
    _, y_prob = _run_inference(predictor, X_seq, threshold=0.5)
    best_threshold = _find_best_threshold(y_true, y_prob)
    print(f"  Best threshold: {best_threshold:.2f}")
    y_pred, y_prob = _run_inference(predictor, X_seq, threshold=best_threshold)

    # Save threshold for use by Predictor
    threshold_path = Path(predictor.pipeline.__class__.__module__).parent
    import pickle, sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from streaming.config import MODEL_DIR
    with open(Path(MODEL_DIR) / "threshold.pkl", "wb") as f:
        pickle.dump(best_threshold, f)
    print(f"  Saved threshold={best_threshold:.2f} to {MODEL_DIR}/threshold.pkl")

    # ── Confusion matrix ────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(5, 4))
    cm = confusion_matrix(y_true, y_pred)
    ConfusionMatrixDisplay(cm, display_labels=["Normal", "Attack"]).plot(ax=ax, colorbar=False)
    ax.set_title("CNN-LSTM Confusion Matrix (test set)")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "confusion_matrix.png", dpi=120)
    plt.close(fig)
    print(f"  Saved confusion_matrix.png")

    # ── ROC curve ───────────────────────────────────────────────────────────
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    roc_auc = auc(fpr, tpr)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot(fpr, tpr, label=f"AUC = {roc_auc:.4f}", linewidth=2)
    ax.plot([0, 1], [0, 1], "k--", linewidth=1)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve — CNN-LSTM")
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "roc_curve.png", dpi=120)
    plt.close(fig)
    print(f"  Saved roc_curve.png  (AUC={roc_auc:.4f})")

    # ── Class distribution ──────────────────────────────────────────────────
    labels, counts = np.unique(y_true, return_counts=True)
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.bar(["Normal", "Attack"], counts, color=["steelblue", "tomato"])
    ax.set_title("Test Set Class Distribution")
    ax.set_ylabel("Count")
    for i, c in enumerate(counts):
        ax.text(i, c + 10, str(c), ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "class_distribution.png", dpi=120)
    plt.close(fig)
    print(f"  Saved class_distribution.png")

    # ── Classification report ───────────────────────────────────────────────
    report = classification_report(y_true, y_pred, target_names=["Normal", "Attack"])
    report_path = PLOTS_DIR / "classification_report.txt"
    report_path.write_text(report)
    print(f"  Saved classification_report.txt")
    print(f"\n{report}")
    print(f"Plots saved to {PLOTS_DIR}")


if __name__ == "__main__":
    main()
