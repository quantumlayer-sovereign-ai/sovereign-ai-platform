"""
Project Output Module

Generates enterprise folder structures from agent outputs:
- Code extraction and organization
- Project manifest generation
- ZIP export functionality
"""

from .models import CodeBlock, ProjectFile, ProjectManifest
from .project_generator import ProjectGenerator

__all__ = [
    "CodeBlock",
    "ProjectFile",
    "ProjectManifest",
    "ProjectGenerator",
]
