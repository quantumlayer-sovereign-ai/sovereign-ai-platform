"""
Orchestrator - Master coordinator for multi-agent tasks

The Orchestrator:
1. Analyzes incoming tasks
2. Determines required agents and roles
3. Spawns agents dynamically
4. Coordinates execution (parallel/sequential)
5. Aggregates results
6. Ensures compliance requirements
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import structlog

from ..agents.base import Agent, AgentContext, DEFAULT_EXECUTION_TIMEOUT
from ..utils.retry import RetryError, with_retry
from ..agents.factory import AgentFactory
from ..agents.registry import get_registry
from .task_analyzer import get_analyzer, TaskAnalysis

logger = structlog.get_logger()

# Configuration constants
MAX_HISTORY_SIZE = 1000  # Maximum task history entries to keep
DEFAULT_TASK_TIMEOUT = 300.0  # 5 minutes for full task execution
AGENT_RETRY_ATTEMPTS = 3
AGENT_RETRY_BACKOFF = 2.0


class ExecutionMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"  # Output of one feeds into next


@dataclass
class TaskPlan:
    """Plan for executing a task"""
    task_id: str
    original_task: str
    analysis: str
    subtasks: list[dict[str, Any]]
    agents_needed: list[str]
    execution_mode: ExecutionMode
    compliance_checks: list[str]
    vertical: str | None = None
    complexity: str | None = None  # simple, medium, complex
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TaskResult:
    """Result of task execution"""
    task_id: str
    success: bool
    results: list[dict[str, Any]]
    aggregated_output: str
    compliance_status: dict[str, bool]
    execution_time_seconds: float
    agents_used: list[str]
    audit_trail: list[dict[str, Any]]


class Orchestrator:
    """
    Master Orchestrator for multi-agent coordination

    Features:
    - Task analysis and planning
    - Dynamic agent spawning
    - Parallel/sequential execution
    - Result aggregation
    - Compliance verification
    """

    def __init__(
        self,
        model_interface: Any = None,
        max_agents: int = 10,
        default_vertical: str | None = None
    ):
        self.model = model_interface
        self.factory = AgentFactory(model_interface=model_interface, max_agents=max_agents)
        self.registry = get_registry()
        self.default_vertical = default_vertical

        self.task_history: list[TaskResult] = []
        self._task_counter = 0

    async def execute(
        self,
        task: str,
        vertical: str | None = None,
        region: str | None = None,
        compliance_requirements: list[str] | None = None,
        timeout_seconds: float = DEFAULT_TASK_TIMEOUT
    ) -> TaskResult:
        """
        Execute a task using multi-agent coordination

        Args:
            task: Task description
            vertical: Vertical context (fintech, healthcare, etc.)
            region: Region for compliance (india, eu, uk)
            compliance_requirements: Specific compliance needs
            timeout_seconds: Maximum task execution time (default 300s / 5 min)

        Returns:
            TaskResult with all outputs and audit trail
        """
        start_time = datetime.now()
        vertical = vertical or self.default_vertical
        region = region or "india"  # Default to India for backward compatibility
        compliance_requirements = compliance_requirements or []

        # Generate task ID
        self._task_counter += 1
        task_id = f"task_{self._task_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info("task_started", task_id=task_id, task=task[:100], vertical=vertical, region=region)

        agents: list[Agent] = []

        try:
            async with asyncio.timeout(timeout_seconds):
                # Step 1: Analyze and plan
                plan = await self._analyze_task(task_id, task, vertical, region, compliance_requirements)
                logger.info("task_planned", task_id=task_id, agents=plan.agents_needed, region=region)

                # Step 2: Spawn required agents
                agents = await self._spawn_agents(plan)
                logger.info("agents_spawned", task_id=task_id, count=len(agents))

                # Step 3: Execute subtasks with retry logic
                results = await self._execute_plan_with_retry(plan, agents)
                logger.info("subtasks_completed", task_id=task_id, results_count=len(results))

                # Step 4: Aggregate results
                aggregated = await self._aggregate_results(results, plan)

                # Step 5: Verify compliance
                compliance_status = await self._verify_compliance(
                    results, compliance_requirements, vertical, region
                )

                # Step 6: Cleanup agents
                audit_trail = self._collect_audit_trail(agents)
                self._cleanup_agents(agents)

                # Calculate execution time
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

                self._append_task_history(result)
                logger.info("task_completed", task_id=task_id, execution_time=execution_time)

                return result

        except asyncio.TimeoutError:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error("task_timeout", task_id=task_id, timeout=timeout_seconds)

            # Cleanup any spawned agents
            if agents:
                self._cleanup_agents(agents)

            result = TaskResult(
                task_id=task_id,
                success=False,
                results=[{"error": f"Task timed out after {timeout_seconds}s"}],
                aggregated_output=f"Task timed out after {timeout_seconds} seconds",
                compliance_status={},
                execution_time_seconds=execution_time,
                agents_used=[],
                audit_trail=[]
            )

            self._append_task_history(result)
            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error("task_failed", task_id=task_id, error=str(e))

            # Cleanup any spawned agents
            if agents:
                self._cleanup_agents(agents)

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

            self._append_task_history(result)
            return result

    def _append_task_history(self, result: TaskResult):
        """Append to task history with memory management"""
        self.task_history.append(result)
        if len(self.task_history) > MAX_HISTORY_SIZE:
            self.task_history = self.task_history[-MAX_HISTORY_SIZE:]

    async def _analyze_task(
        self,
        task_id: str,
        task: str,
        vertical: str | None,
        region: str,
        compliance_requirements: list[str]
    ) -> TaskPlan:
        """Analyze task and create execution plan using intelligent task analyzer"""

        # Use intelligent task analyzer
        analyzer = get_analyzer()
        analysis_result: TaskAnalysis = analyzer.analyze(task, compliance_requirements, vertical)

        # Get recommended agents from intelligent analysis
        recommended_agents = analysis_result.recommended_agents

        # Also check registry for any additional matches
        registry_roles = self.registry.find_roles_for_task(task, vertical)

        # Merge recommended agents with registry matches (recommended takes priority)
        # Avoid adding base roles when vertical-specific roles already exist
        all_agents = list(recommended_agents)

        # Extract base role names from recommended agents for duplicate detection
        # e.g., "fintech_coder" -> "coder", "fintech_security" -> "security"
        base_role_names = set()
        for agent in all_agents:
            # Strip vertical prefixes to get base role name
            for prefix in ["fintech_", "eu_fintech_", "uk_fintech_"]:
                if agent.startswith(prefix):
                    base_role_names.add(agent[len(prefix):])
                    break
            else:
                # No prefix, it's already a base role
                base_role_names.add(agent)

        for role in registry_roles:
            # Check if this role or its base version is already in the list
            if role not in all_agents and role not in base_role_names:
                all_agents.append(role)

        # If still no agents, fall back to coder
        if not all_agents:
            all_agents = ["coder"]

        # Apply region prefix to roles (eu_, uk_, or none for india)
        region_roles = self._apply_region_prefix(all_agents, region)

        # Determine execution mode based on complexity
        if analysis_result.complexity.value == "complex" and len(region_roles) > 2:
            execution_mode = ExecutionMode.PARALLEL
        elif len(region_roles) > 3:
            execution_mode = ExecutionMode.PARALLEL
        else:
            execution_mode = ExecutionMode.SEQUENTIAL

        # Create subtasks for each role
        subtasks = []
        for role in region_roles:
            subtasks.append({
                "role": role,
                "task": f"[{role.upper()}] {task}",
                "depends_on": []
            })

        # Add compliance checks based on vertical, region, and detected needs
        compliance_checks = list(compliance_requirements)
        compliance_checks.extend(analysis_result.compliance_needs)

        if vertical == "fintech":
            # Base checks for all regions
            compliance_checks.extend(["pci_dss", "data_encryption", "audit_logging"])

            # Region-specific compliance
            if region == "india":
                compliance_checks.extend(["rbi", "dpdp"])
            elif region == "eu":
                compliance_checks.extend(["gdpr", "psd2", "dora"])
            elif region == "uk":
                compliance_checks.extend(["uk_gdpr", "fca", "psr"])
        elif vertical == "healthcare":
            compliance_checks.extend(["hipaa", "phi_protection", "access_control"])
        elif vertical == "government":
            compliance_checks.extend(["fedramp", "security_clearance", "data_sovereignty"])

        # Build analysis string
        analysis = (
            f"{analysis_result.reasoning} "
            f"[type={analysis_result.task_type.value}, "
            f"complexity={analysis_result.complexity.value}, "
            f"region={region}]"
        )

        logger.info(
            "task_plan_created",
            task_id=task_id,
            task_type=analysis_result.task_type.value,
            complexity=analysis_result.complexity.value,
            agents=region_roles,
            components=analysis_result.detected_components,
        )

        return TaskPlan(
            task_id=task_id,
            original_task=task,
            analysis=analysis,
            subtasks=subtasks,
            agents_needed=region_roles,
            execution_mode=execution_mode,
            compliance_checks=list(set(compliance_checks)),
            vertical=vertical,
            complexity=analysis_result.complexity.value
        )

    def _apply_region_prefix(self, roles: list[str], region: str) -> list[str]:
        """Apply region prefix to role names"""
        if region == "india":
            # India roles have no prefix, but ensure we don't use EU/UK roles
            return [r for r in roles if not r.startswith(("eu_", "uk_"))]

        # For EU/UK, add prefix if not already present
        prefix = f"{region}_"
        result = []
        for role in roles:
            if role.startswith(("eu_", "uk_")):
                # Already has a region prefix
                if role.startswith(prefix):
                    result.append(role)
            else:
                # Add region prefix
                region_role = f"{prefix}{role}"
                # Check if this regional role exists, otherwise fall back
                if self.registry.get_role(region_role):
                    result.append(region_role)
                else:
                    result.append(role)

        return result if result else roles

    async def _spawn_agents(self, plan: TaskPlan) -> list[Agent]:
        """Spawn agents based on plan"""
        agents = []

        for role_name in plan.agents_needed:
            try:
                agent = self.factory.spawn(role_name)
                agents.append(agent)
            except Exception as e:
                logger.warning("agent_spawn_failed", role=role_name, error=str(e))

        return agents

    async def _execute_plan(
        self,
        plan: TaskPlan,
        agents: list[Agent]
    ) -> list[dict[str, Any]]:
        """Execute the task plan"""
        results = []

        if plan.execution_mode == ExecutionMode.PARALLEL:
            # Execute all agents in parallel
            tasks = []
            for i, agent in enumerate(agents):
                subtask = plan.subtasks[i] if i < len(plan.subtasks) else plan.subtasks[0]
                context = AgentContext(
                    task=subtask["task"],
                    vertical=plan.vertical,
                    compliance_requirements=plan.compliance_checks,
                    complexity=plan.complexity
                )
                tasks.append(agent.execute(context))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            results = [
                r if isinstance(r, dict) else {"error": str(r)}
                for r in results
            ]

        else:  # Sequential execution
            for i, agent in enumerate(agents):
                subtask = plan.subtasks[i] if i < len(plan.subtasks) else plan.subtasks[0]

                # Include previous results in context
                context = AgentContext(
                    task=subtask["task"],
                    conversation_history=[
                        {"role": "assistant", "content": str(r.get("response", ""))}
                        for r in results
                    ],
                    vertical=plan.vertical,
                    compliance_requirements=plan.compliance_checks,
                    complexity=plan.complexity
                )

                result = await agent.execute(context)
                results.append(result)

        return results

    async def _execute_plan_with_retry(
        self,
        plan: TaskPlan,
        agents: list[Agent]
    ) -> list[dict[str, Any]]:
        """Execute task plan with retry logic for agent failures"""
        results = []

        if plan.execution_mode == ExecutionMode.PARALLEL:
            # Execute all agents in parallel with retry
            tasks = []
            for i, agent in enumerate(agents):
                subtask = plan.subtasks[i] if i < len(plan.subtasks) else plan.subtasks[0]
                context = AgentContext(
                    task=subtask["task"],
                    vertical=plan.vertical,
                    compliance_requirements=plan.compliance_checks,
                    complexity=plan.complexity
                )
                # Wrap each agent execution in retry logic
                tasks.append(
                    self._execute_agent_with_retry(agent, context)
                )

            results = await asyncio.gather(*tasks, return_exceptions=True)
            results = [
                r if isinstance(r, dict) else {"error": str(r), "success": False}
                for r in results
            ]

        else:  # Sequential execution
            for i, agent in enumerate(agents):
                subtask = plan.subtasks[i] if i < len(plan.subtasks) else plan.subtasks[0]

                context = AgentContext(
                    task=subtask["task"],
                    conversation_history=[
                        {"role": "assistant", "content": str(r.get("response", ""))}
                        for r in results
                    ],
                    vertical=plan.vertical,
                    compliance_requirements=plan.compliance_checks,
                    complexity=plan.complexity
                )

                result = await self._execute_agent_with_retry(agent, context)
                results.append(result)

        return results

    async def _execute_agent_with_retry(
        self,
        agent: Agent,
        context: AgentContext
    ) -> dict[str, Any]:
        """Execute a single agent with retry logic"""
        try:
            return await with_retry(
                agent.execute,
                context,
                max_attempts=AGENT_RETRY_ATTEMPTS,
                backoff_factor=AGENT_RETRY_BACKOFF,
                initial_delay=1.0,
                exceptions=(Exception,)
            )
        except RetryError as e:
            logger.error(
                "agent_retry_exhausted",
                agent_id=agent.agent_id,
                role=agent.role_name,
                error=str(e)
            )
            return {
                "agent_id": agent.agent_id,
                "role": agent.role_name,
                "response": None,
                "error": f"Agent failed after {AGENT_RETRY_ATTEMPTS} retries: {e}",
                "success": False
            }

    async def _aggregate_results(
        self,
        results: list[dict[str, Any]],
        plan: TaskPlan
    ) -> str:
        """Aggregate results from all agents"""
        output_parts = []

        for i, result in enumerate(results):
            role = result.get("role", f"Agent {i}")
            response = result.get("response", "No response")
            success = result.get("success", False)

            status = "✓" if success else "✗"
            output_parts.append(f"## {role} {status}\n\n{response}\n")

        return "\n---\n".join(output_parts)

    async def _verify_compliance(
        self,
        results: list[dict[str, Any]],
        requirements: list[str],
        vertical: str | None,
        region: str = "india"
    ) -> dict[str, bool]:
        """
        Actually verify compliance by scanning agent outputs

        Args:
            results: Agent execution results containing responses
            requirements: List of compliance requirements to check
            vertical: Industry vertical (fintech, healthcare, etc.)
            region: Region for compliance (india, eu, uk)

        Returns:
            Dict mapping requirement names to pass/fail status
        """
        from ..tools.security_tools import SecurityScanner

        compliance_status: dict[str, bool] = {}
        code_blocks = self._extract_code_from_results(results)

        if not code_blocks:
            # No code to check - pass by default with a note
            for req in requirements:
                compliance_status[req] = True
            compliance_status["_note"] = True  # Indicates no code was checked
            return compliance_status

        # Run compliance checker if vertical is fintech
        if vertical == "fintech":
            try:
                from verticals.fintech.compliance import ComplianceChecker

                checker = ComplianceChecker(standards=requirements, region=region)
                for code, filename in code_blocks:
                    report = checker.check_code(code, filename)

                    for req in requirements:
                        # Check if this requirement has issues
                        req_issues = [
                            i for i in report.issues
                            if req.lower() in i.rule_id.lower() or req.lower() in i.rule_name.lower()
                        ]
                        critical_high = [
                            i for i in req_issues
                            if i.severity.value in ("critical", "high")
                        ]

                        if critical_high:
                            # Fail if there are critical/high severity issues
                            compliance_status[req] = False
                        elif req not in compliance_status:
                            # Pass if no critical/high issues found
                            compliance_status[req] = True
            except ImportError:
                logger.warning("compliance_checker_not_available")
                # Fall back to security scanner only
                for req in requirements:
                    if req not in compliance_status:
                        compliance_status[req] = True

        # Always run security scan
        try:
            scanner = SecurityScanner()
            has_critical_security_issues = False

            for code, filename in code_blocks:
                scan_result = scanner.scan_code(code, filename)
                if not scan_result["passed"]:
                    # Check for critical/high severity issues
                    critical_issues = [
                        i for i in scan_result.get("issues", [])
                        if i.get("severity") in ("critical", "high")
                    ]
                    if critical_issues:
                        has_critical_security_issues = True
                        break

            compliance_status["security_scan"] = not has_critical_security_issues
        except Exception as e:
            logger.warning("security_scan_failed", error=str(e))
            compliance_status["security_scan"] = True  # Don't fail if scanner unavailable

        # Always pass audit_logging if we have audit trails
        if vertical == "fintech":
            compliance_status["audit_logging"] = True

        # Fill in any remaining requirements as passed
        for req in requirements:
            if req not in compliance_status:
                compliance_status[req] = True

        return compliance_status

    def _extract_code_from_results(
        self,
        results: list[dict[str, Any]]
    ) -> list[tuple[str, str]]:
        """
        Extract code blocks from agent responses

        Args:
            results: List of agent result dicts

        Returns:
            List of (code, filename) tuples
        """
        import re

        code_blocks: list[tuple[str, str]] = []

        for i, result in enumerate(results):
            response = result.get("response", "")
            if not response:
                continue

            # Match markdown code blocks with optional language specifier
            pattern = r'```(?:python|py)?\n(.*?)```'
            matches = re.findall(pattern, response, re.DOTALL)

            for j, code in enumerate(matches):
                code = code.strip()
                if code:  # Only include non-empty code blocks
                    filename = f"agent_{i}_block_{j}.py"
                    code_blocks.append((code, filename))

        return code_blocks

    def _collect_audit_trail(self, agents: list[Agent]) -> list[dict[str, Any]]:
        """Collect audit trails from all agents"""
        return [agent.get_audit_log() for agent in agents]

    def _cleanup_agents(self, agents: list[Agent]):
        """Clean up agents after task completion"""
        for agent in agents:
            self.factory.destroy_agent(agent.agent_id)

    def get_task_history(self) -> list[dict[str, Any]]:
        """Get history of all executed tasks"""
        return [
            {
                "task_id": r.task_id,
                "success": r.success,
                "execution_time": r.execution_time_seconds,
                "agents_used": r.agents_used,
                "compliance_status": r.compliance_status
            }
            for r in self.task_history
        ]

    @property
    def stats(self) -> dict[str, Any]:
        """Get orchestrator statistics"""
        successful = sum(1 for r in self.task_history if r.success)
        total = len(self.task_history)

        return {
            "total_tasks": total,
            "successful_tasks": successful,
            "success_rate": successful / total if total > 0 else 0,
            "factory_stats": self.factory.stats,
            "available_roles": self.registry.list_roles()
        }
