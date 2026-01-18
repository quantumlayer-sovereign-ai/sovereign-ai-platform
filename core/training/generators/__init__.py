"""
Training Data Generators

Domain-specific generators for creating instruction-tuning datasets
from knowledge documents.

Supports multiple regions:
- India (default): RBI, SEBI, DPDP, PCI-DSS
- EU: GDPR, PSD2, eIDAS, DORA, PCI-DSS
- UK: UK GDPR, FCA, PSR, PCI-DSS
"""

from .base import BaseGenerator, TrainingSample
from .coder import CoderGenerator
from .security import SecurityGenerator
from .compliance import ComplianceGenerator
from .architect import ArchitectGenerator
from .tester import TesterGenerator

# EU generators
from .eu import EUCoderGenerator, EUComplianceGenerator, EUSecurityGenerator

# UK generators
from .uk import UKCoderGenerator, UKComplianceGenerator, UKSecurityGenerator

# Generator registry - maps role names to generator classes
GENERATORS = {
    # India roles (default)
    "fintech_coder": CoderGenerator,
    "fintech_security": SecurityGenerator,
    "fintech_compliance": ComplianceGenerator,
    "fintech_architect": ArchitectGenerator,
    "fintech_tester": TesterGenerator,

    # EU roles
    "eu_fintech_coder": EUCoderGenerator,
    "eu_fintech_security": EUSecurityGenerator,
    "eu_fintech_compliance": EUComplianceGenerator,
    "eu_fintech_architect": EUCoderGenerator,  # Uses coder for architecture patterns
    "eu_fintech_tester": EUSecurityGenerator,  # Uses security for test patterns

    # UK roles
    "uk_fintech_coder": UKCoderGenerator,
    "uk_fintech_security": UKSecurityGenerator,
    "uk_fintech_compliance": UKComplianceGenerator,
    "uk_fintech_architect": UKCoderGenerator,  # Uses coder for architecture patterns
    "uk_fintech_tester": UKSecurityGenerator,  # Uses security for test patterns
}


def get_generator(role_name: str) -> BaseGenerator:
    """Get generator instance for a role"""
    if role_name not in GENERATORS:
        raise ValueError(f"No generator for role: {role_name}")
    return GENERATORS[role_name]()


def get_generators_for_region(region: str) -> dict[str, type[BaseGenerator]]:
    """Get all generators for a specific region"""
    region_lower = region.lower()
    prefix_map = {
        "india": "",
        "eu": "eu_",
        "uk": "uk_",
    }
    prefix = prefix_map.get(region_lower, "")

    if prefix == "":
        # India roles don't have prefix
        return {k: v for k, v in GENERATORS.items() if not k.startswith(("eu_", "uk_"))}
    else:
        return {k: v for k, v in GENERATORS.items() if k.startswith(prefix)}


__all__ = [
    # Base classes
    "BaseGenerator",
    "TrainingSample",
    # India generators
    "CoderGenerator",
    "SecurityGenerator",
    "ComplianceGenerator",
    "ArchitectGenerator",
    "TesterGenerator",
    # EU generators
    "EUCoderGenerator",
    "EUComplianceGenerator",
    "EUSecurityGenerator",
    # UK generators
    "UKCoderGenerator",
    "UKComplianceGenerator",
    "UKSecurityGenerator",
    # Registry
    "GENERATORS",
    "get_generator",
    "get_generators_for_region",
]
