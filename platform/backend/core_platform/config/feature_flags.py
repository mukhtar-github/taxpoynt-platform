"""Feature flag helpers for the TaxPoynt platform."""
import logging
from functools import lru_cache
from typing import Dict

from .environment import get_config

logger = logging.getLogger(__name__)
_IRN_FLAG_WARNING_EMITTED = False


@lru_cache(maxsize=1)
def get_feature_flags() -> Dict[str, bool]:
    """Return cached feature flags from the environment configuration."""
    return dict(get_config().get_feature_flags())


def is_firs_remote_irn_enabled() -> bool:
    """
    Historical flag indicating whether IRNs should be issued remotely by FIRS.

    This behaviour is deprecated – SIs now generate IRNs locally before submission.
    The function remains for backward compatibility but always returns ``False``.
    """

    global _IRN_FLAG_WARNING_EMITTED
    if get_feature_flags().get("FIRS_REMOTE_IRN", False) and not _IRN_FLAG_WARNING_EMITTED:
        logger.warning(
            "FIRS_REMOTE_IRN flag is deprecated and ignored; SIs must generate IRNs locally."
        )
        _IRN_FLAG_WARNING_EMITTED = True
    return False
