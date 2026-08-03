"""Utility to clear PySpark streaming checkpoint state and reset logging stream."""
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from streaming.config import SPARK_CHECKPOINT_DIR

def clean_checkpoint():
    checkpoint_dir = Path(SPARK_CHECKPOINT_DIR)
    if checkpoint_dir.exists():
        print(f"Cleaning PySpark checkpoint directory: {checkpoint_dir}")
        try:
            shutil.rmtree(checkpoint_dir)
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            print("Checkpoint state successfully cleared.")
        except Exception as e:
            print(f"Error clearing checkpoint: {e}")
    else:
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created fresh checkpoint directory: {checkpoint_dir}")

if __name__ == "__main__":
    clean_checkpoint()
