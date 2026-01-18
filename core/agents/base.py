"""
Base Agent Class - Foundation for all AI agents

Supports:
- Dynamic role assumption
- State management
- Tool execution
- Child agent spawning
- Lifecycle management
"""

import asyncio
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger()

# Memory management constants
MAX_STATE_HISTORY_SIZE = 100
MAX_ACTION_LOG_SIZE = 100
DEFAULT_EXECUTION_TIMEOUT = 60.0  # seconds


class AgentState(Enum):
    """Agent lifecycle states"""
    IDLE = "idle"
    SPAWNED = "spawned"
    WORKING = "working"
    WAITING = "waiting"  # Waiting for child agents or external input
    COMPLETED = "completed"
    FAILED = "failed"
    DESTROYED = "destroyed"


@dataclass
class AgentMessage:
    """Message passed between agents"""
    sender_id: str
    receiver_id: str
    content: str
    message_type: str = "text"  # text, task, result, error
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentContext:
    """Context passed to agent for task execution"""
    task: str
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    shared_memory: dict[str, Any] = field(default_factory=dict)
    parent_agent_id: str | None = None
    vertical: str | None = None  # fintech, healthcare, government, legal
    compliance_requirements: list[str] = field(default_factory=list)


class Agent:
    """
    Base Agent Class

    Features:
    - Dynamic role switching
    - Tool execution
    - Child agent spawning
    - State management
    - Audit logging
    """

    def __init__(
        self,
        agent_id: str | None = None,
        role: dict[str, Any] | None = None,
        model_interface: Any = None,
        tools: dict[str, Callable] | None = None,
        parent_id: str | None = None,
    ):
        self.agent_id = agent_id or str(uuid.uuid4())[:8]
        self.role = role or {}
        self.model = model_interface
        self.tools = tools or {}
        self.parent_id = parent_id

        self.state = AgentState.IDLE
        self.children: list[str] = []
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.results: list[Any] = []

        # Audit trail
        self.created_at = datetime.now()
        self.state_history: list[dict[str, Any]] = []
        self.action_log: list[dict[str, Any]] = []

        self._log_state_change(AgentState.IDLE)
        logger.info("agent_created", agent_id=self.agent_id, role=self.role.get("name", "unnamed"))

    @property
    def role_name(self) -> str:
        return self.role.get("name", "base_agent")

    @property
    def system_prompt(self) -> str:
        return self.role.get("system_prompt", "You are a helpful AI assistant.")

    def _log_state_change(self, new_state: AgentState):
        """Log state changes for audit trail (bounded)"""
        self.state_history.append({
            "from_state": self.state.value if hasattr(self, 'state') else None,
            "to_state": new_state.value,
            "timestamp": datetime.now().isoformat()
        })
        # Memory management: bound the state history
        if len(self.state_history) > MAX_STATE_HISTORY_SIZE:
            self.state_history = self.state_history[-MAX_STATE_HISTORY_SIZE:]
        self.state = new_state

    def _log_action(self, action: str, details: dict[str, Any]):
        """Log actions for audit trail (bounded)"""
        self.action_log.append({
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "role": self.role_name
        })
        # Memory management: bound the action log
        if len(self.action_log) > MAX_ACTION_LOG_SIZE:
            self.action_log = self.action_log[-MAX_ACTION_LOG_SIZE:]

    def assume_role(self, role: dict[str, Any]):
        """
        Dynamically switch to a different role

        Args:
            role: Role configuration dict with system_prompt, tools, etc.
        """
        old_role = self.role_name
        self.role = role

        # Update tools if specified in role (tools can be list of names or dict)
        role_tools = role.get("tools", [])
        if isinstance(role_tools, list):
            # Convert tool names to placeholder functions
            for tool_name in role_tools:
                if tool_name not in self.tools:
                    self.tools[tool_name] = lambda tn=tool_name: f"Tool {tn} executed"
        elif isinstance(role_tools, dict):
            self.tools.update(role_tools)

        self._log_action("role_switch", {
            "from_role": old_role,
            "to_role": self.role_name
        })
        logger.info("role_switched", agent_id=self.agent_id, from_role=old_role, to_role=self.role_name)

    async def execute(
        self,
        context: AgentContext,
        timeout_seconds: float = DEFAULT_EXECUTION_TIMEOUT
    ) -> dict[str, Any]:
        """
        Execute a task with the current role

        Args:
            context: AgentContext with task details
            timeout_seconds: Maximum execution time in seconds (default 60)

        Returns:
            Result dict with output and metadata
        """
        self._log_state_change(AgentState.WORKING)
        self._log_action("execute_start", {"task": context.task[:100], "timeout": timeout_seconds})

        try:
            async with asyncio.timeout(timeout_seconds):
                # Build messages for the model
                messages = self._build_messages(context)

                # Execute with model
                if self.model:
                    response = await self._call_model(messages)
                else:
                    response = f"[No model attached] Would process: {context.task}"

                # Check if we need to use tools
                tool_results = await self._process_tool_calls(response)

                result = {
                    "agent_id": self.agent_id,
                    "role": self.role_name,
                    "response": response,
                    "tool_results": tool_results,
                    "success": True
                }

                self._log_state_change(AgentState.COMPLETED)
                self._log_action("execute_complete", {"success": True})

                return result

        except asyncio.TimeoutError:
            self._log_state_change(AgentState.FAILED)
            self._log_action("execute_timeout", {"timeout_seconds": timeout_seconds})
            logger.error(
                "agent_execution_timeout",
                agent_id=self.agent_id,
                timeout=timeout_seconds
            )

            return {
                "agent_id": self.agent_id,
                "role": self.role_name,
                "response": None,
                "error": f"Agent execution timed out after {timeout_seconds}s",
                "success": False
            }

        except Exception as e:
            self._log_state_change(AgentState.FAILED)
            self._log_action("execute_failed", {"error": str(e)})
            logger.error("agent_execution_failed", agent_id=self.agent_id, error=str(e))

            return {
                "agent_id": self.agent_id,
                "role": self.role_name,
                "response": None,
                "error": str(e),
                "success": False
            }

    def _build_messages(self, context: AgentContext) -> list[dict[str, str]]:
        """Build message list for model"""
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add conversation history
        messages.extend(context.conversation_history)

        # Add current task
        messages.append({"role": "user", "content": context.task})

        return messages

    async def _call_model(self, messages: list[dict[str, str]]) -> str:
        """Call the underlying model"""
        # This will be implemented by the model interface
        if hasattr(self.model, 'generate'):
            return await self.model.generate(messages)
        return str(messages)

    async def _process_tool_calls(self, response: str) -> list[dict[str, Any]]:
        """Process any tool calls in the response"""
        # Tool call detection and execution logic
        tool_results = []

        # Simple tool call detection (can be enhanced)
        for tool_name, tool_func in self.tools.items():
            if f"[TOOL:{tool_name}]" in response:
                try:
                    result = await tool_func() if asyncio.iscoroutinefunction(tool_func) else tool_func()
                    tool_results.append({
                        "tool": tool_name,
                        "result": result,
                        "success": True
                    })
                except Exception as e:
                    tool_results.append({
                        "tool": tool_name,
                        "error": str(e),
                        "success": False
                    })

        return tool_results

    async def spawn_child(self, role: dict[str, Any], task: str) -> 'Agent':
        """
        Spawn a child agent for a subtask

        Args:
            role: Role for the child agent
            task: Task for the child to execute

        Returns:
            The spawned child agent
        """
        from .factory import AgentFactory

        self._log_state_change(AgentState.WAITING)

        child = AgentFactory.create_agent(
            role=role,
            model_interface=self.model,
            parent_id=self.agent_id
        )
        self.children.append(child.agent_id)

        self._log_action("spawn_child", {
            "child_id": child.agent_id,
            "child_role": child.role_name,
            "task": task[:100]
        })

        logger.info("child_spawned",
                   parent_id=self.agent_id,
                   child_id=child.agent_id,
                   child_role=child.role_name)

        return child

    async def send_message(self, receiver_id: str, content: str, message_type: str = "text"):
        """Send a message to another agent"""
        message = AgentMessage(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            content=content,
            message_type=message_type
        )
        self._log_action("send_message", {
            "receiver": receiver_id,
            "type": message_type
        })
        return message

    async def receive_message(self) -> AgentMessage:
        """Receive a message from the queue"""
        return await self.message_queue.get()

    def destroy(self):
        """Clean up and destroy the agent"""
        self._log_state_change(AgentState.DESTROYED)
        self._log_action("destroyed", {})
        logger.info("agent_destroyed", agent_id=self.agent_id)

    def get_audit_log(self) -> dict[str, Any]:
        """Get complete audit log for compliance"""
        return {
            "agent_id": self.agent_id,
            "role": self.role_name,
            "created_at": self.created_at.isoformat(),
            "state_history": self.state_history,
            "action_log": self.action_log,
            "children": self.children
        }

    def __repr__(self):
        return f"Agent(id={self.agent_id}, role={self.role_name}, state={self.state.value})"
