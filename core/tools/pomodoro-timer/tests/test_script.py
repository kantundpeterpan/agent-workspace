"""Tests for pomodoro timer script."""

import json
import os
import signal
import sys
import time as time_module
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

# Import after path is set in conftest
import script
from script import (
    Timer,
    TimerData,
    start,
    status,
    stop,
    pause,
    resume,
    status_poller,
)

# For path helper functions, we'll access them through the script module
# to ensure mocks work correctly


class TestPathHelpers:
    """Test path helper functions."""

    def test_access_timer_base_returns_correct_path(
        self, mock_timer_paths, sample_session_id
    ):
        """Test that access_timer_base returns the expected base path."""
        # When using the mock_timer_paths fixture, the functions are already patched
        # So calling them should return paths in the temp directory
        base_path = script.access_timer_base(sample_session_id)
        expected = mock_timer_paths / f"opencode-pomodoro-{sample_session_id}"
        assert base_path == expected

    def test_access_timer_file_returns_json_path(
        self, mock_timer_paths, sample_session_id
    ):
        """Test that access_timer_file returns path with .json suffix."""
        timer_file = script.access_timer_file(sample_session_id)
        expected = mock_timer_paths / f"opencode-pomodoro-{sample_session_id}.json"
        assert timer_file == expected
        assert timer_file.suffix == ".json"

    def test_access_pid_file_returns_pid_path(
        self, mock_timer_paths, sample_session_id
    ):
        """Test that access_pid_file returns path with .pid suffix."""
        pid_file = script.access_pid_file(sample_session_id)
        expected = mock_timer_paths / f"opencode-pomodoro-{sample_session_id}.pid"
        assert pid_file == expected
        assert pid_file.suffix == ".pid"


class TestStart:
    """Test the start function."""

    def test_start_creates_timer_file(
        self, mock_timer_paths, frozen_time, sample_session_id
    ):
        """Test that start creates a timer file with correct data."""
        frozen_time["set"](1000.0)

        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            result = start(sample_session_id, duration=25.0, phase="implement")

        timer_file = script.access_timer_file(sample_session_id)
        assert timer_file.exists()

        # Verify file contents
        saved_data = json.loads(timer_file.read_text())
        assert saved_data["session_id"] == sample_session_id
        assert saved_data["data"]["status"] == "running"
        assert saved_data["data"]["phase"] == "implement"
        assert saved_data["data"]["duration"] == 25.0
        assert saved_data["data"]["end_time"] == 1000.0 + (25 * 60)

    def test_start_returns_correct_data(
        self, mock_timer_paths, frozen_time, sample_session_id
    ):
        """Test that start returns correct status information."""
        frozen_time["set"](1000.0)

        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            result = start(sample_session_id, duration=25.0, phase="plan")

        assert result["status"] == "started"
        assert result["pid"] == 12345
        assert "log" in result

    def test_start_launches_poller_subprocess(
        self, mock_timer_paths, frozen_time, sample_session_id
    ):
        """Test that start launches the status_poller subprocess."""
        frozen_time["set"](1000.0)

        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            start(sample_session_id, duration=25.0)

        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        assert "status_poller" in call_args[0][0]
        assert "--session_id" in call_args[0][0]
        assert sample_session_id in call_args[0][0]

    def test_start_creates_pid_file(
        self, mock_timer_paths, frozen_time, sample_session_id
    ):
        """Test that start creates a PID file for the poller."""
        frozen_time["set"](1000.0)

        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            start(sample_session_id, duration=25.0)

        pid_file = script.access_pid_file(sample_session_id)
        assert pid_file.exists()
        assert pid_file.read_text() == "12345"


