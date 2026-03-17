"""Tests for Scheduler Module"""
import pytest
from scheduler.task_scheduler import TaskScheduler, ScheduledTask


class TestTaskScheduler:
    """Test TaskScheduler"""

    def test_scheduler_creation(self):
        """Test creating scheduler"""
        scheduler = TaskScheduler()
        assert scheduler is not None
        assert hasattr(scheduler, 'tasks')

    def test_scheduler_run(self):
        """Test scheduler has run method"""
        scheduler = TaskScheduler()
        assert hasattr(scheduler, 'run')
        assert hasattr(scheduler, 'schedule')
        assert hasattr(scheduler, 'unschedule')


class TestScheduledTask:
    """Test ScheduledTask"""

    def test_task_creation(self):
        """Test creating scheduled task"""
        def dummy_task():
            return "done"
        
        task = ScheduledTask(
            id="test_1",
            name="test",
            func=dummy_task
        )
        assert task.name == "test"
        assert task.id == "test_1"
