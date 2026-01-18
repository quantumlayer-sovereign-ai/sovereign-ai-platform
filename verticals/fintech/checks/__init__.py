"""
FinTech Compliance Checks

Modular compliance checking for multiple regions:
- Global: PCI-DSS
- India: RBI, DPDP
- EU: GDPR, PSD2, eIDAS, DORA
- UK: UK GDPR, FCA, PSR
"""

from .base import (
    Severity,
    ComplianceCheck,
    ComplianceIssue,
    ComplianceReport,
    BaseComplianceChecker,
    ComplianceCheckerRegistry,
    register_checker,
)

# Import all checkers to register them
from .pci_dss import PCIDSSChecker, PCI_DSS_CHECKS
from .india import RBIChecker, RBI_CHECKS, DPDPChecker, DPDP_CHECKS
from .eu import (
    GDPRChecker, GDPR_CHECKS,
    PSD2Checker, PSD2_CHECKS,
    EIDASChecker, EIDAS_CHECKS,
    DORAChecker, DORA_CHECKS,
)
from .uk import (
    UKGDPRChecker, UK_GDPR_CHECKS,
    FCAChecker, FCA_CHECKS,
    PSRChecker, PSR_CHECKS,
)

# Region to standards mapping
REGION_STANDARDS = {
    "india": ["pci_dss", "rbi", "dpdp"],
    "eu": ["pci_dss", "gdpr", "psd2", "eidas", "dora"],
    "uk": ["pci_dss", "uk_gdpr", "fca", "psr"],
}


def get_checkers_for_region(region: str) -> list[BaseComplianceChecker]:
    """
    Get all compliance checkers for a specific region

    Args:
        region: Region name (india, eu, uk)

    Returns:
        List of checker instances for the region
    """
    standards = REGION_STANDARDS.get(region.lower(), [])
    checkers = []

    for standard in standards:
        checker = ComplianceCheckerRegistry.get(standard)
        if checker:
            checkers.append(checker)

    return checkers


def check_code_for_region(
    code: str,
    region: str,
    filename: str = "code"
) -> ComplianceReport:
    """
    Check code for compliance with all standards in a region

    Args:
        code: Source code to check
        region: Region name (india, eu, uk)
        filename: Name of the file being checked

    Returns:
        Aggregated ComplianceReport
    """
    checkers = get_checkers_for_region(region)
    all_issues: list[ComplianceIssue] = []
    standards_checked: list[str] = []

    for checker in checkers:
        issues = checker.check_code(code, filename)
        all_issues.extend(issues)
        standards_checked.append(checker.standard_name)

    summary = BaseComplianceChecker.generate_summary(all_issues)
    recommendations = list({i.remediation for i in all_issues})
    passed = summary["critical"] == 0 and summary["high"] == 0

    return ComplianceReport(
        passed=passed,
        issues=all_issues,
        summary=summary,
        recommendations=recommendations,
        standards_checked=standards_checked,
    )


__all__ = [
    # Base types
    "Severity",
    "ComplianceCheck",
    "ComplianceIssue",
    "ComplianceReport",
    "BaseComplianceChecker",
    "ComplianceCheckerRegistry",
    "register_checker",
    # Global
    "PCIDSSChecker",
    "PCI_DSS_CHECKS",
    # India
    "RBIChecker",
    "RBI_CHECKS",
    "DPDPChecker",
    "DPDP_CHECKS",
    # EU
    "GDPRChecker",
    "GDPR_CHECKS",
    "PSD2Checker",
    "PSD2_CHECKS",
    "EIDASChecker",
    "EIDAS_CHECKS",
    "DORAChecker",
    "DORA_CHECKS",
    # UK
    "UKGDPRChecker",
    "UK_GDPR_CHECKS",
    "FCAChecker",
    "FCA_CHECKS",
    "PSRChecker",
    "PSR_CHECKS",
    # Utilities
    "REGION_STANDARDS",
    "get_checkers_for_region",
    "check_code_for_region",
]