class TestStatus:
    """Test the status function."""

    def test_status_idle_when_no_timer(self, mock_timer_paths, sample_session_id):
        """Test that status returns idle when no timer exists."""
        result = status(sample_session_id)

        assert result["status"] == "idle"
        assert "No active timer" in result["message"]

    def test_status_running_with_time_remaining(
        self, mock_timer_paths, frozen_time, sample_session_id
    ):
        """Test status returns running with correct remaining time."""
        frozen_time["set"](1000.0)

        # Create a timer with 25 minutes duration
        timer_data = {
            "session_id": sample_session_id,
            "data": {
                "status": "running",
                "phase": "implement",
                "message": "Test",
                "duration": 25.0,
                "end_time": 1000.0 + (25 * 60),
                "remaining": 25.0 * 60,
            },
        }

        timer_file = script.access_timer_file(sample_session_id)
        timer_file.write_text(json.dumps(timer_data))

        # Advance time by 5 minutes
        frozen_time["advance"](5 * 60)

        result = status(sample_session_id)

        assert result["status"] == "running"
        assert result["phase"] == "implement"
        assert result["remaining"] == pytest.approx(20 * 60, rel=1e-3)
        assert "20:00" in result["message"] or "20" in result["message"]

    def test_status_complete_when_timer_expires(
        self, mock_timer_paths, frozen_time, sample_session_id
    ):
        """Test status returns complete when timer has expired."""
        frozen_time["set"](1000.0)

        timer_data = {
            "session_id": sample_session_id,
            "data": {
                "status": "running",
                "phase": "review",
                "message": "Test",
                "duration": 25.0,
                "end_time": 1000.0 + (25 * 60),
                "remaining": 25.0 * 60,
            },
        }

        timer_file = script.access_timer_file(sample_session_id)
        timer_file.write_text(json.dumps(timer_data))

        # Advance time past the end
        frozen_time["advance"](30 * 60)

        on_finish_mock = MagicMock()
        result = status(sample_session_id, on_finish=on_finish_mock)

        assert result["status"] == "complete"
        assert "complete" in result["message"].lower()
        assert result["phase"] == "review"
        on_finish_mock.assert_called_once()

    def test_status_cleans_up_files_on_completion(
        self, mock_timer_paths, frozen_time, sample_session_id
    ):
        """Test that status cleans up timer and pid files when timer completes."""
        frozen_time["set"](1000.0)

        timer_data = {
            "session_id": sample_session_id,
            "data": {
                "status": "running",
                "phase": "implement",
                "message": "Test",
                "duration": 25.0,
                "end_time": 1000.0 + (25 * 60),
                "remaining": 25.0 * 60,
            },
        }

        timer_file = script.access_timer_file(sample_session_id)
        timer_file.write_text(json.dumps(timer_data))

        pid_file = script.access_pid_file(sample_session_id)
        pid_file.write_text("12345")

        # Advance time past the end
        frozen_time["advance"](30 * 60)

        status(sample_session_id)

        assert not timer_file.exists()
        assert not pid_file.exists()

    def test_status_paused(self, mock_timer_paths, frozen_time, sample_session_id):
        """Test status returns paused when timer is paused."""
        frozen_time["set"](1000.0)

        timer_data = {
            "session_id": sample_session_id,
            "data": {
                "status": "paused",
                "phase": "plan",
                "message": "Test",
                "duration": 25.0,
                "end_time": 1000.0 + (25 * 60),
                "remaining": 900.0,  # 15 minutes remaining
            },
        }

        timer_file = script.access_timer_file(sample_session_id)
        timer_file.write_text(json.dumps(timer_data))

        result = status(sample_session_id)

        assert result["status"] == "paused"
        assert result["phase"] == "plan"
        assert result["remaining"] == 900.0


