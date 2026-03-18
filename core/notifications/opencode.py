"""Optional shim to forward pomodoro finished notifications to Opencode.

This file is intentionally minimal and test-friendly. A real integration
should replace notify_pomodoro_finished with actual API calls or SDK usage.
"""

import json
from pathlib import Path


def notify_pomodoro_finished(payload: dict) -> None:
    """Write payload to a temp file for testing/inspection.

    Replace this with real network calls or SDK usage in production.
    """
    out = Path("/tmp/opencode-pomodoro-notify.json")
    out.write_text(json.dumps(payload))
