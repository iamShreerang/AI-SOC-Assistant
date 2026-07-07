"""Dataset registry and unified manager."""

from ml.datasets.registry import REGISTRY, get_loader
from ml.datasets.beth import BETHLoader
from ml.datasets.cic_ids2018 import CICIds2018Loader
from ml.datasets.dsrl_api2023 import DSRLApi2023Loader
from ml.datasets.unsw_nb15 import UNSWNb15Loader
from ml.datasets.manager import DatasetManager, DatasetMeta, LoadResult

__all__ = [
    "REGISTRY", "get_loader",
    "DatasetManager", "DatasetMeta", "LoadResult",
    "BETHLoader", "CICIds2018Loader", "DSRLApi2023Loader", "UNSWNb15Loader",
]
