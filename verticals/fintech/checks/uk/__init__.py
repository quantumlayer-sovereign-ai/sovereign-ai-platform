"""
UK-specific Compliance Checks

Covers:
- UK GDPR (Data Protection Act 2018)
- FCA (Financial Conduct Authority)
- PSR (Payment Systems Regulator)
"""

from .uk_gdpr import UKGDPRChecker, UK_GDPR_CHECKS
from .fca import FCAChecker, FCA_CHECKS
from .psr import PSRChecker, PSR_CHECKS

__all__ = [
    "UKGDPRChecker",
    "UK_GDPR_CHECKS",
    "FCAChecker",
    "FCA_CHECKS",
    "PSRChecker",
    "PSR_CHECKS",
]
