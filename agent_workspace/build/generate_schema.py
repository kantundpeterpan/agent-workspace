#!/usr/bin/env python3
"""
Schema generator for install.config.yaml.

Reads the core/ directory to discover all valid agents, skills, commands,
MCP servers, and scopes, then writes core/schemas/install-config.json with
up-to-date enum arrays.

Run this whenever a new agent, skill, command, MCP server, or scope is added:

    python build/generate_schema.py
    python build/generate_schema.py --core core/ --output core/schemas/install-config.json
    python build/generate_schema.py --check   # exit non-zero if schema is stale
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List


# ---------------------------------------------------------------------------
# Discovery helpers
# ---------------------------------------------------------------------------

def _sorted_stems(directory: Path, glob: str = "*.yaml") -> List[str]:
    """Return sorted stem names (filename without extension) matching glob."""
    return sorted(p.stem for p in directory.glob(glob) if p.is_file())


def _sorted_dirs(directory: Path) -> List[str]:
    """Return sorted names of immediate subdirectories."""
    return sorted(p.name for p in directory.iterdir() if p.is_dir())


def discover_enums(core_path: Path) -> dict[str, List[str]]:
    """Discover all valid enum values by inspecting the core directory."""
    return {
        "scopes":      _sorted_stems(core_path / "scopes"),
        "agents":      _sorted_stems(core_path / "agents"),
        "skills":      _sorted_dirs(core_path / "skills"),
        "commands":    _sorted_stems(core_path / "commands"),
        "mcp_servers": _sorted_stems(core_path / "mcp-servers", glob="*.json"),
    }


# ---------------------------------------------------------------------------
# Schema construction
# ---------------------------------------------------------------------------

# Static property definitions — description, default, and any non-enum
# constraints that never change regardless of what lives in core/.
_STATIC_PROPS: dict[str, dict] = {
    "scopes": {
        "description": (
            "Pre-defined scope bundles to install. "
            "Each scope pulls in a curated set of agents, skills, commands, and MCP servers."
        ),
        "item_description": "Scope name",
    },
    "agents": {
        "description": (
            "Additional agents to include on top of scope defaults. "
            "Values are unioned with whatever the selected scopes already include."
        ),
        "item_description": "Agent name",
    },
    "skills": {
        "description": (
            "Additional skills to include on top of scope defaults. "
            "Values are unioned with whatever the selected scopes already include."
        ),
        "item_description": "Skill name",
    },
    "commands": {
        "description": (
            "Additional slash commands to include on top of scope defaults. "
            "Values are unioned with whatever the selected scopes already include."
        ),
        "item_description": "Command name",
    },
    "mcp_servers": {
        "description": (
            "MCP servers to include. "
            "Values are unioned with whatever the selected scopes already include."
        ),
        "item_description": "MCP server name",
    },
}


def build_schema(enums: dict[str, List[str]]) -> dict:
    """Build the full JSON Schema dict from discovered enum values."""
    # Array properties backed by enum lists
    array_props: dict = {}
    for key, static in _STATIC_PROPS.items():
        array_props[key] = {
            "type": "array",
            "description": static["description"],
            "items": {
                "type": "string",
                "enum": enums[key],
                "description": static["item_description"],
            },
            "uniqueItems": True,
            "default": [],
        }

    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Install Config Schema",
        "description": (
            "Schema for agent-workspace install.config.yaml — "
            "controls which agents, skills, commands, and tools are transpiled and installed"
        ),
        "type": "object",
        "additionalProperties": False,
        "properties": {
            **array_props,
            "language": {
                "type": "string",
                "description": (
                    "Language variant for statistics and data-science agent system prompts.\n"
                    "- python: Python-only (pandas, statsmodels, PyMC, scikit-learn\u2026)\n"
                    "- r: R-only (tidyverse, lme4, brms, forecast\u2026)\n"
                    "- both: Bilingual Python + R in every agent"
                ),
                "enum": ["python", "r", "both"],
                "default": "python",
            },
            "target": {
                "type": "string",
                "description": (
                    "Platform(s) to generate output for.\n"
                    "- all: OpenCode + Continue.dev + Claude Code\n"
                    "- opencode: OpenCode only\n"
                    "- continue: Continue.dev only\n"
                    "- claude: Claude Code only"
                ),
                "enum": ["all", "opencode", "continue", "claude"],
                "default": "all",
            },
            "input": {
                "type": "string",
                "description": "Path to the core input directory. Defaults to 'core/'.",
                "default": "core/",
            },
            "output": {
                "type": "string",
                "description": "Path to the platform output root directory. Defaults to 'platforms/'.",
                "default": "platforms/",
            },
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate core/schemas/install-config.json from the core/ directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--core",
        default=None,
        metavar="PATH",
        help="Path to the core/ directory (default: auto-detected from script location).",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="PATH",
        help="Path to write the schema JSON (default: <core>/schemas/install-config.json).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Check mode: verify the on-disk schema matches what would be generated. "
            "Exits with code 1 and prints a diff if the schema is stale."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the generated schema to stdout without writing any files.",
    )
    args = parser.parse_args()

    # Resolve paths
    script_dir = Path(__file__).resolve().parent
    core_path = Path(args.core).resolve() if args.core else script_dir.parent / "core"

    if not core_path.exists():
        print(f"❌ Core directory not found: {core_path}")
        sys.exit(1)

    output_path = (
        Path(args.output).resolve()
        if args.output
        else core_path / "schemas" / "install-config.json"
    )

    # Discover + build
    print(f"🔍 Discovering core definitions in: {core_path}")
    enums = discover_enums(core_path)

    for key, values in enums.items():
        print(f"   {key:12s} → {len(values)} items: {', '.join(values)}")

    schema = build_schema(enums)
    new_text = json.dumps(schema, indent=2, ensure_ascii=False) + "\n"

    # --dry-run: print and exit
    if args.dry_run:
        print("\n" + new_text)
        sys.exit(0)

    # --check: compare with on-disk version
    if args.check:
        if not output_path.exists():
            print(f"❌ Schema file not found: {output_path}")
            print("   Run 'python build/generate_schema.py' to create it.")
            sys.exit(1)

        current_text = output_path.read_text(encoding="utf-8")
        if current_text == new_text:
            print(f"\n✅ Schema is up to date: {output_path}")
            sys.exit(0)
        else:
            print(f"\n❌ Schema is stale: {output_path}")
            print("   Run 'python build/generate_schema.py' to regenerate it.\n")
            # Show which enum lists changed
            try:
                current_schema = json.loads(current_text)
                for key in _STATIC_PROPS:
                    current_enum = (
                        current_schema.get("properties", {})
                        .get(key, {})
                        .get("items", {})
                        .get("enum", [])
                    )
                    new_enum = enums[key]
                    added = sorted(set(new_enum) - set(current_enum))
                    removed = sorted(set(current_enum) - set(new_enum))
                    if added:
                        print(f"   + {key}: {added}")
                    if removed:
                        print(f"   - {key}: {removed}")
            except Exception:
                pass
            sys.exit(1)

    # Write schema
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(new_text, encoding="utf-8")
    print(f"\n✅ Schema written to: {output_path}")


if __name__ == "__main__":
    main()
