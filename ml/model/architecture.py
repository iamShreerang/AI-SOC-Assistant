"""CNN-LSTM hybrid model — PyTorch implementation.

Input shape: (batch, sequence_length, n_features)

Architecture
------------
Conv1d → BN → MaxPool → Conv1d → BN → MaxPool → LSTM → Dropout → Dense → BN → Output
"""

import torch
import torch.nn as nn

from ml.config import (
    CNN_FILTERS, CNN_KERNEL_SIZE, LSTM_UNITS,
    DROPOUT_RATE, DENSE_UNITS, USE_BATCH_NORM,
)


class CnnLstm(nn.Module):
    """Configurable CNN-LSTM for binary and multiclass NIDS classification."""

    def __init__(
        self,
        sequence_length: int,
        n_features: int,
        n_classes: int,
        cnn_filters: int = CNN_FILTERS,
        cnn_kernel_size: int = CNN_KERNEL_SIZE,
        lstm_units: int = LSTM_UNITS,
        dropout_rate: float = DROPOUT_RATE,
        dense_units: int = DENSE_UNITS,
        use_batch_norm: bool = USE_BATCH_NORM,
    ) -> None:
        super().__init__()
        self.n_classes = n_classes
        self.binary = n_classes == 2

        # CNN block 1 — input: (batch, seq, feat) → permute to (batch, feat, seq)
        self.conv1 = nn.Conv1d(n_features, cnn_filters, cnn_kernel_size, padding=cnn_kernel_size // 2)
        self.bn1 = nn.BatchNorm1d(cnn_filters) if use_batch_norm else nn.Identity()
        self.pool1 = nn.MaxPool1d(kernel_size=2, padding=0)

        # CNN block 2
        self.conv2 = nn.Conv1d(cnn_filters, cnn_filters * 2, cnn_kernel_size, padding=cnn_kernel_size // 2)
        self.bn2 = nn.BatchNorm1d(cnn_filters * 2) if use_batch_norm else nn.Identity()
        self.pool2 = nn.MaxPool1d(kernel_size=2, padding=0)

        # Compute LSTM input size after pooling
        lstm_seq = sequence_length // 4  # two MaxPool1d(2)
        if lstm_seq < 1:
            lstm_seq = 1

        # LSTM
        self.lstm = nn.LSTM(
            input_size=cnn_filters * 2,
            hidden_size=lstm_units,
            batch_first=True,
        )
        self.dropout = nn.Dropout(dropout_rate)

        # Dense head
        self.dense = nn.Linear(lstm_units, dense_units)
        self.bn3 = nn.BatchNorm1d(dense_units) if use_batch_norm else nn.Identity()
        self.dropout2 = nn.Dropout(dropout_rate / 2)
        self.relu = nn.ReLU()

        # Output
        out_size = 1 if self.binary else n_classes
        self.output_layer = nn.Linear(dense_units, out_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq, feat) → (batch, feat, seq) for Conv1d
        x = x.permute(0, 2, 1)

        x = self.relu(self.bn1(self.conv1(x)))
        x = self.pool1(x)

        x = self.relu(self.bn2(self.conv2(x)))
        x = self.pool2(x)

        # (batch, channels, seq) → (batch, seq, channels) for LSTM
        x = x.permute(0, 2, 1)
        x, _ = self.lstm(x)
        x = x[:, -1, :]  # last timestep
        x = self.dropout(x)

        x = self.relu(self.bn3(self.dense(x)))
        x = self.dropout2(x)
        return self.output_layer(x)


def build_cnn_lstm(
    sequence_length: int,
    n_features: int,
    n_classes: int,
    cnn_filters: int = CNN_FILTERS,
    cnn_kernel_size: int = CNN_KERNEL_SIZE,
    lstm_units: int = LSTM_UNITS,
    dropout_rate: float = DROPOUT_RATE,
    dense_units: int = DENSE_UNITS,
    learning_rate: float = 0.001,
    use_batch_norm: bool = USE_BATCH_NORM,
) -> CnnLstm:
    """Build and return a CnnLstm model (not compiled — PyTorch style)."""
    return CnnLstm(
        sequence_length=sequence_length,
        n_features=n_features,
        n_classes=n_classes,
        cnn_filters=cnn_filters,
        cnn_kernel_size=cnn_kernel_size,
        lstm_units=lstm_units,
        dropout_rate=dropout_rate,
        dense_units=dense_units,
        use_batch_norm=use_batch_norm,
    )
