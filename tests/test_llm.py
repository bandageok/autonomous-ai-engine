"""Tests for LLM Module"""
import pytest
from llm.provider import BaseLLM, OllamaLLM


class TestOllamaLLM:
    """Test OllamaLLM"""

    def test_ollama_creation(self):
        """Test OllamaLLM creation"""
        llm = OllamaLLM(model="qwen2.5:7b")
        assert llm.model == "qwen2.5:7b"
        assert llm.base_url == "http://localhost:11434"

    def test_default_options(self):
        """Test default options"""
        llm = OllamaLLM()
        assert llm.default_options["temperature"] == 0.7
        assert llm.default_options["num_predict"] == 2048

    def test_custom_options(self):
        """Test custom options"""
        llm = OllamaLLM()
        # Just verify it accepts options
        assert hasattr(llm, 'default_options')


class TestBaseLLM:
    """Test BaseLLM abstract class"""

    def test_abstract_methods(self):
        """Test BaseLLM has abstract methods"""
        # BaseLLM is abstract, verify it exists
        assert BaseLLM is not None
        assert hasattr(BaseLLM, 'generate')
        assert hasattr(BaseLLM, 'chat')
