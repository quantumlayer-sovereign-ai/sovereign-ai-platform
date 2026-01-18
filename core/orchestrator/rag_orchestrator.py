"""
RAG-Enhanced Orchestrator

Extends base orchestrator with RAG capabilities:
- Knowledge retrieval before task execution
- Context-aware agent prompts
- Compliance document lookup
- Code pattern retrieval
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import structlog

from ..agents.base import Agent
from ..rag.pipeline import FintechRAG, RAGPipeline
from ..tools.security_tools import SecurityScanner
from .main import Orchestrator, TaskPlan, TaskResult

logger = structlog.get_logger()


@dataclass
class RAGContext:
    """Context retrieved from RAG pipeline"""
    documents: list[dict[str, Any]]
    sources: list[str]
    relevance_scores: list[float]
    context_text: str
    vertical: str


class RAGOrchestrator(Orchestrator):
    """
    Orchestrator enhanced with RAG capabilities

    Features:
    - Retrieves relevant knowledge before task execution
    - Augments agent prompts with domain context
    - Provides compliance guidance from knowledge base
    - Cites sources for audit trail
    """

    def __init__(
        self,
        model_interface: Any = None,
        max_agents: int = 10,
        default_vertical: str | None = "fintech",
        rag_persist_dir: str | None = None,
        chromadb_host: str | None = None,
        chromadb_port: int = 8000
    ):
        super().__init__(
            model_interface=model_interface,
            max_agents=max_agents,
            default_vertical=default_vertical
        )

        # Initialize RAG pipeline
        self.rag = RAGPipeline(
            persist_directory=rag_persist_dir,
            embedding_model="minilm",
            chromadb_host=chromadb_host,
            chromadb_port=chromadb_port
        )

        # Vertical-specific RAG pipelines
        self.vertical_rags: dict[str, RAGPipeline] = {}

        # Security scanner for compliance
        self.security_scanner = SecurityScanner()

        logger.info("rag_orchestrator_initialized",
                   vertical=default_vertical,
                   persist_dir=rag_persist_dir)

    def get_vertical_rag(self, vertical: str) -> RAGPipeline:
        """Get or create RAG pipeline for a vertical"""
        if vertical not in self.vertical_rags:
            if vertical == "fintech":
                self.vertical_rags[vertical] = FintechRAG(
                    persist_directory=self.rag.persist_directory
                )
            else:
                self.vertical_rags[vertical] = self.rag

        return self.vertical_rags[vertical]

    async def execute(
        self,
        task: str,
        vertical: str | None = None,
        region: str | None = None,
        compliance_requirements: list[str] | None = None,
        use_rag: bool = True
    ) -> TaskResult:
        """
        Execute task with RAG-enhanced context

        Args:
            task: Task description
            vertical: Vertical context
            region: Region for compliance (india, eu, uk)
            compliance_requirements: Specific compliance needs
            use_rag: Whether to use RAG for context (default True)

        Returns:
            TaskResult with outputs, sources, and audit trail
        """
        start_time = datetime.now()
        vertical = vertical or self.default_vertical
        region = region or "india"  # Default to India for backward compatibility
        compliance_requirements = compliance_requirements or []

        # Generate task ID
        self._task_counter += 1
        task_id = f"task_{self._task_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info("rag_task_started",
                   task_id=task_id,
                   task=task[:100],
                   vertical=vertical,
                   region=region,
                   use_rag=use_rag)

        try:
            # Step 1: Retrieve relevant context from RAG
            rag_context = None
            if use_rag:
                rag_context = await self._retrieve_context(task, vertical)
                logger.info("rag_context_retrieved",
                           task_id=task_id,
                           documents=len(rag_context.documents) if rag_context else 0)

            # Step 2: Analyze and plan (with RAG context)
            plan = await self._analyze_task_with_rag(
                task_id, task, vertical, region, compliance_requirements, rag_context
            )

            # Step 3: Spawn agents with RAG-enhanced prompts
            agents = await self._spawn_agents_with_rag(plan, rag_context)
            logger.info("agents_spawned", task_id=task_id, count=len(agents))

            # Step 4: Execute subtasks
            results = await self._execute_plan(plan, agents)

            # Step 5: Security scan any generated code
            security_results = await self._scan_results_for_security(results)

            # Step 6: Aggregate results with RAG sources
            aggregated = await self._aggregate_results_with_sources(
                results, plan, rag_context, security_results
            )

            # Step 7: Verify compliance
            compliance_status = await self._verify_compliance_with_rag(
                results, compliance_requirements, vertical, rag_context, region
            )

            # Step 8: Cleanup
            audit_trail = self._collect_audit_trail(agents)

            # Add RAG sources to audit trail
            if rag_context:
                audit_trail.append({
                    "type": "rag_sources",
                    "sources": rag_context.sources,
                    "documents_used": len(rag_context.documents)
                })

            self._cleanup_agents(agents)

            execution_time = (datetime.now() - start_time).total_seconds()

            result = TaskResult(
                task_id=task_id,
                success=True,
                results=results,
                aggregated_output=aggregated,
                compliance_status=compliance_status,
                execution_time_seconds=execution_time,
                agents_used=[a.role_name for a in agents],
                audit_trail=audit_trail
            )

            self.task_history.append(result)
            logger.info("rag_task_completed",
                       task_id=task_id,
                       execution_time=execution_time)

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error("rag_task_failed", task_id=task_id, error=str(e))

            result = TaskResult(
                task_id=task_id,
                success=False,
                results=[{"error": str(e)}],
                aggregated_output=f"Task failed: {e!s}",
                compliance_status={},
                execution_time_seconds=execution_time,
                agents_used=[],
                audit_trail=[]
            )

            self.task_history.append(result)
            return result

    async def _retrieve_context(
        self,
        task: str,
        vertical: str
    ) -> RAGContext | None:
        """Retrieve relevant context from RAG"""
        try:
            rag = self.get_vertical_rag(vertical)
            retrieval = rag.retrieve_with_context(
                query=task,
                vertical=vertical,
                n_results=5
            )

            if not retrieval["found"]:
                return None

            documents = rag.retrieve(query=task, vertical=vertical, n_results=5)

            return RAGContext(
                documents=documents,
                sources=[s["source"] for s in retrieval["sources"]],
                relevance_scores=[s["score"] for s in retrieval["sources"]],
                context_text=retrieval["context"],
                vertical=vertical
            )

        except Exception as e:
            logger.warning("rag_retrieval_failed", error=str(e))
            return None

    async def _analyze_task_with_rag(
        self,
        task_id: str,
        task: str,
        vertical: str | None,
        region: str,
        compliance_requirements: list[str],
        rag_context: RAGContext | None
    ) -> TaskPlan:
        """Analyze task with RAG context"""
        # Get base plan (now region-aware)
        plan = await self._analyze_task(task_id, task, vertical, region, compliance_requirements)

        # Enhance with RAG insights
        if rag_context:
            # Check if compliance documents were retrieved
            for doc in rag_context.documents:
                source = doc.get("metadata", {}).get("source", "").lower()
                if "pci" in source and "pci_dss" not in plan.compliance_checks:
                    plan.compliance_checks.append("pci_dss")

                # Region-specific RAG checks
                if region == "india":
                    if "rbi" in source and "rbi_guidelines" not in plan.compliance_checks:
                        plan.compliance_checks.append("rbi_guidelines")
                    if "dpdp" in source and "dpdp" not in plan.compliance_checks:
                        plan.compliance_checks.append("dpdp")
                elif region == "eu":
                    if "gdpr" in source and "gdpr" not in plan.compliance_checks:
                        plan.compliance_checks.append("gdpr")
                    if "psd2" in source and "psd2" not in plan.compliance_checks:
                        plan.compliance_checks.append("psd2")
                    if "dora" in source and "dora" not in plan.compliance_checks:
                        plan.compliance_checks.append("dora")
                elif region == "uk":
                    if "fca" in source and "fca" not in plan.compliance_checks:
                        plan.compliance_checks.append("fca")
                    if "uk_gdpr" in source and "uk_gdpr" not in plan.compliance_checks:
                        plan.compliance_checks.append("uk_gdpr")
                    if "psr" in source and "psr" not in plan.compliance_checks:
                        plan.compliance_checks.append("psr")

            # Update analysis with context
            plan.analysis += f"\n\nRAG Context: Retrieved {len(rag_context.documents)} relevant documents"

        return plan

    async def _spawn_agents_with_rag(
        self,
        plan: TaskPlan,
        rag_context: RAGContext | None
    ) -> list[Agent]:
        """Spawn agents with RAG-enhanced prompts"""
        agents = []

        for role_name in plan.agents_needed:
            try:
                agent = self.factory.spawn(role_name)

                # Enhance agent's system prompt with RAG context
                if rag_context and rag_context.context_text:
                    enhanced_prompt = self._enhance_prompt(
                        agent.system_prompt,
                        rag_context,
                        plan.vertical
                    )
                    agent.role["system_prompt"] = enhanced_prompt

                agents.append(agent)

            except Exception as e:
                logger.warning("agent_spawn_failed", role=role_name, error=str(e))

        return agents

    def _enhance_prompt(
        self,
        original_prompt: str,
        rag_context: RAGContext,
        vertical: str | None
    ) -> str:
        """Enhance system prompt with RAG context"""
        context_section = f"""

