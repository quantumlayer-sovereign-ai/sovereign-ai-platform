"""
FinTech Region Configuration

Defines region-specific compliance standards, payment schemes, and configurations
for India, EU, and UK markets.
"""

from enum import Enum
from dataclasses import dataclass, field


class FinTechRegion(Enum):
    """Supported FinTech regions"""
    INDIA = "india"
    EU = "eu"
    UK = "uk"


@dataclass
class RegionConfig:
    """Configuration for a specific region"""
    compliance_standards: list[str]
    payment_schemes: list[str]
    currency: str
    data_residency: str
    regulatory_bodies: list[str]
    breach_notification_hours: int = 72
    cross_border_allowed: bool = False


# Region-specific configurations
REGION_CONFIGS: dict[FinTechRegion, RegionConfig] = {
    FinTechRegion.INDIA: RegionConfig(
        compliance_standards=["pci_dss", "rbi", "sebi", "dpdp"],
        payment_schemes=["UPI", "IMPS", "RTGS", "NEFT"],
        currency="INR",
        data_residency="india",
        regulatory_bodies=["RBI", "SEBI", "NPCI", "MEITY"],
        breach_notification_hours=72,
        cross_border_allowed=False  # Strict data localization
    ),
    FinTechRegion.EU: RegionConfig(
        compliance_standards=["pci_dss", "gdpr", "psd2", "eidas", "dora"],
        payment_schemes=["SEPA", "SEPA_INSTANT", "TARGET2"],
        currency="EUR",
        data_residency="eu",
        regulatory_bodies=["ECB", "EBA", "EDPB", "National DPAs"],
        breach_notification_hours=72,  # GDPR Article 33
        cross_border_allowed=True  # Within EU/EEA
    ),
    FinTechRegion.UK: RegionConfig(
        compliance_standards=["pci_dss", "uk_gdpr", "fca", "psr"],
        payment_schemes=["FASTER_PAYMENTS", "BACS", "CHAPS"],
        currency="GBP",
        data_residency="uk",
        regulatory_bodies=["FCA", "PRA", "ICO", "PSR"],
        breach_notification_hours=72,  # UK GDPR
        cross_border_allowed=True  # Adequacy decisions apply
    ),
}


def get_region_config(region: FinTechRegion | str) -> RegionConfig:
    """
    Get configuration for a specific region

    Args:
        region: Region enum or string name

    Returns:
        RegionConfig for the specified region

    Raises:
        ValueError: If region is not supported
    """
    if isinstance(region, str):
        try:
            region = FinTechRegion(region.lower())
        except ValueError:
            raise ValueError(
                f"Unknown region: {region}. Supported: {[r.value for r in FinTechRegion]}"
            )

    return REGION_CONFIGS[region]


def get_compliance_standards(region: FinTechRegion | str) -> list[str]:
    """Get compliance standards for a region"""
    config = get_region_config(region)
    return config.compliance_standards


def get_payment_schemes(region: FinTechRegion | str) -> list[str]:
    """Get payment schemes for a region"""
    config = get_region_config(region)
    return config.payment_schemes


def get_region_roles(region: FinTechRegion | str) -> list[str]:
    """
    Get role names for a specific region

    Args:
        region: Region enum or string

    Returns:
        List of role names for the region
    """
    if isinstance(region, str):
        region = FinTechRegion(region.lower())

    role_types = ["coder", "security", "compliance", "architect", "tester"]

    if region == FinTechRegion.INDIA:
        # India uses the base fintech_* roles
        return [f"fintech_{role}" for role in role_types]
    elif region == FinTechRegion.EU:
        return [f"eu_fintech_{role}" for role in role_types]
    elif region == FinTechRegion.UK:
        return [f"uk_fintech_{role}" for role in role_types]

    return []


# Default region for backward compatibility
DEFAULT_REGION = FinTechRegion.INDIA


__all__ = [
    "FinTechRegion",
    "RegionConfig",
    "REGION_CONFIGS",
    "get_region_config",
    "get_compliance_standards",
    "get_payment_schemes",
    "get_region_roles",
    "DEFAULT_REGION",
]
