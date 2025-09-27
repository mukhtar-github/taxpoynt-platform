"""Feature flag helpers for the TaxPoynt platform."""
from functools import lru_cache
from typing import Dict

from .environment import get_config


@lru_cache(maxsize=1)
def get_feature_flags() -> Dict[str, bool]:
    """Return cached feature flags from the environment configuration."""
    return dict(get_config().get_feature_flags())


def is_firs_remote_irn_enabled() -> bool:
    """Whether the platform should rely on FIRS-issued IRNs and stamps."""
    return bool(get_feature_flags().get("FIRS_REMOTE_IRN", False))
