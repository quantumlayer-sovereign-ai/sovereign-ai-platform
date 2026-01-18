"""
Multi-Pass Code Generation Pipeline
====================================
Orchestrates high-quality code generation through multiple passes:

1. Template Retrieval (RAG) - Get relevant code templates
2. Architecture Design - Plan the project structure
3. Code Generation - Generate code using templates as context
4. Code Review - Fix issues and ensure consistency
5. Post-Processing - Auto-fix remaining issues
"""

from pathlib import Path
from typing import Any, Optional

import structlog

from .code_reviewer import CodeReviewer
from .post_processor import CodePostProcessor
from .project_generator import ProjectGenerator
from .models import CodeBlock, ProjectFile, ProjectManifest

logger = structlog.get_logger()


class GenerationPipeline:
    """
    Multi-pass code generation pipeline.

    Orchestrates:
    1. RAG retrieval for templates
    2. Architect agent for structure
    3. Coder agent for implementation
    4. Reviewer for fixes
    5. Post-processor for final cleanup
    """

    def __init__(
        self,
        model_interface: Any,
        rag_pipeline: Optional[Any] = None,
        project_base_dir: str = "projects",
    ):
        self.model = model_interface
        self.rag = rag_pipeline
        self.project_generator = ProjectGenerator(base_dir=project_base_dir)
        self.reviewer = CodeReviewer()

    async def generate(
        self,
        task: str,
        task_id: str,
        vertical: str = "fintech",
        agents_used: Optional[list[str]] = None,
    ) -> dict:
        """
        Execute the full generation pipeline.

        Args:
            task: Task description
            task_id: Unique task identifier
            vertical: Industry vertical for context
            agents_used: List of agents that contributed

        Returns:
            dict with generation results including project manifest
        """
        agents_used = agents_used or []
        context = {}

        # Phase 1: Retrieve relevant templates
        if self.rag:
            templates = await self._retrieve_templates(task, vertical)
            context["templates"] = templates
            logger.info("templates_retrieved", count=len(templates))

        # Phase 2: Generate code (would call model here)
        # This is handled by the orchestrator calling agents
        # We receive the results after agent execution

        # Phase 3 & 4 are handled by project_generator with post-processor

        return {
            "context": context,
            "pipeline_version": "1.0",
        }

    async def _retrieve_templates(
        self,
        task: str,
        vertical: str,
    ) -> list[dict]:
        """Retrieve relevant code templates from RAG."""
        templates = []

        # Determine which collections to search
        collections = ["fastapi_templates", "common_templates"]
        if vertical == "fintech":
            collections.append("fintech_templates")

        for collection in collections:
            try:
                results = await self.rag.search(
                    query=task,
                    collection_name=collection,
                    n_results=2,
                )
                templates.extend(results)
            except Exception as e:
                logger.warning(f"Failed to search {collection}: {e}")

        return templates

    def create_enhanced_prompt(
        self,
        task: str,
        templates: list[dict],
        vertical: str = "fintech",
    ) -> str:
        """
        Create an enhanced prompt with RAG context.

        This prompt includes:
        - Retrieved code templates as examples
        - Explicit instructions for code quality
        - Project structure requirements
        """
        template_context = ""
        if templates:
            template_context = "\n\n## REFERENCE CODE EXAMPLES\n"
            template_context += "Use these as reference for patterns and style:\n\n"
            for i, tmpl in enumerate(templates[:3], 1):
                content = tmpl.get("content", "")[:1500]  # Limit size
                source = tmpl.get("metadata", {}).get("section", "unknown")
                template_context += f"### Example {i} ({source})\n```python\n{content}\n```\n\n"

        prompt = f"""## TASK
{task}

## REQUIREMENTS
Generate a complete, production-ready Python project with:

1. **Project Structure**:
   - app/main.py - FastAPI application entry point
   - app/config/settings.py - Pydantic v2 settings
   - app/models/schemas.py - Pydantic request/response models
   - app/services/ - Business logic
   - app/routers/ - API endpoints
   - requirements.txt - Dependencies

2. **Code Quality**:
   - Use Pydantic v2 syntax (pydantic_settings for BaseSettings)
   - Include ALL imports in EVERY file
   - Use type hints everywhere
   - Use Decimal for money (never float)
   - Include proper error handling

3. **Output Format**:
   - Use markdown headers: #### `app/path/to/file.py`
   - Followed by ```python code block

{template_context}

Generate the complete project now:
"""
        return prompt


class RAGEnhancedOrchestrator:
    """
    Extends the base orchestrator with RAG-enhanced generation.
    """

    def __init__(
        self,
        base_orchestrator: Any,
        rag_pipeline: Optional[Any] = None,
    ):
        self.orchestrator = base_orchestrator
        self.rag = rag_pipeline
        self.pipeline = GenerationPipeline(
            model_interface=base_orchestrator.model,
            rag_pipeline=rag_pipeline,
        )

    async def execute_with_rag(
        self,
        task: str,
        vertical: str = "fintech",
        **kwargs,
    ) -> dict:
        """
        Execute task with RAG-enhanced context.

        1. Retrieve relevant templates
        2. Enhance prompt with context
        3. Execute through orchestrator
        4. Review and post-process
        """
        # Get templates
        templates = []
        if self.rag:
            templates = await self.pipeline._retrieve_templates(task, vertical)

        # Create enhanced prompt
        enhanced_task = self.pipeline.create_enhanced_prompt(
            task=task,
            templates=templates,
            vertical=vertical,
        )

        # Execute through base orchestrator
        result = await self.orchestrator.execute(
            task=enhanced_task,
            vertical=vertical,
            **kwargs,
        )

        result["rag_templates_used"] = len(templates)
        return result


def enhance_agent_context(
    agent_prompt: str,
    templates: list[dict],
    vertical: str,
) -> str:
    """
    Enhance an agent's system prompt with RAG context.

    This can be used to inject relevant code examples into
    the agent's context before generation.
    """
    if not templates:
        return agent_prompt

    context = "\n\n## CODE REFERENCE EXAMPLES\n"
    context += "Use these high-quality examples as reference:\n\n"

    for tmpl in templates[:2]:
        content = tmpl.get("content", "")[:1000]
        source = tmpl.get("metadata", {}).get("template_name", "unknown")
        context += f"### From {source}:\n```python\n{content}\n```\n\n"

    return agent_prompt + context
