"""Tests for Agent Module"""
import pytest
from agent import AgentCore, AgentState, Task


class TestAgentCore:
    """Test AgentCore"""

    def test_agent_creation(self):
        """Test agent creation"""
        agent = AgentCore("test_agent")
        assert agent.name == "test_agent"
        assert agent.state == AgentState.IDLE

    def test_register_tool(self):
        """Test tool registration"""
        agent = AgentCore("test")

        def dummy_tool(x):
            return x * 2

        agent.register_tool("double", dummy_tool)
        assert "double" in agent.tools

    def test_set_llm_provider(self):
        """Test LLM provider setting"""
        agent = AgentCore("test")

        class DummyProvider:
            async def generate(self, prompt):
                return "response"

        provider = DummyProvider()
        agent.set_llm_provider(provider)
        assert agent.llm_provider is not None


class TestTask:
    """Test Task"""

    def test_task_creation(self):
        """Test task creation"""
        task = Task("task_1", "Test task", priority=8)
        assert task.id == "task_1"
        assert task.description == "Test task"
        assert task.priority == 8
        assert task.status == "pending"

    def test_task_to_dict(self):
        """Test task serialization"""
        task = Task("task_1", "Test task")
        data = task.to_dict()
        assert data["id"] == "task_1"
        assert data["status"] == "pending"
