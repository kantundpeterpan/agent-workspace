"""Pytest configuration and fixtures for pomodoro timer tests."""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path to import script
sys.path.insert(0, str(Path(__file__).parent.parent))

from script import (
    Timer,
    TimerData,
    access_timer_base,
    access_timer_file,
    access_pid_file,
)


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_timer_paths(temp_dir):
    """Mock all timer path functions to use temp directory."""

    def make_base(session_id: str) -> Path:
        return temp_dir / f"opencode-pomodoro-{session_id}"

    def make_timer_file(session_id: str) -> Path:
        return make_base(session_id).with_suffix(".json")

    def make_pid_file(session_id: str) -> Path:
        return make_base(session_id).with_suffix(".pid")

    with (
        patch("script.access_timer_base", side_effect=make_base),
        patch("script.access_timer_file", side_effect=make_timer_file),
        patch("script.access_pid_file", side_effect=make_pid_file),
    ):
        yield temp_dir


@pytest.fixture
def frozen_time():
    """Mock time.time() to return a fixed value that can be advanced."""
    current_time = 1000.0

    def mock_time():
        return current_time

    def advance_time(seconds: float):
        nonlocal current_time
        current_time += seconds

    def set_time(new_time: float):
        nonlocal current_time
        current_time = new_time

    with (
        patch("script.time.time", side_effect=mock_time),
        patch("time.time", side_effect=mock_time),
    ):
        yield {
            "time": mock_time,
            "advance": advance_time,
            "set": set_time,
            "current": lambda: current_time,
        }


@pytest.fixture
def sample_session_id():
    """Provide a consistent session ID for tests."""
    return "test-session-123"


@pytest.fixture
def sample_timer_data(sample_session_id):
    """Provide sample timer data for testing."""
    return {
        "session_id": sample_session_id,
        "data": {
            "status": "running",
            "phase": "implement",
            "message": "Test timer",
            "duration": 25.0,
            "end_time": 1000.0 + (25 * 60),
            "remaining": 25.0 * 60,
        },
    }


@pytest.fixture
def cleanup_timer_files(mock_timer_paths):
    """Cleanup any timer files created during tests."""
    created_files = []

    yield created_files

    # Cleanup after test
    for file_path in created_files:
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass
