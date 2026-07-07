"""ML module configuration — loaded from environment / .env file."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
MODEL_DIR     = Path(os.getenv("ML_MODEL_DIR",    str(BASE_DIR / "saved_models")))
DATA_DIR      = Path(os.getenv("ML_DATA_DIR",     str(BASE_DIR / "data")))
ARTIFACT_DIR  = Path(os.getenv("ML_ARTIFACT_DIR", str(BASE_DIR / "artifacts")))
PLOT_DIR      = ARTIFACT_DIR / "plots"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
PLOT_DIR.mkdir(parents=True, exist_ok=True)

# ── Model versioning ──────────────────────────────────────────────────────────
MODEL_VERSION = os.getenv("ML_MODEL_VERSION", "v1")

# ── Preprocessing ─────────────────────────────────────────────────────────────
SEQUENCE_LENGTH = int(os.getenv("ML_SEQUENCE_LENGTH", "10"))
TEST_SIZE       = float(os.getenv("ML_TEST_SIZE", "0.2"))
RANDOM_STATE    = int(os.getenv("ML_RANDOM_STATE", "42"))

# ── Training ──────────────────────────────────────────────────────────────────
EPOCHS        = int(os.getenv("ML_EPOCHS", "50"))
BATCH_SIZE    = int(os.getenv("ML_BATCH_SIZE", "64"))
LEARNING_RATE = float(os.getenv("ML_LEARNING_RATE", "0.001"))
PATIENCE      = int(os.getenv("ML_PATIENCE", "10"))

# ── CNN-LSTM architecture ─────────────────────────────────────────────────────
CNN_FILTERS     = int(os.getenv("ML_CNN_FILTERS", "64"))
CNN_KERNEL_SIZE = int(os.getenv("ML_CNN_KERNEL_SIZE", "3"))
LSTM_UNITS      = int(os.getenv("ML_LSTM_UNITS", "128"))
DROPOUT_RATE    = float(os.getenv("ML_DROPOUT_RATE", "0.3"))
DENSE_UNITS     = int(os.getenv("ML_DENSE_UNITS", "64"))
USE_BATCH_NORM  = os.getenv("ML_USE_BATCH_NORM", "true").lower() == "true"

# ── Dataset label column names (per source) ───────────────────────────────────
LABEL_COLUMNS = {
    "beth":         "sus_label",
    "cic_ids2018":  "Label",
    "dsrl_api2023": "label",
    "unsw_nb15":    "label",
}

# ── Known dataset directories / files for auto-discovery inside DATA_DIR ────────
# Directories are listed before single files so the loader gets the full dataset.
DATASET_FILENAMES = {
    "beth":         ["BETH", "beth.csv", "BETH.csv"],
    "cic_ids2018":  ["CSE-CIC-IDS2018", "cic_ids2018.csv", "CIC-IDS-2018.csv"],
    "dsrl_api2023": ["DSRL-APT-2023", "dsrl_api2023.csv", "DSRL-APT-2023.csv"],
    "unsw_nb15":    ["UNSW-NB15", "unsw_nb15.csv", "UNSW-NB15.csv"],
}

# ── Per-dataset row sampling (None = no limit) ────────────────────────────────
# Large datasets are sampled to keep training tractable on CPU.
DATASET_MAX_ROWS = {
    "beth":         100_000,
    "cic_ids2018":  150_000,
    "dsrl_api2023": None,
    "unsw_nb15":    None,
}

# ── Attack label for binary classification ────────────────────────────────────
BENIGN_LABELS = {"BENIGN", "Normal", "normal", "Benign", "0", 0}

# ── Artifact file names ───────────────────────────────────────────────────────
PIPELINE_FILENAME  = "preprocessing_pipeline.joblib"
SCALER_FILENAME    = "scaler.joblib"
ENCODER_FILENAME   = "label_encoder.joblib"
FEATURES_FILENAME  = "feature_columns.json"
METADATA_FILENAME  = "metadata.json"
HISTORY_FILENAME   = "training_history.json"