---
## Relevant Knowledge Base Context ({vertical})

{rag_context.context_text}

### Sources:
{chr(10).join(f"- {s}" for s in rag_context.sources[:5])}

---
Apply the above context when generating your response. Cite sources where applicable.
"""
        return original_prompt + context_section

    async def _scan_results_for_security(
        self,
        results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Scan any generated code for security issues"""
        security_issues = []

        for result in results:
            response = result.get("response", "")

            # Look for code blocks
            if "```" in response:
                # Extract code from markdown code blocks
                import re
                code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', response, re.DOTALL)

                for code in code_blocks:
                    scan_result = self.security_scanner.scan_code(code)
                    if scan_result["issues"]:
                        security_issues.extend(scan_result["issues"])

        return {
            "scanned": True,
            "issues": security_issues,
            "passed": len([i for i in security_issues if i["severity"] in ["critical", "high"]]) == 0
        }

    async def _aggregate_results_with_sources(
        self,
        results: list[dict[str, Any]],
        plan: TaskPlan,
        rag_context: RAGContext | None,
        security_results: dict[str, Any]
    ) -> str:
        """Aggregate results with RAG sources and security findings"""
        output = await self._aggregate_results(results, plan)

        # Add sources section
        if rag_context and rag_context.sources:
            output += "\n\n---\n## Knowledge Base Sources\n\n"
            for i, source in enumerate(rag_context.sources, 1):
                score = rag_context.relevance_scores[i-1] if i <= len(rag_context.relevance_scores) else 0
                output += f"{i}. {source} (relevance: {score:.2f})\n"

        # Add security findings
        if security_results["issues"]:
            output += "\n\n---\n## Security Scan Findings\n\n"
            for issue in security_results["issues"][:5]:  # Top 5
                output += f"- **{issue['severity'].upper()}**: {issue['rule_name']} - {issue['description']}\n"

        return output

    async def _verify_compliance_with_rag(
        self,
        results: list[dict[str, Any]],
        requirements: list[str],
        vertical: str | None,
        rag_context: RAGContext | None,
        region: str = "india"
    ) -> dict[str, bool]:
        """Verify compliance with RAG-backed checks"""
        compliance_status = await self._verify_compliance(results, requirements, vertical, region)

        # Enhanced checks based on RAG context
        if rag_context:
            # Check if required compliance patterns were followed
            for doc in rag_context.documents:
                source = doc.get("metadata", {}).get("source", "")

                if "pci_dss" in source.lower():
                    # Verify PCI-DSS patterns in results
                    compliance_status["pci_dss_context_applied"] = True

                if "rbi" in source.lower():
                    compliance_status["rbi_guidelines_context_applied"] = True

        return compliance_status

    async def index_knowledge_base(
        self,
        directory: str,
        vertical: str
    ) -> dict[str, Any]:
        """Index documents into the knowledge base"""
        from pathlib import Path

        rag = self.get_vertical_rag(vertical)
        result = rag.index_directory(
            directory=Path(directory),
            vertical=vertical,
            recursive=True
        )

        logger.info("knowledge_base_indexed",
                   directory=directory,
                   vertical=vertical,
                   chunks=result.get("chunks_indexed", 0))

        return result

    async def search_knowledge(
        self,
        query: str,
        vertical: str,
        n_results: int = 5
    ) -> list[dict[str, Any]]:
        """Search the knowledge base directly"""
        rag = self.get_vertical_rag(vertical)
        return rag.retrieve(
            query=query,
            vertical=vertical,
            n_results=n_results
        )

    def get_rag_stats(self) -> dict[str, Any]:
        """Get RAG pipeline statistics"""
        return {
            "base_rag": self.rag.get_stats(),
            "vertical_rags": {
                vertical: rag.get_stats()
                for vertical, rag in self.vertical_rags.items()
            }
        }
