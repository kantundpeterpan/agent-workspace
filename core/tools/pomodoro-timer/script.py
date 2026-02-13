#!/usr/bin/env python3
"""Pomodoro Timer for Pair Programming Sessions."""

import json
import time
from pathlib import Path
from typing import Dict, Any, Callable, Literal, Optional
import importlib.util

from pydantic import BaseModel


class TimerData(BaseModel):
    # Use 'status' to match the rest of the code which writes a 'status' field
    status: Literal["running", "paused"]
    phase: Literal["brainstorm", "plan", "implement", "review", "break"]
    message: str
    duration: float
    end_time: float
    remaining: float


class Timer(BaseModel):
    session_id: str
    data: TimerData


"""
1. [x] add sessionid to file name
2. [x] function to create/get tempfiles
3. function to notify opencode
4. need to adapt tool yaml definition with tool specific stuff (opencode: from_context: session_id) or match arguments against context (set get_from_context true in yaml definition)
4. on start launch and detach status poller with on_finish = notify_opencode(session_id)
"""

file_slug = "opencode-pomodoro-{session_id}"

oc_default_url = "http://localhost:4096"


def notify_opencode(
        session_id: str, message: str,
        model: Dict[str, str] = {'providerID':'github-copilot', 'modelID':'gpt-5-mini'}
    ):

    from opencode_ai import Opencode

    client = Opencode(base_url = oc_default_url, max_retries=1)

    client.session.prompt(
        id = session_id,
        parts = [{'type':'text', 'text':message}]
    )



def access_timer_file(session_id: str) -> Path:
    return Path(f"/tmp/{file_slug.format(session_id=session_id)}")

def status_poller(session_id: str, interval_s: int = 15):
    import time, os
    from functools import partial
    
    polling_func = partial(
        status, session_id = session_id,
        on_finish = partial(notify_opencode, session_id = session_id)
    )

    if os.fork() != 0:
        return

    while True:
        polling_func()
        time.sleep(interval_s)


def start(
    session_id: str, duration: float = 25, phase: str = "implement"
) -> Dict[str, Any]:
    """Start a new pomodoro timer.

    Args:
        session_id: opencode session id, OPTIONAL for agentic invocation -> use empty string
        duration: Duration in minutes (default: 25, accepts float)
        phase: Session phase label (brainstorm, plan, implement, review, break)

    Returns:
        Timer status with confirmation message
    """

    TIMER_FILE = access_timer_file(session_id)

    end_time = (time.time()) + (duration * 60)
    timer_data = {
        "phase": phase,
        "duration": duration,
        "remaining": duration,
        "end_time": end_time,
        "status": "running",
        "message": f"⏱️  Timer started: {duration} min ({phase} phase)",
    }

    timer = Timer(session_id=session_id, data=TimerData.model_validate(timer_data))

    # Persist the pydantic model as plain JSON
    TIMER_FILE.write_text(json.dumps(timer.model_dump()))

    from multiprocessing import Process

    poller = Process(target = status_poller, kwargs={"session_id":session_id})
    poller.start()    
    poller.join()

    print(json.dumps(timer.model_dump()))
    return json.dumps(timer.model_dump())


def status(
    session_id: str,
    on_finish: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    """Check the status of the current timer.

    Args:
        session_id: opencode session id, OPTIONAL for agentic invocation -> use empty string
        on_finish: Callable, called when timer has finished

    Returns:
        Current timer status with remaining time
    """

    TIMER_FILE = access_timer_file(session_id)

    if not TIMER_FILE.exists():
        return {"status": "idle", "message": "No active timer"}

    timer = Timer.model_validate_json(TIMER_FILE.read_text())
    current_time = (time.time())

    if timer.data.status == "paused":
        return {
            "status": "paused",
            "message": f"⏸️  Timer paused in {timer.data.phase} phase",
            "phase": timer.data.phase,
            "remaining": timer.data.get("remaining", 0),
        }

    remaining = timer.data.end_time - current_time

    if remaining <= 0:
        try:
            # If caller provided an on_finish callback, call it
            if on_finish:
                on_finish(message = f"✅ Timer complete! ({timer.data.phase} phase finished)")

        except Exception as e:
            # don't let notifier failures crash status
            raise e

        finally:
            # remove timer file (same behavior as before)
            TIMER_FILE.unlink()

        return {
            "status": "complete",
            "message": f"✅ Timer complete! ({timer.data.phase} phase finished)",
            "phase": timer.data.phase,
            "remaining": 0,
        }

    minutes = remaining // 60
    seconds = int(remaining % 60)

    return {
        "status": "running",
        "message": f"⏱️  {minutes}:{seconds:02d} remaining ({timer.data.phase} phase)",
        "phase": timer.data.phase,
        "remaining": remaining,
    }


def stop(session_id: str) -> Dict[str, Any]:
    """Stop the current timer.

    Args:
        session_id: opencode session id, OPTIONAL for agentic invocation -> use empty string

    Returns:
        Confirmation message
    """

    TIMER_FILE = access_timer_file(session_id)

    if TIMER_FILE.exists():
        TIMER_FILE.unlink()
        return {"status": "stopped", "message": "🛑 Timer stopped"}

    return {"status": "idle", "message": "No active timer"}


def pause(session_id: str) -> Dict[str, Any]:
    """Pause the current timer.

    Returns:
        Confirmation message
    """

    TIMER_FILE = access_timer_file(session_id)

    if not TIMER_FILE.exists():
        return {"status": "idle", "message": "No active timer"}

    timer = Timer.model_validate_json(TIMER_FILE.read_text())
    current_time = (time.time())
    remaining = timer.data.end_time - current_time

    timer.data.status = "paused"
    timer.data.remaining = remaining

    TIMER_FILE.write_text(json.dumps(timer.data))

    return {
        "status": "paused",
        "message": "⏸️  Timer paused",
        "phase": timer.data.phase,
        "remaining": remaining,
    }


def resume(session_id: str) -> Dict[str, Any]:
    """Resume a paused timer.

    Returns:
        Confirmation message
    """

    TIMER_FILE = access_timer_file(session_id)

    if not TIMER_FILE.exists():
        return {"status": "idle", "message": "No active timer"}

    timer = Timer.model_validate_json(TIMER_FILE.read_text())

    if timer.data.status != "paused":
        return {"status": timer.data.status, "message": "Timer is not paused"}

    current_time = (time.time())
    remaining = timer.data.get("remaining", 0)
    timer.data.end_time = current_time + remaining
    timer.data.status = "running"

    TIMER_FILE.write_text(json.dumps(timer.data))

    return {
        "status": "running",
        "message": "▶️  Timer resumed",
        "phase": timer.data.phase,
        "remaining": remaining,
    }


if __name__ == "__main__":
    import fire

    fire.Fire()
