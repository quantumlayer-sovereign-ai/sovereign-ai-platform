"""
FinTech Vertical - Specialized agents for financial technology

Compliance:
- PCI-DSS (Payment Card Industry Data Security Standard)
- RBI (Reserve Bank of India) guidelines
- SEBI (Securities and Exchange Board of India) regulations
- DPDP Act (Digital Personal Data Protection)

Specializations:
- Payment gateway integration
- Banking APIs (UPI, IMPS, RTGS, NEFT)
- KYC/AML compliance
- Fraud detection
- Financial data security
"""

from .roles import FINTECH_ROLES, register_fintech_roles
from .compliance import ComplianceChecker, PCI_DSS_CHECKS, RBI_CHECKS

__all__ = [
    "FINTECH_ROLES",
    "register_fintech_roles",
    "ComplianceChecker",
    "PCI_DSS_CHECKS",
    "RBI_CHECKS"
]
