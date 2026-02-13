#!/usr/bin/env python3
"""Pomodoro Timer for Pair Programming Sessions."""

import json
import time
from pathlib import Path
from typing import Dict, Any


TIMER_FILE = Path("/tmp/agent-pomodoro.json")


def start(duration: int = 25, phase: str = "implement") -> Dict[str, Any]:
    """Start a new pomodoro timer.
    
    Args:
        duration: Duration in minutes (default: 25)
        phase: Session phase label (brainstorm, plan, implement, review, break)
        
    Returns:
        Timer status with confirmation message
    """
    end_time = int(time.time()) + (duration * 60)
    timer_data = {
        "phase": phase,
        "duration": duration,
        "end_time": end_time,
        "status": "running"
    }
    
    TIMER_FILE.write_text(json.dumps(timer_data))
    
    return {
        "status": "running",
        "message": f"⏱️  Timer started: {duration} min ({phase} phase)",
        "phase": phase,
        "remaining": duration * 60
    }


def status() -> Dict[str, Any]:
    """Check the status of the current timer.
    
    Returns:
        Current timer status with remaining time
    """
    if not TIMER_FILE.exists():
        return {
            "status": "idle",
            "message": "No active timer"
        }
    
    timer_data = json.loads(TIMER_FILE.read_text())
    current_time = int(time.time())
    
    if timer_data["status"] == "paused":
        return {
            "status": "paused",
            "message": f"⏸️  Timer paused in {timer_data['phase']} phase",
            "phase": timer_data["phase"],
            "remaining": timer_data.get("remaining", 0)
        }
    
    remaining = timer_data["end_time"] - current_time
    
    if remaining <= 0:
        TIMER_FILE.unlink()
        return {
            "status": "complete",
            "message": f"✅ Timer complete! ({timer_data['phase']} phase finished)",
            "phase": timer_data["phase"],
            "remaining": 0
        }
    
    minutes = remaining // 60
    seconds = remaining % 60
    
    return {
        "status": "running",
        "message": f"⏱️  {minutes}:{seconds:02d} remaining ({timer_data['phase']} phase)",
        "phase": timer_data["phase"],
        "remaining": remaining
    }


def stop() -> Dict[str, Any]:
    """Stop the current timer.
    
    Returns:
        Confirmation message
    """
    if TIMER_FILE.exists():
        TIMER_FILE.unlink()
        return {
            "status": "stopped",
            "message": "🛑 Timer stopped"
        }
    
    return {
        "status": "idle",
        "message": "No active timer"
    }


def pause() -> Dict[str, Any]:
    """Pause the current timer.
    
    Returns:
        Confirmation message
    """
    if not TIMER_FILE.exists():
        return {
            "status": "idle",
            "message": "No active timer"
        }
    
    timer_data = json.loads(TIMER_FILE.read_text())
    current_time = int(time.time())
    remaining = timer_data["end_time"] - current_time
    
    timer_data["status"] = "paused"
    timer_data["remaining"] = remaining
    
    TIMER_FILE.write_text(json.dumps(timer_data))
    
    return {
        "status": "paused",
        "message": "⏸️  Timer paused",
        "phase": timer_data["phase"],
        "remaining": remaining
    }


def resume() -> Dict[str, Any]:
    """Resume a paused timer.
    
    Returns:
        Confirmation message
    """
    if not TIMER_FILE.exists():
        return {
            "status": "idle",
            "message": "No active timer"
        }
    
    timer_data = json.loads(TIMER_FILE.read_text())
    
    if timer_data["status"] != "paused":
        return {
            "status": timer_data["status"],
            "message": "Timer is not paused"
        }
    
    current_time = int(time.time())
    remaining = timer_data.get("remaining", 0)
    timer_data["end_time"] = current_time + remaining
    timer_data["status"] = "running"
    
    TIMER_FILE.write_text(json.dumps(timer_data))
    
    return {
        "status": "running",
        "message": "▶️  Timer resumed",
        "phase": timer_data["phase"],
        "remaining": remaining
    }


if __name__ == "__main__":
    import fire
    fire.Fire()
