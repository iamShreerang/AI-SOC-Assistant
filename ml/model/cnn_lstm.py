"""
CNN-LSTM model for intrusion detection on UNSW-NB15.

Input shape : (batch, seq_len, n_features)
Output      : (batch, n_classes)  — binary (0=normal, 1=attack)
"""
from __future__ import annotations

import torch
import torch.nn as nn


class CNNLSTM(nn.Module):
    def __init__(
        self,
        n_features: int,
        seq_len: int,
        n_classes: int = 2,
        cnn_filters: int = 64,
        kernel_size: int = 3,
        lstm_hidden: int = 128,
        lstm_layers: int = 2,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(n_features, cnn_filters, kernel_size, padding=kernel_size // 2),
            nn.BatchNorm1d(cnn_filters),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        self.lstm = nn.LSTM(
            cnn_filters, lstm_hidden, lstm_layers,
            batch_first=True, dropout=dropout if lstm_layers > 1 else 0.0,
        )
        self.classifier = nn.Sequential(
            nn.Linear(lstm_hidden, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, n_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, T, F) → conv expects (B, F, T)
        x = x.permute(0, 2, 1)
        x = self.conv(x)
        x = x.permute(0, 2, 1)          # back to (B, T, filters)
        _, (h_n, _) = self.lstm(x)
        out = self.classifier(h_n[-1])  # last layer hidden state
        return out
