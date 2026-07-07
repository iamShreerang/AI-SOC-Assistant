"""Base dataset loader interface."""

from abc import ABC, abstractmethod
import pandas as pd


class BaseDatasetLoader(ABC):
    """All dataset loaders must implement this interface."""

    @abstractmethod
    def load(self, path: str) -> pd.DataFrame:
        """Load raw CSV/parquet from *path* and return a DataFrame."""

    @abstractmethod
    def get_label_column(self) -> str:
        """Return the name of the label column in the raw file."""

    def load_and_normalise(self, path: str) -> pd.DataFrame:
        """Load then rename label column to 'label' and add binary 'is_attack'."""
        df = self.load(path)
        label_col = self.get_label_column()
        if label_col != "label":
            df = df.rename(columns={label_col: "label"})
        return df
