#!/usr/bin/env python3
"""Backward-compatibility shim — delegates to workspace.py."""
import runpy, pathlib
runpy.run_path(str(pathlib.Path(__file__).parent / "workspace.py"), run_name="__main__")
