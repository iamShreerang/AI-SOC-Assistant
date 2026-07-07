"""Training entry-point script.

Usage
-----
    py -3.14 scripts/train.py                  # auto-discover datasets
    py -3.14 scripts/train.py --generate       # generate synthetic data and train
    py -3.14 scripts/train.py --verify-only    # verify inference after training
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure ml/ package root is on sys.path when run as a script
_ML_ROOT = Path(__file__).resolve().parent.parent
if str(_ML_ROOT) not in sys.path:
    sys.path.insert(0, str(_ML_ROOT))

import numpy as np
import pandas as pd

from ml.config import DATA_DIR, ARTIFACT_DIR, MODEL_VERSION, DATASET_FILENAMES
from ml.services.training_service import TrainingService
from ml.utils.logger import get_logger

logger = get_logger("train")


# ── Synthetic dataset generator ───────────────────────────────────────────────

def generate_synthetic_dataset(path: Path, n_samples: int = 5000, n_features: int = 20) -> None:
    """Generate a synthetic binary-classification CSV for smoke-testing."""
    rng = np.random.default_rng(42)
    X = rng.standard_normal((n_samples, n_features)).astype(np.float32)
    # Attacks have slightly shifted distribution
    attack_mask = rng.random(n_samples) < 0.3
    X[attack_mask] += 1.5
    labels = attack_mask.astype(int)

    cols = [f"feature_{i}" for i in range(n_features)]
    df = pd.DataFrame(X, columns=cols)
    df["label"] = labels
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("Synthetic dataset written → %s (%d rows)", path, n_samples)


def ensure_synthetic_datasets() -> dict:
    """Create synthetic CSVs for all four datasets if they don't exist."""
    paths = {}
    for name, candidates in DATASET_FILENAMES.items():
        target = DATA_DIR / candidates[0]
        if not target.exists():
            logger.warning("Dataset '%s' not found — generating synthetic data at %s", name, target)
            generate_synthetic_dataset(target)
        paths[name] = str(target)
    return paths


# ── Dataset discovery ─────────────────────────────────────────────────────────

def discover_real_datasets() -> dict:
    """Return name → path for datasets that actually exist in DATA_DIR."""
    found = {}
    for name, candidates in DATASET_FILENAMES.items():
        for fname in candidates:
            p = DATA_DIR / fname
            if p.exists():
                found[name] = str(p)
                logger.info("Found dataset '%s' at %s", name, p)
                break
        else:
            logger.warning("Dataset '%s' not found in %s", name, DATA_DIR)
    return found


# ── Inference verification ────────────────────────────────────────────────────

def verify_inference(version: str = MODEL_VERSION) -> None:
    """Load the trained model and run a sample prediction."""
    from ml.inference.engine import InferenceEngine

    logger.info("Verifying inference for version=%s", version)
    engine = InferenceEngine.load(version=version, artifact_dir=ARTIFACT_DIR)

    # Build a dummy sample using the pipeline's feature columns
    features = {col: 0.0 for col in engine._pipeline.feature_columns}
    result = engine.predict_dict(features)
    logger.info(
        "Sample prediction — label=%s, confidence=%.4f, is_attack=%s",
        result.prediction, result.confidence, result.is_attack,
    )
    logger.info("Probabilities: %s", result.probabilities)
    logger.info("Inference verification PASSED")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Train the CNN-LSTM NIDS model")
    parser.add_argument("--generate", action="store_true",
                        help="Generate synthetic datasets if real ones are missing")
    parser.add_argument("--verify-only", action="store_true",
                        help="Skip training; only verify inference on saved model")
    parser.add_argument("--version", default=MODEL_VERSION,
                        help=f"Model version tag (default: {MODEL_VERSION})")
    args = parser.parse_args()

    if args.verify_only:
        verify_inference(args.version)
        return

    # Discover or generate datasets
    dataset_paths = discover_real_datasets()
    if not dataset_paths:
        if args.generate:
            logger.info("No real datasets found — generating synthetic datasets")
            dataset_paths = ensure_synthetic_datasets()
        else:
            logger.error(
                "No datasets found in %s. "
                "Place CSV files there or run with --generate to use synthetic data.",
                DATA_DIR,
            )
            sys.exit(1)
    elif args.generate:
        # Fill in missing datasets with synthetic ones
        for name, candidates in DATASET_FILENAMES.items():
            if name not in dataset_paths:
                target = DATA_DIR / candidates[0]
                logger.warning("Generating synthetic data for missing dataset '%s'", name)
                generate_synthetic_dataset(target)
                dataset_paths[name] = str(target)

    logger.info("Training with datasets: %s", list(dataset_paths))

    svc = TrainingService(model_version=args.version, artifact_dir=ARTIFACT_DIR)
    result = svc.run_training(dataset_paths)

    logger.info("Training result: status=%s, version=%s", result["status"], result["version"])
    metrics = result.get("metrics", {})
    for k, v in metrics.items():
        if k not in ("confusion_matrix", "classification_report"):
            logger.info("  %s = %s", k, v)

    if "classification_report" in metrics:
        logger.info("\nClassification Report:\n%s", metrics["classification_report"])

    # Verify inference with the freshly trained model
    verify_inference(args.version)

    logger.info("All done. Artifacts saved to %s/%s/", ARTIFACT_DIR, args.version)


if __name__ == "__main__":
    main()