class TestStop:
    """Test the stop function."""

    def test_stop_removes_timer_file(self, mock_timer_paths, sample_session_id):
        """Test that stop removes the timer file."""
        timer_file = script.access_timer_file(sample_session_id)
        timer_file.write_text('{"test": "data"}')

        with patch("os.kill"):
            result = stop(sample_session_id)

        assert not timer_file.exists()
        assert result["status"] == "stopped"

    def test_stop_removes_pid_file(self, mock_timer_paths, sample_session_id):
        """Test that stop removes the PID file."""
        timer_file = script.access_timer_file(sample_session_id)
        timer_file.write_text('{"test": "data"}')

        pid_file = script.access_pid_file(sample_session_id)
        pid_file.write_text("12345")

        with patch("os.kill"):
            result = stop(sample_session_id)

        assert not pid_file.exists()
        assert result["status"] == "stopped"

    def test_stop_kills_poller_process(self, mock_timer_paths, sample_session_id):
        """Test that stop kills the poller process."""
        timer_file = script.access_timer_file(sample_session_id)
        timer_file.write_text('{"test": "data"}')

        pid_file = script.access_pid_file(sample_session_id)
        poller_pid = 12345
        pid_file.write_text(str(poller_pid))

        with patch("os.kill") as mock_kill:
            stop(sample_session_id)

        mock_kill.assert_called_once_with(poller_pid, signal.SIGTERM)

    def test_stop_handles_missing_pid_file(self, mock_timer_paths, sample_session_id):
        """Test that stop works when PID file doesn't exist."""
        timer_file = script.access_timer_file(sample_session_id)
        timer_file.write_text('{"test": "data"}')

        result = stop(sample_session_id)

        assert not timer_file.exists()
        assert result["status"] == "stopped"

    def test_stop_handles_dead_process(self, mock_timer_paths, sample_session_id):
        """Test that stop handles already-dead poller process gracefully."""
        timer_file = script.access_timer_file(sample_session_id)
        timer_file.write_text('{"test": "data"}')

        pid_file = script.access_pid_file(sample_session_id)
        pid_file.write_text("99999")

        with patch("os.kill", side_effect=ProcessLookupError()):
            result = stop(sample_session_id)

        assert not timer_file.exists()
        assert not pid_file.exists()
        assert result["status"] == "stopped"

    def test_stop_handles_invalid_pid(self, mock_timer_paths, sample_session_id):
        """Test that stop handles invalid PID in file."""
        timer_file = script.access_timer_file(sample_session_id)
        timer_file.write_text('{"test": "data"}')

        pid_file = script.access_pid_file(sample_session_id)
        pid_file.write_text("not_a_valid_pid")

        result = stop(sample_session_id)

        assert not timer_file.exists()
        assert not pid_file.exists()
        assert result["status"] == "stopped"

    def test_stop_handles_kill_error(self, mock_timer_paths, sample_session_id):
        """Test that stop handles errors when killing process."""
        timer_file = script.access_timer_file(sample_session_id)
        timer_file.write_text('{"test": "data"}')

        pid_file = script.access_pid_file(sample_session_id)
        pid_file.write_text("12345")

        with patch("os.kill", side_effect=PermissionError("Permission denied")):
            result = stop(sample_session_id)

        assert not timer_file.exists()
        assert not pid_file.exists()
        assert result["status"] == "stopped"

    def test_stop_idle_when_no_timer_or_pid(self, mock_timer_paths, sample_session_id):
        """Test that stop returns idle when no timer or PID exists."""
        result = stop(sample_session_id)

        assert result["status"] == "idle"
        assert "No active timer" in result["message"]

    def test_stop_still_cleans_up_if_only_pid_exists(
        self, mock_timer_paths, sample_session_id
    ):
        """Test that stop cleans up PID file even if timer file is missing."""
        pid_file = script.access_pid_file(sample_session_id)
        pid_file.write_text("12345")

        with patch("os.kill"):
            result = stop(sample_session_id)

        assert not pid_file.exists()
        assert result["status"] == "stopped"


class TestPause:
    """Test the pause function."""

    def test_pause_updates_timer_status(
        self, mock_timer_paths, frozen_time, sample_session_id
    ):
        """Test that pause updates the timer status and remaining time."""
        frozen_time["set"](1000.0)

        # Create a running timer
        timer_data = {
            "session_id": sample_session_id,
            "data": {
                "status": "running",
                "phase": "implement",
                "message": "Test",
                "duration": 25.0,
                "end_time": 1000.0 + (25 * 60),
                "remaining": 25.0 * 60,
            },
        }

        timer_file = script.access_timer_file(sample_session_id)
        timer_file.write_text(json.dumps(timer_data))

        # Advance 10 minutes
        frozen_time["advance"](10 * 60)

        result = pause(sample_session_id)

        # Check returned result
        assert result["status"] == "paused"
        assert result["remaining"] == pytest.approx(15 * 60, rel=1e-3)

        # Check saved file
        saved = json.loads(timer_file.read_text())
        assert saved["data"]["status"] == "paused"
        assert saved["data"]["remaining"] == pytest.approx(15 * 60, rel=1e-3)

    def test_pause_idle_when_no_timer(self, mock_timer_paths, sample_session_id):
        """Test that pause returns idle when no timer exists."""
        result = pause(sample_session_id)

        assert result["status"] == "idle"
        assert "No active timer" in result["message"]


