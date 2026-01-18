"""
FinTech Vertical - Specialized agents for financial technology

Regions Supported:
- India: RBI, SEBI, DPDP, PCI-DSS
- EU: GDPR, PSD2, eIDAS, DORA, PCI-DSS
- UK: UK GDPR, FCA, PSR, PCI-DSS

Specializations:
- Payment gateway integration
- Banking APIs (UPI, IMPS, RTGS, NEFT, SEPA, Faster Payments)
- KYC/AML compliance
- Fraud detection
- Financial data security
"""

from .compliance import (
    PCI_DSS_CHECKS,
    RBI_CHECKS,
    DPDP_CHECKS,
    GDPR_CHECKS,
    PSD2_CHECKS,
    FCA_CHECKS,
    UK_GDPR_CHECKS,
    REGION_CHECKS,
    ComplianceChecker,
    ComplianceReport,
    ComplianceIssue,
    Severity,
)
from .region import (
    FinTechRegion,
    RegionConfig,
    REGION_CONFIGS,
    get_region_config,
    get_compliance_standards,
    get_payment_schemes,
    get_region_roles,
    DEFAULT_REGION,
)
from .roles import FINTECH_ROLES, register_fintech_roles

__all__ = [
    # Compliance
    "FINTECH_ROLES",
    "PCI_DSS_CHECKS",
    "RBI_CHECKS",
    "DPDP_CHECKS",
    "GDPR_CHECKS",
    "PSD2_CHECKS",
    "FCA_CHECKS",
    "UK_GDPR_CHECKS",
    "REGION_CHECKS",
    "ComplianceChecker",
    "ComplianceReport",
    "ComplianceIssue",
    "Severity",
    # Region
    "FinTechRegion",
    "RegionConfig",
    "REGION_CONFIGS",
    "get_region_config",
    "get_compliance_standards",
    "get_payment_schemes",
    "get_region_roles",
    "DEFAULT_REGION",
    # Roles
    "register_fintech_roles",
]
