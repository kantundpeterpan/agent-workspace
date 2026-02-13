#!/usr/bin/env python3
"""Detached worker to run the status_poller in its own OS process.

This script is executed via subprocess.Popen with start_new_session=True so
the poller keeps running after the original script exits.
"""

import sys
import os
from pathlib import Path

# Ensure the local directory is on sys.path so we can import script.py
sys.path.insert(0, str(Path(__file__).parent))

try:
    from script import status_poller
except Exception as e:  # pragma: no cover - defensive
    raise ImportError


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: worker.py <session_id> [interval_s]")
        raise SystemExit(2)

    session_id = sys.argv[1]
    try:
        interval_s = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    except ValueError:
        interval_s = 15

    # Run the poller loop; this will block inside status_poller until it exits
    status_poller(session_id=session_id, interval_s=interval_s)


if __name__ == "__main__":
    main()
