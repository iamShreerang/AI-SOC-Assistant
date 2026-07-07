"""Model trainer for the CNN-LSTM NIDS model — PyTorch implementation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset

from ml.config import (
    MODEL_VERSION, SEQUENCE_LENGTH,
    EPOCHS, BATCH_SIZE, LEARNING_RATE, PATIENCE, TEST_SIZE, RANDOM_STATE,
    ARTIFACT_DIR,
)
from ml.artifacts.manager import ArtifactManager
from ml.datasets.manager import DatasetManager
from ml.model.architecture import build_cnn_lstm
from ml.model.evaluator import Evaluator
from ml.preprocessing.pipeline import PreprocessingPipeline
from ml.preprocessing.sequences import create_sequences
from ml.utils.logger import get_logger

logger = get_logger(__name__)


class Trainer:
    """Orchestrates dataset loading, preprocessing, training, evaluation, and saving."""

    def __init__(
        self,
        model_version: str = MODEL_VERSION,
        artifact_dir: Path = ARTIFACT_DIR,
        sequence_length: int = SEQUENCE_LENGTH,
        epochs: int = EPOCHS,
        batch_size: int = BATCH_SIZE,
        learning_rate: float = LEARNING_RATE,
        patience: int = PATIENCE,
    ) -> None:
        self.model_version = model_version
        self.artifact_dir = artifact_dir
        self.sequence_length = sequence_length
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.patience = patience
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.pipeline: Optional[PreprocessingPipeline] = None
        self.model: Optional[nn.Module] = None
        self.history: Optional[dict] = None
        self._artifacts: Optional[ArtifactManager] = None

    # ── Public API ────────────────────────────────────────────────────────────

    def train(self, dataset_paths: Dict[str, str]) -> dict:
        """Train on explicit dataset_paths mapping (name → file path)."""
        logger.info("Starting training — datasets: %s", list(dataset_paths))
        manager = DatasetManager()
        result = manager.load(dataset_paths)
        if result.failed_names:
            logger.warning("Skipped failed datasets: %s", result.failed_names)
        return self._run_training(result.combined, result.loaded_names, manager.summary())

    def train_all(self) -> dict:
        """Auto-discover and train on all available datasets in DATA_DIR."""
        logger.info("Auto-discovering datasets for training")
        manager = DatasetManager()
        result = manager.load_all()
        if result.combined.empty:
            raise RuntimeError("No datasets found. Place CSV files in ml/data/")
        return self._run_training(result.combined, result.loaded_names, manager.summary())

    def retrain(self, dataset_paths: Dict[str, str]) -> dict:
        """Retrain from scratch with a new version timestamp."""
        self.model_version = f"v_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        logger.info("Retraining — new version: %s", self.model_version)
        return self.train(dataset_paths)

    # ── Core training logic ───────────────────────────────────────────────────

    def _run_training(
        self,
        df: pd.DataFrame,
        loaded_names: List[str],
        dataset_summary: dict,
    ) -> dict:
        logger.info("Combined dataset: %d rows, %d cols", len(df), df.shape[1])
        logger.info("Using device: %s", self.device)

        self.pipeline = PreprocessingPipeline()
        X, y = self.pipeline.fit_transform(df, label_col="label")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=0.1, random_state=RANDOM_STATE, stratify=y_train
        )

        X_train_seq, y_train_seq = create_sequences(X_train, y_train, self.sequence_length)
        X_val_seq,   y_val_seq   = create_sequences(X_val,   y_val,   self.sequence_length)
        X_test_seq,  y_test_seq  = create_sequences(X_test,  y_test,  self.sequence_length)

        n_classes = len(self.pipeline.classes)
        self._artifacts = ArtifactManager(version=self.model_version, base_dir=self.artifact_dir)

        self.model = build_cnn_lstm(
            sequence_length=self.sequence_length,
            n_features=self.pipeline.n_features,
            n_classes=n_classes,
            learning_rate=self.learning_rate,
        ).to(self.device)

        logger.info("Model architecture:\n%s", self.model)

        self.history = self._fit(X_train_seq, y_train_seq, X_val_seq, y_val_seq, n_classes)

        evaluator = Evaluator(self.model, self.pipeline.classes)
        eval_metrics = evaluator.evaluate(X_test_seq, y_test_seq)

        self._save_all_artifacts(eval_metrics, loaded_names, dataset_summary)

        logger.info(
            "Training complete — accuracy=%.4f, f1=%.4f",
            eval_metrics.get("accuracy", 0), eval_metrics.get("f1_score", 0),
        )
        return eval_metrics

    # ── PyTorch training loop ─────────────────────────────────────────────────

    def _fit(
        self,
        X_train: np.ndarray, y_train: np.ndarray,
        X_val: np.ndarray,   y_val: np.ndarray,
        n_classes: int,
    ) -> dict:
        binary = n_classes == 2
        criterion = nn.BCEWithLogitsLoss() if binary else nn.CrossEntropyLoss()

        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="min", factor=0.5,
            patience=max(1, self.patience // 2), min_lr=1e-6,
        )

        train_loader = self._make_loader(X_train, y_train, binary, shuffle=True)
        val_loader   = self._make_loader(X_val,   y_val,   binary, shuffle=False)

        history = {"loss": [], "val_loss": [], "accuracy": [], "val_accuracy": []}
        best_val_loss = float("inf")
        best_state = None
        no_improve = 0
        best_path = self._artifacts.artifact_dir / "model_best.pt"

        for epoch in range(1, self.epochs + 1):
            train_loss, train_acc = self._epoch(train_loader, criterion, optimizer, binary, train=True)
            val_loss,   val_acc   = self._epoch(val_loader,   criterion, None,      binary, train=False)
            scheduler.step(val_loss)

            history["loss"].append(train_loss)
            history["val_loss"].append(val_loss)
            history["accuracy"].append(train_acc)
            history["val_accuracy"].append(val_acc)

            logger.info(
                "Epoch %d/%d — loss=%.4f acc=%.4f | val_loss=%.4f val_acc=%.4f",
                epoch, self.epochs, train_loss, train_acc, val_loss, val_acc,
            )

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_state = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}
                torch.save(best_state, best_path)
                no_improve = 0
            else:
                no_improve += 1
                if no_improve >= self.patience:
                    logger.info("Early stopping at epoch %d", epoch)
                    break

        # Restore best weights
        if best_state is not None:
            self.model.load_state_dict(best_state)
            logger.info("Best model restored (val_loss=%.4f)", best_val_loss)

        return history

    def _epoch(self, loader, criterion, optimizer, binary: bool, train: bool):
        self.model.train(train)
        total_loss, correct, total = 0.0, 0, 0

        with torch.set_grad_enabled(train):
            for X_batch, y_batch in loader:
                X_batch = X_batch.to(self.device)
                y_batch = y_batch.to(self.device)

                logits = self.model(X_batch)

                if binary:
                    loss = criterion(logits.squeeze(1), y_batch)
                    preds = (torch.sigmoid(logits.squeeze(1)) >= 0.5).long()
                else:
                    loss = criterion(logits, y_batch.long())
                    preds = logits.argmax(dim=1)

                if train:
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()

                total_loss += loss.item() * len(X_batch)
                correct += (preds == y_batch.long()).sum().item()
                total += len(X_batch)

        return total_loss / total, correct / total

    def _make_loader(self, X: np.ndarray, y: np.ndarray, binary: bool, shuffle: bool) -> DataLoader:
        X_t = torch.tensor(X, dtype=torch.float32)
        y_t = torch.tensor(y, dtype=torch.float32 if binary else torch.long)
        return DataLoader(TensorDataset(X_t, y_t), batch_size=self.batch_size, shuffle=shuffle)

    # ── Artifact saving ───────────────────────────────────────────────────────

    def _save_all_artifacts(
        self,
        eval_metrics: dict,
        loaded_names: List[str],
        dataset_summary: dict,
    ) -> None:
        am = self._artifacts
        am.save_model(self.model, best=False)
        am.save_pipeline(self.pipeline)
        am.save_scaler(self.pipeline.scaler)
        am.save_label_encoder(self.pipeline.label_encoder)
        am.save_feature_columns(self.pipeline.feature_columns)
        am.save_history(self.history)

        safe_metrics = {
            k: v for k, v in eval_metrics.items()
            if k not in ("confusion_matrix", "classification_report")
        }
        meta = {
            "model_version":   self.model_version,
            "trained_at":      datetime.utcnow().isoformat(),
            "sequence_length": self.sequence_length,
            "n_features":      self.pipeline.n_features,
            "classes":         self.pipeline.classes,
            "datasets_used":   loaded_names,
            "dataset_summary": dataset_summary,
            "hyperparameters": {
                "epochs":        self.epochs,
                "batch_size":    self.batch_size,
                "learning_rate": self.learning_rate,
                "patience":      self.patience,
            },
            "eval_metrics": safe_metrics,
        }
        am.save_metadata(meta)
        logger.info("All artifacts saved to %s", am.artifact_dir)
