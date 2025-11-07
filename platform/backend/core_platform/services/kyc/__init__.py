"""
KYC service helpers.

Currently exposes the SubmitKYCCommand that orchestrates Dojah lookups and
persists normalized onboarding metadata.
"""

from .submit_kyc_command import SubmitKYCCommand

__all__ = ["SubmitKYCCommand"]