class TestResume:
    """Test the resume function."""

    def test_resume_updates_timer(
        self, mock_timer_paths, frozen_time, sample_session_id
    ):
        """Test that resume updates end_time and restores running status."""
        frozen_time["set"](2000.0)

        # Create a paused timer with 10 minutes remaining
        timer_data = {
            "session_id": sample_session_id,
            "data": {
                "status": "paused",
                "phase": "review",
                "message": "Test",
                "duration": 25.0,
                "end_time": 1000.0,  # Old end time
                "remaining": 600.0,  # 10 minutes
            },
        }

        timer_file = script.access_timer_file(sample_session_id)
        timer_file.write_text(json.dumps(timer_data))

        result = resume(sample_session_id)

        # Check returned result
        assert result["status"] == "running"
        assert result["remaining"] == 600.0

        # Check saved file
        saved = json.loads(timer_file.read_text())
        assert saved["data"]["status"] == "running"
        assert saved["data"]["end_time"] == 2000.0 + 600.0

    def test_resume_error_when_not_paused(
        self, mock_timer_paths, frozen_time, sample_session_id
    ):
        """Test that resume returns error when timer is not paused."""
        frozen_time["set"](1000.0)

        # Create a running timer (not paused)
        timer_data = {
            "session_id": sample_session_id,
            "data": {
                "status": "running",
                "phase": "implement",
                "message": "Test",
                "duration": 25.0,
                "end_time": 1000.0 + (25 * 60),
                "remaining": 25.0 * 60,
            },
        }

        timer_file = script.access_timer_file(sample_session_id)
        timer_file.write_text(json.dumps(timer_data))

        result = resume(sample_session_id)

        assert result["status"] == "running"  # Current status
        assert "not paused" in result["message"].lower()

    def test_resume_idle_when_no_timer(self, mock_timer_paths, sample_session_id):
        """Test that resume returns idle when no timer exists."""
        result = resume(sample_session_id)

        assert result["status"] == "idle"
        assert "No active timer" in result["message"]


class TestStatusPoller:
    """Test the status_poller function."""

    def test_poller_exits_if_another_instance_running(
        self, mock_timer_paths, sample_session_id
    ):
        """Test that poller exits if another instance is already running."""
        # Create a PID file pointing to a different process (not current)
        other_pid = 99999
        pid_file = script.access_pid_file(sample_session_id)
        pid_file.write_text(str(other_pid))

        # Mock os.kill to simulate that the process is alive
        with patch("os.kill") as mock_kill:
            mock_kill.return_value = None  # Process is alive

            # Poller should exit immediately without doing anything
            status_poller(sample_session_id, interval_s=1)

            mock_kill.assert_called_once_with(other_pid, 0)

    def test_poller_creates_pid_file(self, mock_timer_paths, sample_session_id):
        """Test that poller creates a PID file when starting."""
        pid_file = script.access_pid_file(sample_session_id)
        pid_created = []

        # Mock time.sleep to check that PID file was created before cleanup
        def mock_sleep(seconds):
            # Check that PID file was created during first iteration
            if not pid_created and pid_file.exists():
                pid_created.append(True)
                assert pid_file.read_text() == str(os.getpid())
            raise SystemExit(0)

        with (
            patch("time.sleep", side_effect=mock_sleep),
            patch("script.status") as mock_status,
        ):
            mock_status.return_value = {"status": "running"}

            with pytest.raises(SystemExit):
                status_poller(sample_session_id, interval_s=1)

        # Verify the PID file was created during execution
        assert pid_created, "PID file was not created during poller execution"

    def test_poller_calls_status_periodically(
        self, mock_timer_paths, frozen_time, sample_session_id
    ):
        """Test that poller calls status function at intervals."""
        frozen_time["set"](1000.0)

        # Create a running timer
        timer_data = {
            "session_id": sample_session_id,
            "data": {
                "status": "running",
                "phase": "implement",
                "message": "Test",
                "duration": 25.0,
                "end_time": 1000.0 + (25 * 60),
                "remaining": 25.0 * 60,
            },
        }

        timer_file = script.access_timer_file(sample_session_id)
        timer_file.write_text(json.dumps(timer_data))

        call_count = [0]

        def mock_sleep(seconds):
            call_count[0] += 1
            if call_count[0] >= 3:
                raise SystemExit(0)

        with (
            patch("time.sleep", side_effect=mock_sleep),
            patch("script.status") as mock_status,
        ):
            mock_status.return_value = {"status": "running"}

            with pytest.raises(SystemExit):
                status_poller(sample_session_id, interval_s=15)

        # Status should be called multiple times
        assert mock_status.call_count >= 3

    def test_poller_cleans_up_on_exit(self, mock_timer_paths, sample_session_id):
        """Test that poller cleans up PID file on exit."""
        pid_file = script.access_pid_file(sample_session_id)

        with (
            patch("time.sleep", side_effect=SystemExit(0)),
            patch("script.status") as mock_status,
        ):
            mock_status.return_value = {"status": "running"}

            with pytest.raises(SystemExit):
                status_poller(sample_session_id, interval_s=1)

        # PID file should be cleaned up
        assert not pid_file.exists()

    def test_poller_handles_signals(self, mock_timer_paths, sample_session_id):
        """Test that poller sets up signal handlers."""
        with (
            patch("signal.signal") as mock_signal,
            patch("time.sleep", side_effect=SystemExit(0)),
            patch("script.status"),
        ):
            with pytest.raises(SystemExit):
                status_poller(sample_session_id, interval_s=1)

        # Should have set up SIGINT and SIGTERM handlers
        calls = mock_signal.call_args_list
        signals = [
            call[0][0]
            for call in calls
            if hasattr(call[0][0], "value") or isinstance(call[0][0], int)
        ]
        assert signal.SIGINT in signals or any(
            getattr(c[0][0], "name", "") == "SIGINT" for c in calls
        )


