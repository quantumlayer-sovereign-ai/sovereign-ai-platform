"""
Agent Factory - Creates and manages agent instances

Features:
- Agent spawning with role assignment
- Agent pool management
- Resource tracking
- Lifecycle management
- Auto LoRA adapter loading for specialized roles
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from .base import Agent, AgentState
from .registry import get_registry

logger = structlog.get_logger()

# Default adapter directory
DEFAULT_ADAPTERS_DIR = Path("data/adapters")


class AgentFactory:
    """
    Factory for creating and managing agents

    Handles:
    - Agent creation with role assignment
    - Agent pool management
    - Resource tracking
    - Cleanup and destruction
    - Auto LoRA adapter loading for specialized roles
    """

    def __init__(
        self,
        model_interface: Any = None,
        max_agents: int = 10,
        adapters_dir: Path | None = None,
        auto_load_lora: bool = True
    ):
        self.model_interface = model_interface
        self.max_agents = max_agents
        self.active_agents: dict[str, Agent] = {}
        self.agent_history: list[dict[str, Any]] = []
        self.registry = get_registry()
        self.adapters_dir = adapters_dir or DEFAULT_ADAPTERS_DIR
        self.auto_load_lora = auto_load_lora
        self._loaded_adapters: set[str] = set()

    @classmethod
    def create_agent(
        cls,
        role: dict[str, Any] | None = None,
        role_name: str | None = None,
        model_interface: Any = None,
        parent_id: str | None = None,
        tools: dict[str, Any] | None = None
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
        tools: dict[str, Any] | None = None,
        parent_id: str | None = None,
        lora_version: str = "latest"
    ) -> Agent:
        """
        Spawn a new agent and add to pool

        Args:
            role_name: Name of role from registry
            tools: Additional tools
            parent_id: Parent agent ID
            lora_version: LoRA adapter version to load ("latest" or specific version)

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

        # Auto-load LoRA adapter if available
        if self.auto_load_lora and self.model_interface:
            self._load_adapter_for_role(role_name, lora_version)

        agent = self.create_agent(
            role=role,
            model_interface=self.model_interface,
            parent_id=parent_id,
            tools=tools
        )

        self.active_agents[agent.agent_id] = agent
        return agent

    def _has_adapter(self, role_name: str) -> bool:
        """Check if an adapter exists for the role"""
        adapter_path = self._get_adapter_path(role_name)
        return adapter_path is not None and adapter_path.exists()

    def _get_adapter_path(self, role_name: str, version: str = "latest") -> Path | None:
        """Get path to adapter for a role"""
        role_dir = self.adapters_dir / role_name

        if not role_dir.exists():
            return None

        if version == "latest":
            latest_link = role_dir / "latest"
            if latest_link.exists():
                return latest_link.resolve()
            # Fall back to most recent version directory
            versions = sorted(
                [d for d in role_dir.iterdir() if d.is_dir() and not d.is_symlink()],
                reverse=True
            )
            if versions:
                return versions[0]
            return None

        version_path = role_dir / version
        return version_path if version_path.exists() else None

    def _load_adapter_for_role(self, role_name: str, version: str = "latest"):
        """Load LoRA adapter for a role if available"""
        # Skip if already loaded
        if role_name in self._loaded_adapters:
            # Just activate the existing adapter
            if hasattr(self.model_interface, 'set_active_lora'):
                try:
                    self.model_interface.set_active_lora(role_name)
                    logger.debug("lora_activated", role=role_name)
                except (ValueError, RuntimeError):
                    pass  # Adapter may not be loaded yet
            return

        adapter_path = self._get_adapter_path(role_name, version)
        if adapter_path is None:
            logger.debug("no_adapter_found", role=role_name)
            return

        # Check for adapter files
        if not (adapter_path / "adapter_config.json").exists():
            logger.debug("invalid_adapter", role=role_name, path=str(adapter_path))
            return

        # Load the adapter
        try:
            if hasattr(self.model_interface, 'load_lora'):
                self.model_interface.load_lora(str(adapter_path), role_name)
                self._loaded_adapters.add(role_name)
                logger.info("lora_loaded", role=role_name, path=str(adapter_path))
        except Exception as e:
            logger.warning("lora_load_failed", role=role_name, error=str(e))

    def unload_adapter(self, role_name: str):
        """Unload a specific LoRA adapter"""
        if role_name not in self._loaded_adapters:
            return

        if hasattr(self.model_interface, 'unload_lora'):
            self.model_interface.unload_lora(role_name)
            self._loaded_adapters.discard(role_name)
            logger.info("lora_unloaded", role=role_name)

    def list_loaded_adapters(self) -> list[str]:
        """List currently loaded adapters"""
        return list(self._loaded_adapters)

    def spawn_for_task(
        self,
        task: str,
        vertical: str | None = None,
        parent_id: str | None = None
    ) -> list[Agent]:
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

    def get_agent(self, agent_id: str) -> Agent | None:
        """Get an agent by ID"""
        return self.active_agents.get(agent_id)

    def list_agents(self) -> list[dict[str, Any]]:
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

    def get_audit_trail(self) -> list[dict[str, Any]]:
        """Get complete audit trail of all agents"""
        return self.agent_history + [
            agent.get_audit_log() for agent in self.active_agents.values()
        ]

    @property
    def stats(self) -> dict[str, Any]:
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
_factory: AgentFactory | None = None


def get_factory(model_interface: Any = None) -> AgentFactory:
    """Get the global agent factory"""
    global _factory
    if _factory is None:
        _factory = AgentFactory(model_interface=model_interface)
    return _factory
