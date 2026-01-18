"""
Unit tests for agent timeout functionality
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.agents.base import (
    Agent,
    AgentContext,
    AgentState,
    DEFAULT_EXECUTION_TIMEOUT,
    MAX_ACTION_LOG_SIZE,
    MAX_STATE_HISTORY_SIZE,
)


class TestAgentTimeout:
    """Tests for agent execution timeout"""

    @pytest.mark.asyncio
    async def test_execute_completes_within_timeout(self):
        """Test that execution completes when under timeout"""
        agent = Agent(role={"name": "test_agent"})

        context = AgentContext(task="Simple task")

        result = await agent.execute(context, timeout_seconds=5.0)

        assert result["success"]
        assert agent.state == AgentState.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_timeout_triggers(self):
        """Test that timeout triggers when execution is slow"""
        agent = Agent(role={"name": "slow_agent"})

        # Create a model that takes too long
        async def slow_generate(messages):
            await asyncio.sleep(2.0)
            return "Response"

        mock_model = MagicMock()
        mock_model.generate = slow_generate
        agent.model = mock_model

        context = AgentContext(task="Slow task")

        result = await agent.execute(context, timeout_seconds=0.1)

        assert not result["success"]
        assert "timed out" in result["error"].lower()
        assert agent.state == AgentState.FAILED

    @pytest.mark.asyncio
    async def test_execute_default_timeout(self):
        """Test that default timeout is used"""
        agent = Agent(role={"name": "test_agent"})
        context = AgentContext(task="Test task")

        # Execute without specifying timeout - should use default
        result = await agent.execute(context)

        assert result["success"]

    @pytest.mark.asyncio
    async def test_timeout_logged_in_action_log(self):
        """Test that timeout is logged in action log"""
        agent = Agent(role={"name": "test_agent"})

        async def slow_generate(messages):
            await asyncio.sleep(1.0)
            return "Response"

        mock_model = MagicMock()
        mock_model.generate = slow_generate
        agent.model = mock_model

        context = AgentContext(task="Test")

        await agent.execute(context, timeout_seconds=0.05)

        # Check that timeout was logged
        timeout_actions = [
            a for a in agent.action_log
            if a["action"] == "execute_timeout"
        ]
        assert len(timeout_actions) == 1
        assert timeout_actions[0]["details"]["timeout_seconds"] == 0.05

    @pytest.mark.asyncio
    async def test_timeout_state_transition(self):
        """Test state transitions on timeout"""
        agent = Agent(role={"name": "test_agent"})

        async def slow_generate(messages):
            await asyncio.sleep(1.0)
            return "Response"

        mock_model = MagicMock()
        mock_model.generate = slow_generate
        agent.model = mock_model

        context = AgentContext(task="Test")

        await agent.execute(context, timeout_seconds=0.05)

        # Check state history includes FAILED transition
        states = [s["to_state"] for s in agent.state_history]
        assert AgentState.FAILED.value in states


class TestAgentMemoryManagement:
    """Tests for agent memory management (bounded logs)"""

    def test_state_history_bounded(self):
        """Test that state_history is bounded"""
        agent = Agent(role={"name": "test_agent"})

        # Generate more state changes than the limit
        for i in range(MAX_STATE_HISTORY_SIZE + 50):
            agent._log_state_change(AgentState.WORKING)
            agent._log_state_change(AgentState.IDLE)

        assert len(agent.state_history) <= MAX_STATE_HISTORY_SIZE

    def test_action_log_bounded(self):
        """Test that action_log is bounded"""
        agent = Agent(role={"name": "test_agent"})

        # Generate more actions than the limit
        for i in range(MAX_ACTION_LOG_SIZE + 50):
            agent._log_action("test_action", {"index": i})

        assert len(agent.action_log) <= MAX_ACTION_LOG_SIZE

    def test_state_history_keeps_recent(self):
        """Test that state_history keeps most recent entries"""
        agent = Agent(role={"name": "test_agent"})

        # Generate numbered states
        for i in range(MAX_STATE_HISTORY_SIZE + 10):
            # We can't add custom data to state changes, so we just verify
            # the most recent ones are kept
            agent._log_state_change(AgentState.WORKING)

        # After exceeding the limit, we should have exactly MAX_STATE_HISTORY_SIZE
        # entries, and they should be the most recent ones
        assert len(agent.state_history) == MAX_STATE_HISTORY_SIZE

    def test_action_log_keeps_recent(self):
        """Test that action_log keeps most recent entries"""
        agent = Agent(role={"name": "test_agent"})

        # Generate numbered actions
        for i in range(MAX_ACTION_LOG_SIZE + 10):
            agent._log_action("action", {"index": i})

        # The last entry should have the highest index
        assert agent.action_log[-1]["details"]["index"] == MAX_ACTION_LOG_SIZE + 9

        # First entry should NOT be index 0 (it was trimmed)
        assert agent.action_log[0]["details"]["index"] > 0

    def test_initial_state_logged(self):
        """Test that initial IDLE state is logged"""
        agent = Agent(role={"name": "test_agent"})

        assert len(agent.state_history) >= 1
        assert agent.state_history[0]["to_state"] == AgentState.IDLE.value


class TestAgentExecuteWithModel:
    """Tests for agent execution with model"""

    @pytest.mark.asyncio
    async def test_execute_without_model(self):
        """Test execution without a model attached"""
        agent = Agent(role={"name": "test_agent"})
        context = AgentContext(task="Test task")

        result = await agent.execute(context)

        assert result["success"]
        assert "[No model attached]" in result["response"]

    @pytest.mark.asyncio
    async def test_execute_with_model(self):
        """Test execution with a model attached"""
        agent = Agent(role={"name": "test_agent"})

        async def mock_generate(messages):
            return "Model response"

        mock_model = MagicMock()
        mock_model.generate = mock_generate
        agent.model = mock_model

        context = AgentContext(task="Test task")

        result = await agent.execute(context)

        assert result["success"]
        assert result["response"] == "Model response"

    @pytest.mark.asyncio
    async def test_execute_handles_model_exception(self):
        """Test execution handles model exceptions"""
        agent = Agent(role={"name": "test_agent"})

        async def failing_generate(messages):
            raise RuntimeError("Model error")

        mock_model = MagicMock()
        mock_model.generate = failing_generate
        agent.model = mock_model

        context = AgentContext(task="Test task")

        result = await agent.execute(context)

        assert not result["success"]
        assert "Model error" in result["error"]
        assert agent.state == AgentState.FAILED


class TestAgentConstants:
    """Tests for agent constants"""

    def test_default_timeout_value(self):
        """Test default timeout is reasonable"""
        assert DEFAULT_EXECUTION_TIMEOUT == 60.0  # 1 minute

    def test_max_state_history_value(self):
        """Test max state history is reasonable"""
        assert MAX_STATE_HISTORY_SIZE == 100

    def test_max_action_log_value(self):
        """Test max action log is reasonable"""
        assert MAX_ACTION_LOG_SIZE == 100
