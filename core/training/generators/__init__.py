"""
Training Data Generators

Domain-specific generators for creating instruction-tuning datasets
from knowledge documents.
"""

from .base import BaseGenerator, TrainingSample
from .coder import CoderGenerator
from .security import SecurityGenerator
from .compliance import ComplianceGenerator
from .architect import ArchitectGenerator
from .tester import TesterGenerator

# Generator registry
GENERATORS = {
    "fintech_coder": CoderGenerator,
    "fintech_security": SecurityGenerator,
    "fintech_compliance": ComplianceGenerator,
    "fintech_architect": ArchitectGenerator,
    "fintech_tester": TesterGenerator,
}


def get_generator(role_name: str) -> BaseGenerator:
    """Get generator instance for a role"""
    if role_name not in GENERATORS:
        raise ValueError(f"No generator for role: {role_name}")
    return GENERATORS[role_name]()


__all__ = [
    "BaseGenerator",
    "TrainingSample",
    "CoderGenerator",
    "SecurityGenerator",
    "ComplianceGenerator",
    "ArchitectGenerator",
    "TesterGenerator",
    "GENERATORS",
    "get_generator",
]
