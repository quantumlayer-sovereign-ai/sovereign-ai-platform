"""
Unit Tests for Base Agent

Tests:
- Agent initialization
- State management
- Context handling
- Execution flow
- Audit logging
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest


class TestAgentBaseUnit:
    """Unit tests for Agent base class"""

    @pytest.fixture
    def basic_role(self):
        """Basic role configuration"""
        return {
            "name": "test_agent",
            "display_name": "Test Agent",
            "description": "A test agent",
            "system_prompt": "You are a test assistant.",
            "capabilities": ["testing"],
            "spawn_conditions": ["test"],
            "vertical": "test"
        }

    @pytest.fixture
    def mock_model(self):
        """Mock model interface"""
        model = Mock()
        model.generate = Mock(return_value="Generated response")
        model.generate_async = AsyncMock(return_value="Generated response")
        return model

    @pytest.mark.unit
    def test_agent_initialization(self, basic_role):
        """Test agent initialization"""
        from core.agents.base import Agent

        agent = Agent(role=basic_role)

        assert agent.role_name == "test_agent"
        assert agent.system_prompt == "You are a test assistant."
        assert agent.agent_id is not None
        assert len(agent.agent_id) == 8

    @pytest.mark.unit
    def test_agent_id_uniqueness(self, basic_role):
        """Test that agent IDs are unique"""
        from core.agents.base import Agent

        agents = [Agent(role=basic_role) for _ in range(10)]
        ids = [a.agent_id for a in agents]

        assert len(ids) == len(set(ids))

    @pytest.mark.unit
    def test_agent_initial_state(self, basic_role):
        """Test agent initial state"""
        from core.agents.base import Agent, AgentState

        agent = Agent(role=basic_role)

        assert agent.state == AgentState.IDLE

    @pytest.mark.unit
    def test_agent_with_parent(self, basic_role):
        """Test agent with parent ID"""
        from core.agents.base import Agent

        agent = Agent(role=basic_role, parent_id="parent123")

        assert agent.parent_id == "parent123"

    @pytest.mark.unit
    def test_agent_with_model(self, basic_role, mock_model):
        """Test agent with model interface"""
        from core.agents.base import Agent

        agent = Agent(role=basic_role, model_interface=mock_model)

        assert agent.model == mock_model

    @pytest.mark.unit
    def test_agent_without_model(self, basic_role):
        """Test agent without model interface"""
        from core.agents.base import Agent

        agent = Agent(role=basic_role, model_interface=None)

        assert agent.model is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_agent_execute_without_model(self, basic_role):
        """Test agent execution without model"""
        from core.agents.base import Agent, AgentContext

        agent = Agent(role=basic_role, model_interface=None)
        context = AgentContext(task="Test task")

        result = await agent.execute(context)

        assert result["success"] is True
        assert "[No model attached]" in result["response"]

    @pytest.mark.unit
    def test_agent_context_creation(self):
        """Test AgentContext creation"""
        from core.agents.base import AgentContext

        context = AgentContext(
            task="Test task",
            vertical="fintech",
            compliance_requirements=["pci_dss"]
        )

        assert context.task == "Test task"
        assert context.vertical == "fintech"
        assert "pci_dss" in context.compliance_requirements

    @pytest.mark.unit
    def test_agent_context_with_history(self):
        """Test AgentContext with conversation history"""
        from core.agents.base import AgentContext

        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]

        context = AgentContext(
            task="Continue conversation",
            conversation_history=history
        )

        assert len(context.conversation_history) == 2

    @pytest.mark.unit
    def test_agent_audit_log(self, basic_role):
        """Test agent audit logging"""
        from core.agents.base import Agent

        agent = Agent(role=basic_role)

        audit_log = agent.get_audit_log()

        assert "agent_id" in audit_log
        assert "role" in audit_log
        assert "created_at" in audit_log
        assert "state_history" in audit_log

    @pytest.mark.unit
    def test_agent_destroy(self, basic_role):
        """Test agent destruction"""
        from core.agents.base import Agent, AgentState

        agent = Agent(role=basic_role)
        agent.destroy()

        assert agent.state == AgentState.DESTROYED

    @pytest.mark.unit
    def test_agent_spawn_child(self, basic_role):
        """Test spawning child agent"""
        from core.agents.base import Agent

        parent = Agent(role=basic_role)
        child = Agent(role=basic_role, parent_id=parent.agent_id)

        assert child.parent_id == parent.agent_id

    @pytest.mark.unit
    def test_agent_created_at(self, basic_role):
        """Test agent creation timestamp"""
        from core.agents.base import Agent

        before = datetime.now()
        agent = Agent(role=basic_role)
        after = datetime.now()

        assert before <= agent.created_at <= after


class TestAgentStateUnit:
    """Unit tests for AgentState enum"""

    @pytest.mark.unit
    def test_agent_states(self):
        """Test agent state values"""
        from core.agents.base import AgentState

        assert AgentState.IDLE.value == "idle"
        assert AgentState.SPAWNED.value == "spawned"
        assert AgentState.WORKING.value == "working"
        assert AgentState.WAITING.value == "waiting"
        assert AgentState.COMPLETED.value == "completed"
        assert AgentState.FAILED.value == "failed"
        assert AgentState.DESTROYED.value == "destroyed"
