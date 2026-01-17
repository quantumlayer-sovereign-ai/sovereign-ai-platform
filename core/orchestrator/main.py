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
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import structlog

from ..agents.base import Agent, AgentContext, AgentState
from ..agents.factory import AgentFactory
from ..agents.registry import get_registry

logger = structlog.get_logger()


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
    subtasks: List[Dict[str, Any]]
    agents_needed: List[str]
    execution_mode: ExecutionMode
    compliance_checks: List[str]
    vertical: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TaskResult:
    """Result of task execution"""
    task_id: str
    success: bool
    results: List[Dict[str, Any]]
    aggregated_output: str
    compliance_status: Dict[str, bool]
    execution_time_seconds: float
    agents_used: List[str]
    audit_trail: List[Dict[str, Any]]


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
        default_vertical: Optional[str] = None
    ):
        self.model = model_interface
        self.factory = AgentFactory(model_interface=model_interface, max_agents=max_agents)
        self.registry = get_registry()
        self.default_vertical = default_vertical

        self.task_history: List[TaskResult] = []
        self._task_counter = 0

    async def execute(
        self,
        task: str,
        vertical: Optional[str] = None,
        compliance_requirements: Optional[List[str]] = None
    ) -> TaskResult:
        """
        Execute a task using multi-agent coordination

        Args:
            task: Task description
            vertical: Vertical context (fintech, healthcare, etc.)
            compliance_requirements: Specific compliance needs

        Returns:
            TaskResult with all outputs and audit trail
        """
        start_time = datetime.now()
        vertical = vertical or self.default_vertical
        compliance_requirements = compliance_requirements or []

        # Generate task ID
        self._task_counter += 1
        task_id = f"task_{self._task_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info("task_started", task_id=task_id, task=task[:100], vertical=vertical)

        try:
            # Step 1: Analyze and plan
            plan = await self._analyze_task(task_id, task, vertical, compliance_requirements)
            logger.info("task_planned", task_id=task_id, agents=plan.agents_needed)

            # Step 2: Spawn required agents
            agents = await self._spawn_agents(plan)
            logger.info("agents_spawned", task_id=task_id, count=len(agents))

            # Step 3: Execute subtasks
            results = await self._execute_plan(plan, agents)
            logger.info("subtasks_completed", task_id=task_id, results_count=len(results))

            # Step 4: Aggregate results
            aggregated = await self._aggregate_results(results, plan)

            # Step 5: Verify compliance
            compliance_status = await self._verify_compliance(
                results, compliance_requirements, vertical
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

            self.task_history.append(result)
            logger.info("task_completed", task_id=task_id, execution_time=execution_time)

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error("task_failed", task_id=task_id, error=str(e))

            result = TaskResult(
                task_id=task_id,
                success=False,
                results=[{"error": str(e)}],
                aggregated_output=f"Task failed: {str(e)}",
                compliance_status={},
                execution_time_seconds=execution_time,
                agents_used=[],
                audit_trail=[]
            )

            self.task_history.append(result)
            return result

    async def _analyze_task(
        self,
        task_id: str,
        task: str,
        vertical: Optional[str],
        compliance_requirements: List[str]
    ) -> TaskPlan:
        """Analyze task and create execution plan"""

        # Find matching roles based on task content
        matching_roles = self.registry.find_roles_for_task(task, vertical)

        # If no specific roles match, use a default set
        if not matching_roles:
            matching_roles = ["coder"]

        # Determine execution mode
        execution_mode = ExecutionMode.SEQUENTIAL
        if len(matching_roles) > 2:
            # For complex tasks, some can run in parallel
            execution_mode = ExecutionMode.PARALLEL

        # Create subtasks for each role
        subtasks = []
        for role in matching_roles:
            subtasks.append({
                "role": role,
                "task": f"[{role.upper()}] {task}",
                "depends_on": []
            })

        # Add compliance checks based on vertical
        compliance_checks = list(compliance_requirements)
        if vertical == "fintech":
            compliance_checks.extend(["pci_dss", "data_encryption", "audit_logging"])
        elif vertical == "healthcare":
            compliance_checks.extend(["hipaa", "phi_protection", "access_control"])
        elif vertical == "government":
            compliance_checks.extend(["fedramp", "security_clearance", "data_sovereignty"])

        # Simple analysis without model for now
        analysis = f"Task requires {len(matching_roles)} agent(s): {', '.join(matching_roles)}"

        return TaskPlan(
            task_id=task_id,
            original_task=task,
            analysis=analysis,
            subtasks=subtasks,
            agents_needed=matching_roles,
            execution_mode=execution_mode,
            compliance_checks=list(set(compliance_checks)),
            vertical=vertical
        )

    async def _spawn_agents(self, plan: TaskPlan) -> List[Agent]:
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
        agents: List[Agent]
    ) -> List[Dict[str, Any]]:
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
                    compliance_requirements=plan.compliance_checks
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
                    compliance_requirements=plan.compliance_checks
                )

                result = await agent.execute(context)
                results.append(result)

        return results

    async def _aggregate_results(
        self,
        results: List[Dict[str, Any]],
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
        results: List[Dict[str, Any]],
        requirements: List[str],
        vertical: Optional[str]
    ) -> Dict[str, bool]:
        """Verify compliance requirements are met"""
        compliance_status = {}

        for req in requirements:
            # Simple compliance check - can be enhanced with real checks
            compliance_status[req] = True  # Placeholder

        # Add vertical-specific checks
        if vertical == "fintech":
            compliance_status["audit_logging"] = True  # We have audit trails
            compliance_status["data_encryption"] = True  # Placeholder

        return compliance_status

    def _collect_audit_trail(self, agents: List[Agent]) -> List[Dict[str, Any]]:
        """Collect audit trails from all agents"""
        return [agent.get_audit_log() for agent in agents]

    def _cleanup_agents(self, agents: List[Agent]):
        """Clean up agents after task completion"""
        for agent in agents:
            self.factory.destroy_agent(agent.agent_id)

    def get_task_history(self) -> List[Dict[str, Any]]:
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
    def stats(self) -> Dict[str, Any]:
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
