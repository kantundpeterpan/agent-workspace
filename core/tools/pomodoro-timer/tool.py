#!/usr/bin/env python3
"""Pomodoro Timer for Pair Programming Sessions."""

import json
import time
from pathlib import Path
from typing import Literal
import fire


TIMER_FILE = Path("/tmp/agent-pomodoro.json")


class PomodoroTimer:
    """Manages timed coding rounds with notifications for pair programming sessions."""

    def start(self, duration: int = 25, phase: str = "implement") -> str:
        """Start a new pomodoro timer.
        
        Args:
            duration: Duration in minutes (default: 25)
            phase: Session phase label (brainstorm, plan, implement, review, break)
            
        Returns:
            Status message
        """
        end_time = int(time.time()) + (duration * 60)
        timer_data = {
            "phase": phase,
            "duration": duration,
            "end_time": end_time,
            "status": "running"
        }
        
        TIMER_FILE.write_text(json.dumps(timer_data))
        return f"⏱️  Timer started: {duration} min ({phase} phase)"

    def status(self) -> str:
        """Check the status of the current timer.
        
        Returns:
            Current timer status with remaining time
        """
        if not TIMER_FILE.exists():
            return "No active timer"
        
        timer_data = json.loads(TIMER_FILE.read_text())
        current_time = int(time.time())
        
        if timer_data["status"] == "paused":
            return f"⏸️  Timer paused in {timer_data['phase']} phase"
        
        remaining = timer_data["end_time"] - current_time
        
        if remaining <= 0:
            TIMER_FILE.unlink()
            return f"✅ Timer complete! ({timer_data['phase']} phase finished)"
        
        minutes = remaining // 60
        seconds = remaining % 60
        return f"⏱️  {minutes}:{seconds:02d} remaining ({timer_data['phase']} phase)"

    def stop(self) -> str:
        """Stop the current timer.
        
        Returns:
            Confirmation message
        """
        if TIMER_FILE.exists():
            TIMER_FILE.unlink()
            return "🛑 Timer stopped"
        return "No active timer"

    def pause(self) -> str:
        """Pause the current timer.
        
        Returns:
            Confirmation message
        """
        if not TIMER_FILE.exists():
            return "No active timer"
        
        timer_data = json.loads(TIMER_FILE.read_text())
        current_time = int(time.time())
        remaining = timer_data["end_time"] - current_time
        
        timer_data["status"] = "paused"
        timer_data["remaining"] = remaining
        
        TIMER_FILE.write_text(json.dumps(timer_data))
        return "⏸️  Timer paused"

    def resume(self) -> str:
        """Resume a paused timer.
        
        Returns:
            Confirmation message
        """
        if not TIMER_FILE.exists():
            return "No active timer"
        
        timer_data = json.loads(TIMER_FILE.read_text())
        
        if timer_data["status"] != "paused":
            return "Timer is not paused"
        
        current_time = int(time.time())
        timer_data["end_time"] = current_time + timer_data.get("remaining", 0)
        timer_data["status"] = "running"
        
        TIMER_FILE.write_text(json.dumps(timer_data))
        return "▶️  Timer resumed"


def main():
    """CLI entry point using fire."""
    fire.Fire(PomodoroTimer)


if __name__ == "__main__":
    main()
