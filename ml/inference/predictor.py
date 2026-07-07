"""
Predictor — loads trained CNN-LSTM + preprocessing pipeline and runs inference.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

from ml.model import CNNLSTM
from ml.preprocessing import PreprocessingPipeline, SEQUENCE_LENGTH

logger = logging.getLogger(__name__)

_DEFAULT_MODEL_DIR = Path(__file__).parent.parent / "saved_models"


class Predictor:
    def __init__(
        self,
        model: CNNLSTM,
        pipeline: PreprocessingPipeline,
        device: str = "cpu",
        threshold: float = 0.5,
    ) -> None:
        self.model = model.to(device)
        self.model.eval()
        self.pipeline = pipeline
        self.device = device
        self.seq_len = SEQUENCE_LENGTH
        self.threshold = threshold

    # -- Factory ------------------------------------------------------------
    @classmethod
    def load(cls, model_dir: str | Path = _DEFAULT_MODEL_DIR) -> "Predictor":
        import pickle
        model_dir = Path(model_dir)
        device = "cuda" if torch.cuda.is_available() else "cpu"

        pipeline = PreprocessingPipeline.load(model_dir)

        checkpoint = torch.load(model_dir / "cnn_lstm.pt", map_location=device)
        model = CNNLSTM(
            n_features=pipeline.n_features,
            seq_len=SEQUENCE_LENGTH,
            n_classes=checkpoint.get("n_classes", 2),
        )
        model.load_state_dict(checkpoint["model_state_dict"])

        threshold = 0.5
        threshold_path = model_dir / "threshold.pkl"
        if threshold_path.exists():
            with open(threshold_path, "rb") as f:
                threshold = pickle.load(f)

        logger.info("Predictor loaded from %s on %s (threshold=%.2f)", model_dir, device, threshold)
        return cls(model, pipeline, device, threshold)

    # -- Inference ----------------------------------------------------------
    def predict_batch(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Args:
            records: list of raw log dicts (must contain FEATURE_COLS keys)
        Returns:
            list of dicts with keys: label, label_name, confidence, latency_ms
        """
        import pandas as pd
        from ml.preprocessing import FEATURE_COLS

        if len(records) < self.seq_len:
            pad = [dict.fromkeys(FEATURE_COLS, 0)] * (self.seq_len - len(records))
            records = pad + list(records)

        df = pd.DataFrame(records)
        for col in FEATURE_COLS:
            if col not in df.columns:
                df[col] = 0

        X = self.pipeline.transform(df)

        results = []
        t0 = time.perf_counter()
        for i in range(len(X) - self.seq_len + 1):
            seq = torch.tensor(X[i: i + self.seq_len], dtype=torch.float32).unsqueeze(0).to(self.device)
            with torch.no_grad():
                logits = self.model(seq)
                probs = F.softmax(logits, dim=-1)
                attack_prob = float(probs[0, 1].item())
                pred = 1 if attack_prob >= self.threshold else 0
                conf = attack_prob if pred == 1 else (1.0 - attack_prob)

            latency_ms = (time.perf_counter() - t0) * 1000
            results.append({
                "label": pred,
                "label_name": "attack" if pred == 1 else "normal",
                "confidence": round(conf, 4),
                "attack_probability": round(attack_prob, 4),
                "latency_ms": round(latency_ms, 2),
            })
            t0 = time.perf_counter()

        return results
