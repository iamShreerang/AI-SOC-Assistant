"""Sequence generation for CNN-LSTM input.

Converts a 2-D array (n_samples, n_features) into a 3-D array
(n_sequences, sequence_length, n_features) using a sliding window.
"""

import numpy as np
from ml.config import SEQUENCE_LENGTH


def create_sequences(
    X: np.ndarray,
    y: np.ndarray,
    sequence_length: int = SEQUENCE_LENGTH,
) -> tuple[np.ndarray, np.ndarray]:
    """Slide a window of *sequence_length* over X and y.

    Returns
    -------
    X_seq : (n_sequences, sequence_length, n_features)
    y_seq : (n_sequences,)  — label of the last step in each window
    """
    n = len(X) - sequence_length + 1
    if n <= 0:
        raise ValueError(
            f"Not enough samples ({len(X)}) for sequence_length={sequence_length}"
        )

    X_seq = np.lib.stride_tricks.sliding_window_view(
        X, window_shape=(sequence_length, X.shape[1])
    ).reshape(n, sequence_length, X.shape[1])

    y_seq = y[sequence_length - 1:]
    return X_seq.astype(np.float32), y_seq


def create_inference_sequence(
    X: np.ndarray,
    sequence_length: int = SEQUENCE_LENGTH,
) -> np.ndarray:
    """Pad or trim *X* to exactly one sequence of shape (1, sequence_length, n_features)."""
    n_features = X.shape[1] if X.ndim == 2 else X.shape[0]

    if X.ndim == 1:
        X = X.reshape(1, -1)

    if len(X) >= sequence_length:
        window = X[-sequence_length:]
    else:
        pad = np.zeros((sequence_length - len(X), n_features), dtype=np.float32)
        window = np.vstack([pad, X])

    return window.reshape(1, sequence_length, n_features).astype(np.float32)
