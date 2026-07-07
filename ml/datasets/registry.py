"""Dataset registry — separate from __init__ to avoid circular imports."""

from ml.datasets.beth import BETHLoader
from ml.datasets.cic_ids2018 import CICIds2018Loader
from ml.datasets.dsrl_api2023 import DSRLApi2023Loader
from ml.datasets.unsw_nb15 import UNSWNb15Loader

REGISTRY = {
    "beth":         BETHLoader,
    "cic_ids2018":  CICIds2018Loader,
    "dsrl_api2023": DSRLApi2023Loader,
    "unsw_nb15":    UNSWNb15Loader,
}


def get_loader(name: str):
    """Return an instantiated loader for *name*."""
    if name not in REGISTRY:
        raise ValueError(f"Unknown dataset '{name}'. Available: {list(REGISTRY)}")
    return REGISTRY[name]()
