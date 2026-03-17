"""Tests for Database Module"""
import pytest
import tempfile
import os
from pathlib import Path
from db.database import Database, QueryBuilder, Model


class TestDatabase:
    """Test Database"""

    def test_database_creation(self):
        """Test database creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)
            assert str(db.db_path) == str(db_path)

    def test_connect(self):
        """Test database connection"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)
            db.connect()
            assert db.connection is not None
            db.close()

    def test_query_builder(self):
        """Test QueryBuilder"""
        qb = QueryBuilder("users")
        qb.where("age", ">", 18)
        qb.order("name", desc=True)
        qb.limit(10)

        assert "users" in qb.table
        assert len(qb.where_clauses) > 0


class TestModel:
    """Test Model base class"""

    def test_model_creation(self):
        """Test model creation"""
        model = Model()
        assert model.id == ""
