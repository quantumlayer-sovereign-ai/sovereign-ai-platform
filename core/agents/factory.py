"""
Agent Factory - Creates and manages agent instances

Features:
- Agent spawning with role assignment
- Agent pool management
- Resource tracking
- Lifecycle management
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog

from .base import Agent, AgentState
from .registry import RoleRegistry, get_registry

logger = structlog.get_logger()


class AgentFactory:
    """
    Factory for creating and managing agents

    Handles:
    - Agent creation with role assignment
    - Agent pool management
    - Resource tracking
    - Cleanup and destruction
    """

    def __init__(self, model_interface: Any = None, max_agents: int = 10):
        self.model_interface = model_interface
        self.max_agents = max_agents
        self.active_agents: Dict[str, Agent] = {}
        self.agent_history: List[Dict[str, Any]] = []
        self.registry = get_registry()

    @classmethod
    def create_agent(
        cls,
        role: Optional[Dict[str, Any]] = None,
        role_name: Optional[str] = None,
        model_interface: Any = None,
        parent_id: Optional[str] = None,
        tools: Optional[Dict[str, Any]] = None
    ) -> Agent:
        """
        Create a new agent instance

        Args:
            role: Direct role configuration dict
            role_name: Name of role to load from registry
            model_interface: Model to use for generation
            parent_id: Parent agent ID if spawned as child
            tools: Additional tools to attach

        Returns:
            Newly created Agent instance
        """
        # Get role from registry if name provided
        if role_name and not role:
            registry = get_registry()
            role = registry.get_role(role_name)
            if not role:
                raise ValueError(f"Role not found: {role_name}")

        # Create agent
        agent = Agent(
            role=role or {},
            model_interface=model_interface,
            parent_id=parent_id,
            tools=tools
        )

        agent._log_state_change(AgentState.SPAWNED)
        logger.info("agent_spawned",
                   agent_id=agent.agent_id,
                   role=agent.role_name,
                   parent_id=parent_id)

        return agent

    def spawn(
        self,
        role_name: str,
        tools: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None
    ) -> Agent:
        """
        Spawn a new agent and add to pool

        Args:
            role_name: Name of role from registry
            tools: Additional tools
            parent_id: Parent agent ID

        Returns:
            Spawned agent
        """
        if len(self.active_agents) >= self.max_agents:
            # Try to clean up completed agents
            self._cleanup_completed()

            if len(self.active_agents) >= self.max_agents:
                raise RuntimeError(f"Maximum agents ({self.max_agents}) reached")

        role = self.registry.get_role(role_name)
        if not role:
            raise ValueError(f"Role not found: {role_name}")

        agent = self.create_agent(
            role=role,
            model_interface=self.model_interface,
            parent_id=parent_id,
            tools=tools
        )

        self.active_agents[agent.agent_id] = agent
        return agent

    def spawn_for_task(
        self,
        task: str,
        vertical: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> List[Agent]:
        """
        Automatically spawn agents based on task analysis

        Args:
            task: Task description
            vertical: Vertical context (fintech, healthcare, etc.)
            parent_id: Parent agent ID

        Returns:
            List of spawned agents
        """
        matching_roles = self.registry.find_roles_for_task(task, vertical)

        if not matching_roles:
            # Default to coder if no specific match
            matching_roles = ["coder"]

        agents = []
        for role_name in matching_roles:
            try:
                agent = self.spawn(role_name, parent_id=parent_id)
                agents.append(agent)
            except RuntimeError as e:
                logger.warning("spawn_failed", role=role_name, error=str(e))
                break

        logger.info("agents_spawned_for_task",
                   task=task[:50],
                   roles=matching_roles,
                   count=len(agents))

        return agents

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID"""
        return self.active_agents.get(agent_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all active agents"""
        return [
            {
                "id": agent.agent_id,
                "role": agent.role_name,
                "state": agent.state.value,
                "parent": agent.parent_id,
                "children": agent.children
            }
            for agent in self.active_agents.values()
        ]

    def destroy_agent(self, agent_id: str):
        """Destroy an agent and remove from pool"""
        agent = self.active_agents.get(agent_id)
        if agent:
            # Archive to history
            self.agent_history.append({
                "agent_id": agent.agent_id,
                "role": agent.role_name,
                "created_at": agent.created_at.isoformat(),
                "destroyed_at": datetime.now().isoformat(),
                "audit_log": agent.get_audit_log()
            })

            agent.destroy()
            del self.active_agents[agent_id]
            logger.info("agent_destroyed", agent_id=agent_id)

    def _cleanup_completed(self):
        """Remove completed/failed agents from pool"""
        to_remove = [
            agent_id for agent_id, agent in self.active_agents.items()
            if agent.state in (AgentState.COMPLETED, AgentState.FAILED, AgentState.DESTROYED)
        ]

        for agent_id in to_remove:
            self.destroy_agent(agent_id)

        if to_remove:
            logger.info("agents_cleaned_up", count=len(to_remove))

    def destroy_all(self):
        """Destroy all agents"""
        agent_ids = list(self.active_agents.keys())
        for agent_id in agent_ids:
            self.destroy_agent(agent_id)
        logger.info("all_agents_destroyed")

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Get complete audit trail of all agents"""
        return self.agent_history + [
            agent.get_audit_log() for agent in self.active_agents.values()
        ]

    @property
    def stats(self) -> Dict[str, Any]:
        """Get factory statistics"""
        state_counts = {}
        for agent in self.active_agents.values():
            state = agent.state.value
            state_counts[state] = state_counts.get(state, 0) + 1

        return {
            "active_agents": len(self.active_agents),
            "max_agents": self.max_agents,
            "total_spawned": len(self.agent_history) + len(self.active_agents),
            "state_breakdown": state_counts
        }


# Global factory instance
_factory: Optional[AgentFactory] = None


def get_factory(model_interface: Any = None) -> AgentFactory:
    """Get the global agent factory"""
    global _factory
    if _factory is None:
        _factory = AgentFactory(model_interface=model_interface)
    return _factory
