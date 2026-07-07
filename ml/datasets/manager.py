"""Unified dataset manager.

Handles loading individual or all datasets, schema alignment,
and dataset metadata tracking. Does not replace individual loaders.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from ml.config import DATA_DIR, DATASET_FILENAMES
from ml.datasets.registry import get_loader, REGISTRY
from ml.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DatasetMeta:
    name: str
    path: str
    rows: int
    columns: int
    label_distribution: Dict[str, int]
    loaded: bool = True
    error: Optional[str] = None


@dataclass
class LoadResult:
    combined: pd.DataFrame
    metadata: List[DatasetMeta]
    loaded_names: List[str]
    failed_names: List[str] = field(default_factory=list)


class DatasetManager:
    """Load one, several, or all datasets into a single aligned DataFrame.

    Usage
    -----
    manager = DatasetManager()

    # Auto-discover and load all available datasets
    result = manager.load_all()

    # Load specific datasets by name → path mapping
    result = manager.load({"beth": "/data/beth.csv", "unsw_nb15": "/data/unsw.csv"})

    # Load a single dataset
    df, meta = manager.load_single("unsw_nb15", "/data/unsw.csv")
    """

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self.data_dir = data_dir
        self._metadata: List[DatasetMeta] = []

    # ── Public API ────────────────────────────────────────────────────────────

    def load_all(self) -> LoadResult:
        """Auto-discover all known datasets in data_dir and load them."""
        discovered = self._discover()
        if not discovered:
            logger.warning("No datasets found in %s", self.data_dir)
            return LoadResult(
                combined=pd.DataFrame(),
                metadata=[],
                loaded_names=[],
                failed_names=list(REGISTRY.keys()),
            )
        return self.load(discovered)

    def load(self, dataset_paths: Dict[str, str]) -> LoadResult:
        """Load and combine datasets from an explicit name → path mapping.

        Datasets that fail to load are skipped; training continues with
        the remaining valid datasets.
        """
        frames: List[pd.DataFrame] = []
        metadata: List[DatasetMeta] = []
        loaded_names: List[str] = []
        failed_names: List[str] = []

        for name, path in dataset_paths.items():
            try:
                df, meta = self.load_single(name, path)
                df["_source"] = name
                frames.append(df)
                metadata.append(meta)
                loaded_names.append(name)
            except Exception as exc:
                logger.error("Failed to load dataset '%s' from %s: %s", name, path, exc)
                failed_names.append(name)
                metadata.append(DatasetMeta(
                    name=name, path=path, rows=0, columns=0,
                    label_distribution={}, loaded=False, error=str(exc),
                ))

        if not frames:
            raise RuntimeError(
                f"All datasets failed to load: {failed_names}. "
                "Check DATA_DIR and file names."
            )

        combined = self._align_and_combine(frames)
        self._metadata = metadata

        logger.info(
            "Loaded %d datasets (%d rows total). Failed: %s",
            len(loaded_names), len(combined), failed_names or "none",
        )
        return LoadResult(
            combined=combined,
            metadata=metadata,
            loaded_names=loaded_names,
            failed_names=failed_names,
        )

    def load_single(self, name: str, path: str) -> tuple[pd.DataFrame, DatasetMeta]:
        """Load one dataset and return (DataFrame, DatasetMeta)."""
        loader = get_loader(name)
        df = loader.load_and_normalise(path)

        label_dist: Dict[str, int] = {}
        if "label" in df.columns:
            label_dist = df["label"].astype(str).value_counts().to_dict()

        meta = DatasetMeta(
            name=name,
            path=path,
            rows=len(df),
            columns=df.shape[1],
            label_distribution=label_dist,
        )
        logger.info(
            "Dataset '%s': %d rows, %d cols, labels=%s",
            name, meta.rows, meta.columns, label_dist,
        )
        return df, meta

    @property
    def metadata(self) -> List[DatasetMeta]:
        return self._metadata

    def summary(self) -> Dict:
        """Return a summary dict of all loaded datasets."""
        return {
            m.name: {
                "rows": m.rows,
                "columns": m.columns,
                "loaded": m.loaded,
                "error": m.error,
                "label_distribution": m.label_distribution,
            }
            for m in self._metadata
        }

    # ── Private ───────────────────────────────────────────────────────────────

    def _discover(self) -> Dict[str, str]:
        """Scan data_dir for known dataset files/dirs and return name -> path mapping."""
        found: Dict[str, str] = {}
        for name, candidates in DATASET_FILENAMES.items():
            for fname in candidates:
                p = self.data_dir / fname
                if p.exists():
                    found[name] = str(p)
                    logger.info("Discovered dataset '%s' at %s", name, p)
                    break
            else:
                logger.warning("Dataset '%s' not found in %s (tried: %s)",
                               name, self.data_dir, candidates)
        return found

    @staticmethod
    def _align_and_combine(frames: List[pd.DataFrame]) -> pd.DataFrame:
        """Outer-join all frames on columns, fill missing with 0."""
        combined = pd.concat(frames, ignore_index=True, sort=False)
        combined = combined.fillna(0)
        return combined
