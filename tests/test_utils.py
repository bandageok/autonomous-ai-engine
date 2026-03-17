"""Tests for Utils Module"""
import pytest
from pathlib import Path
from utils.config import AppConfig, ConfigManager
from utils.helpers import generate_id, hash_text, ensure_dir
from utils.logger import get_logger, JSONFormatter
import tempfile
import os


class TestConfig:
    """Test Config"""

    def test_app_config_creation(self):
        """Test AppConfig creation"""
        config = AppConfig()
        assert config.app_name == "AIEngine"
        assert config.version == "0.1.0"

    def test_app_config_to_dict(self):
        """Test config serialization"""
        config = AppConfig()
        data = config.to_dict()
        assert "app_name" in data
        assert "version" in data


class TestHelpers:
    """Test Helpers"""

    def test_generate_id(self):
        """Test ID generation"""
        id1 = generate_id()
        id2 = generate_id()
        assert id1 != id2
        assert len(id1) > 0

    def test_hash_text(self):
        """Test text hashing"""
        hash1 = hash_text("test")
        hash2 = hash_text("test")
        hash3 = hash_text("different")
        assert hash1 == hash2
        assert hash1 != hash3

    def test_ensure_dir(self):
        """Test directory creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test" / "nested"
            ensure_dir(test_dir)
            assert test_dir.exists()


class TestLogger:
    """Test Logger"""

    def test_get_logger(self):
        """Test logger creation"""
        logger = get_logger("test")
        assert logger.name == "test"

    def test_json_formatter(self):
        """Test JSON formatter"""
        formatter = JSONFormatter()
        # Just verify it exists and has format method
        assert hasattr(formatter, 'format')