class TestDataModels:
    """Test Pydantic data models."""

    def test_timer_data_validation(self):
        """Test TimerData validates required fields."""
        data = {
            "status": "running",
            "phase": "implement",
            "message": "Test timer",
            "duration": 25.0,
            "end_time": 1000.0,
            "remaining": 1500.0,
        }

        timer_data = TimerData.model_validate(data)

        assert timer_data.status == "running"
        assert timer_data.phase == "implement"
        assert timer_data.duration == 25.0

    def test_timer_data_invalid_status(self):
        """Test TimerData rejects invalid status values."""
        data = {
            "status": "invalid_status",
            "phase": "implement",
            "message": "Test",
            "duration": 25.0,
            "end_time": 1000.0,
            "remaining": 1500.0,
        }

        with pytest.raises(Exception):
            TimerData.model_validate(data)

    def test_timer_data_invalid_phase(self):
        """Test TimerData rejects invalid phase values."""
        data = {
            "status": "running",
            "phase": "invalid_phase",
            "message": "Test",
            "duration": 25.0,
            "end_time": 1000.0,
            "remaining": 1500.0,
        }

        with pytest.raises(Exception):
            TimerData.model_validate(data)

    def test_timer_model_serialization(self, sample_session_id):
        """Test Timer model serializes and deserializes correctly."""
        timer_data = {
            "session_id": sample_session_id,
            "data": {
                "status": "running",
                "phase": "implement",
                "message": "Test",
                "duration": 25.0,
                "end_time": 1000.0,
                "remaining": 1500.0,
            },
        }

        timer = Timer.model_validate(timer_data)
        serialized = timer.model_dump_json()
        deserialized = Timer.model_validate_json(serialized)

        assert deserialized.session_id == sample_session_id
        assert deserialized.data.status == "running"
        assert deserialized.data.phase == "implement"


class TestIntegration:
    """Integration tests for full timer lifecycle."""

    def test_full_timer_lifecycle(
        self, mock_timer_paths, frozen_time, sample_session_id
    ):
        """Test complete timer lifecycle: start -> pause -> resume -> stop."""
        frozen_time["set"](1000.0)

        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            # Start the timer
            result = start(sample_session_id, duration=25.0, phase="implement")
            assert result["status"] == "started"

            # Check timer is running
            frozen_time["advance"](5 * 60)
            status_result = status(sample_session_id)
            assert status_result["status"] == "running"

            # Pause the timer
            pause_result = pause(sample_session_id)
            assert pause_result["status"] == "paused"
            assert pause_result["remaining"] == pytest.approx(20 * 60, rel=1e-3)

            # Wait and check status (should still show paused with same remaining)
            frozen_time["advance"](10 * 60)
            status_result = status(sample_session_id)
            assert status_result["status"] == "paused"
            assert status_result["remaining"] == pytest.approx(20 * 60, rel=1e-3)

            # Resume the timer
            resume_result = resume(sample_session_id)
            assert resume_result["status"] == "running"

            # Check timer is running again
            frozen_time["advance"](5 * 60)
            status_result = status(sample_session_id)
            assert status_result["status"] == "running"

            # Stop the timer
            with patch("os.kill"):
                stop_result = stop(sample_session_id)
            assert stop_result["status"] == "stopped"

            # Verify timer file and PID file are gone
            assert not script.access_timer_file(sample_session_id).exists()
            assert not script.access_pid_file(sample_session_id).exists()

    def test_timer_completion(self, mock_timer_paths, frozen_time, sample_session_id):
        """Test timer completes and cleans up automatically."""
        frozen_time["set"](1000.0)

        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_popen.return_value = mock_proc

            # Start a 5 minute timer
            start(sample_session_id, duration=5.0, phase="break")

            # Advance past the end
            frozen_time["advance"](6 * 60)

            on_finish_mock = MagicMock()
            result = status(sample_session_id, on_finish=on_finish_mock)

            assert result["status"] == "complete"
            on_finish_mock.assert_called_once()
            assert not script.access_timer_file(sample_session_id).exists()
