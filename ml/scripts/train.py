"""
Train CNN-LSTM on all 4 datasets (UNSW-NB15, DSRL-APT-2023, BETH, CSE-CIC-IDS2018)
and save artifacts to ml/saved_models/.

Usage:
    py ml/scripts/train.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ml.model import CNNLSTM
from ml.preprocessing import PreprocessingPipeline, SEQUENCE_LENGTH
from ml.preprocessing.pipeline import load_all_datasets

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
SAVE_DIR = Path(__file__).parent.parent / "saved_models"
EPOCHS = 15
BATCH_SIZE = 256
LR = 1e-3


def main() -> None:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info("Using device: %s", device)

    logger.info("Loading all datasets...")
    df = load_all_datasets(DATA_DIR)

    pipeline = PreprocessingPipeline()
    X_all = pipeline.fit_transform(df)
    y_all = df["label"].astype(int).values

    # Stratified split AFTER sequence creation to avoid leakage
    X_seq, y_seq = PreprocessingPipeline.make_sequences(X_all, y_all, SEQUENCE_LENGTH)
    logger.info("Sequences: %s | attack=%.1f%%", X_seq.shape, y_seq.mean() * 100)

    X_train, X_val, y_train, y_val = train_test_split(
        X_seq, y_seq, test_size=0.2, stratify=y_seq, random_state=42
    )
    logger.info("Train: %d | Val: %d", len(X_train), len(X_val))

    train_ds = TensorDataset(torch.tensor(X_train), torch.tensor(y_train))
    val_ds = TensorDataset(torch.tensor(X_val), torch.tensor(y_val))
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, num_workers=0)

    n_classes = 2
    model = CNNLSTM(
        n_features=pipeline.n_features, seq_len=SEQUENCE_LENGTH, n_classes=n_classes
    ).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    # Class-weighted loss
    n_normal = int((y_train == 0).sum())
    n_attack = int((y_train == 1).sum())
    total = n_normal + n_attack
    weights = torch.tensor(
        [total / (2 * n_normal), total / (2 * n_attack)], dtype=torch.float32
    ).to(device)
    logger.info("Class weights: normal=%.4f attack=%.4f", weights[0].item(), weights[1].item())
    criterion = nn.CrossEntropyLoss(weight=weights)

    best_val_acc = 0.0
    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_loss, correct, total = 0.0, 0, 0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item() * len(yb)
            correct += (logits.argmax(1) == yb).sum().item()
            total += len(yb)
        scheduler.step()

        # Validation
        model.eval()
        val_correct, val_total = 0, 0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                val_correct += (model(xb).argmax(1) == yb).sum().item()
                val_total += len(yb)
        val_acc = val_correct / val_total

        logger.info(
            "Epoch %2d/%d | loss=%.4f train_acc=%.4f val_acc=%.4f lr=%.6f",
            epoch, EPOCHS, total_loss / total, correct / total, val_acc,
            scheduler.get_last_lr()[0],
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(
                {"model_state_dict": model.state_dict(), "n_classes": n_classes},
                SAVE_DIR / "cnn_lstm.pt",
            )

    logger.info("Best val accuracy: %.4f", best_val_acc)
    pipeline.save(SAVE_DIR)
    logger.info("Artifacts saved to %s", SAVE_DIR)


if __name__ == "__main__":
    main()
