"""
Project Output Module

Generates enterprise folder structures from agent outputs:
- Code extraction and organization
- Project manifest generation
- ZIP export functionality
- Post-processing for auto-fixing code issues
- Code review for consistency
- Multi-pass generation pipeline
"""

from .models import CodeBlock, ProjectFile, ProjectManifest
from .project_generator import ProjectGenerator
from .post_processor import CodePostProcessor, post_process_project
from .code_reviewer import CodeReviewer, create_review_prompt
from .generation_pipeline import (
    GenerationPipeline,
    RAGEnhancedOrchestrator,
    enhance_agent_context,
)

__all__ = [
    # Models
    "CodeBlock",
    "ProjectFile",
    "ProjectManifest",
    # Generator
    "ProjectGenerator",
    # Post-processor
    "CodePostProcessor",
    "post_process_project",
    # Code reviewer
    "CodeReviewer",
    "create_review_prompt",
    # Generation pipeline
    "GenerationPipeline",
    "RAGEnhancedOrchestrator",
    "enhance_agent_context",
]
