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
    session_id: str,
    message: str,
    model: Dict[str, str] = {"providerID": "github-copilot", "modelID": "gpt-5-mini"},
):
    from opencode_ai import Opencode

    client = Opencode(base_url=oc_default_url, max_retries=1)

    client.session.prompt(id=session_id, parts=[{"type": "text", "text": message}])


def access_timer_base(session_id: str) -> Path:
    return Path(f"/tmp/{file_slug.format(session_id=session_id)}")


def access_timer_file(session_id: str) -> Path:
    return access_timer_base(session_id).with_suffix(".json")


def access_pid_file(session_id: str) -> Path:
    return access_timer_base(session_id).with_suffix(".pid")


def status_poller(session_id: str, interval_s: int = 15):
    import os, signal, time
    from functools import partial
    from pathlib import Path

    pidfile = access_pid_file(session_id)
    logdir = Path("/tmp/opencode-pomodoro-logs")
    try:
        logdir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    # If pidfile exists and points to a live process, do not start another poller
    if pidfile.exists():
        try:
            existing = int(pidfile.read_text())
            if existing and existing != os.getpid():
                # check process liveness; will raise if not alive
                os.kill(existing, 0)
                return
        except Exception:
            try:
                pidfile.unlink()
            except Exception:
                pass

    # write our pid so other starts can detect us
    try:
        pidfile.write_text(str(os.getpid()))
    except Exception:
        pass

    def _cleanup(signum=None, frame=None):
        try:
            if pidfile.exists():
                pidfile.unlink()
        except Exception:
            pass
        raise SystemExit(0)

    for sig in ("SIGINT", "SIGTERM"):
        if hasattr(signal, sig):
            signal.signal(getattr(signal, sig), _cleanup)

    # create a wrapper so the on_finish callback receives a dict payload
    # and forwards the message to notify_opencode
    def _on_finish(payload: Dict[str, Any]):
        try:
            msg = payload.get("message") if isinstance(payload, dict) else str(payload)
        except Exception:
            msg = str(payload)
        try:
            notify_opencode(session_id, str(msg))
        except Exception:
            # best-effort notify
            pass

    polling_func = partial(
        status,
        session_id=session_id,
        on_finish=_on_finish,
    )

    try:
        while True:
            try:
                polling_func()
            except Exception as e:
                try:
                    with open(logdir / f"poll_err-{session_id}.log", "a") as f:
                        f.write(f"{time.time()}: poller error: {e}\n")
                except Exception:
                    pass
            time.sleep(interval_s)
    finally:
        _cleanup()


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
    TIMER_FILE.write_text(timer.model_dump_json(indent=2))

    # Launch a detached subprocess that runs the status_poller so start() returns
    import sys, subprocess, os
    from pathlib import Path

    logdir = Path("/tmp/opencode-pomodoro-logs")
    try:
        logdir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    logpath = logdir / f"pomodoro-{session_id}-{int(time.time())}.log"
    out = open(logpath, "a")

    # Start detached process: explicit kwargs per-platform to keep types clear
    if os.name == "nt":
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        proc = subprocess.Popen(
            [sys.executable, __file__, "status_poller", "--session_id", session_id],
            stdout=out,
            stderr=out,
            close_fds=True,
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
        )
    else:
        proc = subprocess.Popen(
            [sys.executable, __file__, "status_poller", "--session_id", session_id],
            stdout=out,
            stderr=out,
            close_fds=True,
            start_new_session=True,
        )

    # write pidfile for dedupe
    pidfile = access_pid_file(session_id)
    try:
        pidfile.write_text(str(proc.pid))
    except Exception:
        pass

    # return immediately with timer info + background process details
    print(timer.model_dump_json(indent=2))
    return {"status": "started", "pid": proc.pid, "log": str(logpath)}


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
    current_time = time.time()

    if timer.data.status == "paused":
        return {
            "status": "paused",
            "message": f"⏸️  Timer paused in {timer.data.phase} phase",
            "phase": timer.data.phase,
            "remaining": getattr(timer.data, "remaining", 0),
        }

    remaining = timer.data.end_time - current_time

    if remaining <= 0:
        try:
            # If caller provided an on_finish callback, call it
            if on_finish:
                try:
                    on_finish(
                        {
                            "message": f"✅ Timer complete! ({timer.data.phase} phase finished)",
                            "phase": timer.data.phase,
                        }
                    )
                except Exception as notify_err:
                    # log notifier failure but continue cleanup
                    try:
                        Path("/tmp/opencode-pomodoro-logs").mkdir(
                            parents=True, exist_ok=True
                        )
                        with open(
                            f"/tmp/opencode-pomodoro-logs/notify_err-{session_id}.log",
                            "a",
                        ) as f:
                            f.write(f"{time.time()}: notify error: {notify_err}\n")
                    except Exception:
                        pass

        finally:
            # remove timer file and pidfile
            try:
                TIMER_FILE.unlink()
            except Exception:
                pass
            try:
                pidfile = access_pid_file(session_id)
                if pidfile.exists():
                    pidfile.unlink()
            except Exception:
                pass

        return {
            "status": "complete",
            "message": f"✅ Timer complete! ({timer.data.phase} phase finished)",
            "phase": timer.data.phase,
            "remaining": 0,
        }

    minutes = int(remaining // 60)
    seconds = int(remaining % 60)

    return {
        "status": "running",
        "message": f"⏱️  {minutes}:{seconds:02d} remaining ({timer.data.phase} phase)",
        "phase": timer.data.phase,
        "remaining": remaining,
    }


def stop(session_id: str) -> Dict[str, Any]:
    """Stop the current timer and cleanup the poller.

    Args:
        session_id: opencode session id, OPTIONAL for agentic invocation -> use empty string

    Returns:
        Confirmation message
    """
    import os, signal

    TIMER_FILE = access_timer_file(session_id)
    PID_FILE = access_pid_file(session_id)

    stopped = False

    # Kill the poller process if it exists
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            if pid and pid != os.getpid():
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass  # Process already dead
        except (ValueError, OSError):
            pass  # Invalid PID or can't kill
        finally:
            try:
                PID_FILE.unlink()
                stopped = True
            except OSError:
                pass

    # Remove timer file
    if TIMER_FILE.exists():
        try:
            TIMER_FILE.unlink()
            stopped = True
        except OSError:
            pass

    if stopped:
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
    current_time = time.time()
    remaining = timer.data.end_time - current_time

    timer.data.status = "paused"
    timer.data.remaining = remaining

    TIMER_FILE.write_text(timer.model_dump_json(indent=2))

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

    current_time = time.time()
    remaining = getattr(timer.data, "remaining", 0)
    timer.data.end_time = current_time + remaining
    timer.data.status = "running"

    TIMER_FILE.write_text(timer.model_dump_json(indent=2))

    return {
        "status": "running",
        "message": "▶️  Timer resumed",
        "phase": timer.data.phase,
        "remaining": remaining,
    }


if __name__ == "__main__":
    import fire
    from types import SimpleNamespace

    fire.Fire(
        SimpleNamespace(
            start=start,
            status=status,
            resume=resume,
            stop=stop,
            pause=pause,
            status_poller=status_poller,
        )
    )
