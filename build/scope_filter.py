#!/usr/bin/env python3
"""
Scope-aware transpilation filter.

Reads one or more scope manifests (core/scopes/<name>.yaml) and an optional
install config file, then calls the transpile engine with the correct
agent / skill / command / mcp-server / language filters.

Usage:
    python build/scope_filter.py --scopes stats university --target all
    python build/scope_filter.py --config install.config.yaml --target claude
    python build/scope_filter.py --scopes coding --language python --target opencode
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml

# Add build/ to sys.path so we can import transpile
BUILD_DIR = Path(__file__).parent
sys.path.insert(0, str(BUILD_DIR))

from transpile import transpile  # noqa: E402


# ---------------------------------------------------------------------------
# Scope loading
# ---------------------------------------------------------------------------

def load_scope(scopes_dir: Path, scope_name: str) -> Dict:
    """Load a single scope manifest."""
    path = scopes_dir / f"{scope_name}.yaml"
    if not path.exists():
        raise FileNotFoundError(
            f"Scope '{scope_name}' not found at {path}. "
            f"Available scopes: {[p.stem for p in scopes_dir.glob('*.yaml')]}"
        )
    with open(path) as f:
        return yaml.safe_load(f)


def merge_scopes(scopes_dir: Path, scope_names: List[str]) -> Dict:
    """Merge multiple scope manifests into a single combined filter set."""
    merged: Dict[str, Set[str]] = {
        "agents": set(),
        "skills": set(),
        "commands": set(),
        "mcp_servers": set(),
        "custom_tools": set(),
    }

    for name in scope_names:
        scope = load_scope(scopes_dir, name)
        for key in ("agents", "skills", "commands", "mcp_servers", "custom_tools"):
            for item in scope.get(key, []):
                merged[key].add(item)

    return {k: sorted(v) for k, v in merged.items()}


# ---------------------------------------------------------------------------
# Config file loading
# ---------------------------------------------------------------------------

def load_install_config(config_path: Path) -> Dict:
    """Load and validate an install config YAML file."""
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    if cfg is None:
        cfg = {}

    # Normalise keys to lists
    for key in ("scopes", "agents", "skills", "commands", "mcp_servers", "custom_tools"):
        val = cfg.get(key)
        if val is None:
            cfg[key] = []
        elif isinstance(val, str):
            cfg[key] = [val]

    if "language" not in cfg:
        cfg["language"] = "python"

    if "target" not in cfg:
        cfg["target"] = "all"

    return cfg


# ---------------------------------------------------------------------------
# Filter resolution
# ---------------------------------------------------------------------------

def resolve_filters(
    core_path: Path,
    scopes: Optional[List[str]] = None,
    config: Optional[Dict] = None,
    language_override: Optional[str] = None,
    target_override: Optional[str] = None,
) -> Dict:
    """
    Resolve the final set of filters from scope names and/or config.

    Priority:
        CLI --language / --target  >  config file  >  scope defaults
    """
    scopes_dir = core_path / "scopes"

    agent_filter: Optional[Set[str]] = None
    skill_filter: Optional[Set[str]] = None
    command_filter: Optional[Set[str]] = None
    mcp_filter: Optional[Set[str]] = None
    language = "python"
    target = "all"

    # 1. Merge scopes (from config or direct args)
    effective_scopes = list(scopes or [])
    if config:
        effective_scopes = list(dict.fromkeys(effective_scopes + (config.get("scopes") or [])))

    if effective_scopes:
        merged = merge_scopes(scopes_dir, effective_scopes)
        agent_filter = set(merged["agents"]) if merged["agents"] else None
        skill_filter = set(merged["skills"]) if merged["skills"] else None
        command_filter = set(merged["commands"]) if merged["commands"] else None
        mcp_filter = set(merged["mcp_servers"]) if merged["mcp_servers"] else None

    # 2. Apply explicit overrides from config (union with scope)
    if config:
        for items, filt_attr in (
            (config.get("agents"), "agent_filter"),
            (config.get("skills"), "skill_filter"),
            (config.get("commands"), "command_filter"),
            (config.get("mcp_servers"), "mcp_filter"),
        ):
            if items:
                current = locals()[filt_attr]
                if current is None:
                    # Replace entirely if no scope filter set
                    locals_copy = {"agent_filter": agent_filter, "skill_filter": skill_filter,
                                   "command_filter": command_filter, "mcp_filter": mcp_filter}
                    locals_copy[filt_attr] = set(items)
                    agent_filter = locals_copy["agent_filter"]
                    skill_filter = locals_copy["skill_filter"]
                    command_filter = locals_copy["command_filter"]
                    mcp_filter = locals_copy["mcp_filter"]
                else:
                    # Union
                    current.update(items)

        language = config.get("language", "python")
        target = config.get("target", "all")

    # 3. CLI overrides win
    if language_override:
        language = language_override
    if target_override:
        target = target_override

    return {
        "agent_filter": agent_filter,
        "skill_filter": skill_filter,
        "command_filter": command_filter,
        "mcp_filter": mcp_filter,
        "language": language,
        "target": target,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scope-aware transpilation filter for agent-workspace."
    )
    parser.add_argument(
        "--scopes", nargs="*", metavar="SCOPE",
        help="One or more scope names (coding, stats, university, study). "
             "Can be combined: --scopes stats university"
    )
    parser.add_argument(
        "--config", metavar="PATH",
        help="Path to an install config YAML file (install.config.yaml)."
    )
    parser.add_argument(
        "--target", choices=["opencode", "continue", "claude", "all"], default=None,
        help="Platform target (overrides config file target). Default: all"
    )
    parser.add_argument(
        "--language", choices=["python", "r", "both"], default=None,
        help="Language variant for stats/DS agents (overrides config). Default: python"
    )
    parser.add_argument(
        "--input", default="core/", help="Core input directory. Default: core/"
    )
    parser.add_argument(
        "--output", default="platforms/", help="Platform output root. Default: platforms/"
    )

    args = parser.parse_args()

    core_path = Path(args.input)
    output_path = Path(args.output)

    if not (core_path / "agents").exists():
        print(f"❌ Core input directory not found or invalid: {core_path.resolve()}")
        sys.exit(1)

    # Load config file if provided
    config: Optional[Dict] = None
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"❌ Config file not found: {config_path}")
            sys.exit(1)
        print(f"📄 Loading install config: {config_path}")
        config = load_install_config(config_path)

    if not args.scopes and not config:
        print("⚠️  No scopes or config specified — transpiling everything (no filters).")

    # Resolve combined filters
    filters = resolve_filters(
        core_path=core_path,
        scopes=args.scopes,
        config=config,
        language_override=args.language,
        target_override=args.target,
    )

    target = filters["target"]
    language = filters["language"]
    agent_filter = filters["agent_filter"]
    skill_filter = filters["skill_filter"]
    command_filter = filters["command_filter"]
    mcp_filter = filters["mcp_filter"]

    # Report what we're doing
    if args.scopes or (config and config.get("scopes")):
        effective_scopes = list(args.scopes or []) + list(
            (config or {}).get("scopes") or []
        )
        print(f"🎯 Scopes:   {', '.join(dict.fromkeys(effective_scopes))}")
    print(f"🔤 Language: {language}")
    print(f"🖥  Target:   {target}")
    if agent_filter is not None:
        print(f"   Agents  ({len(agent_filter)}): {', '.join(sorted(agent_filter))}")
    if skill_filter is not None:
        print(f"   Skills  ({len(skill_filter)}): {', '.join(sorted(skill_filter))}")
    if command_filter is not None:
        print(f"   Commands({len(command_filter)}): {', '.join(sorted(command_filter))}")
    print()

    # Expand target list
    targets = ["opencode", "continue", "claude"] if target == "all" else [target]

    all_success = True
    for tgt in targets:
        if output_path.name == tgt:
            tgt_output = output_path
        else:
            tgt_output = output_path / tgt

        success = transpile(
            tgt, core_path, tgt_output,
            agent_filter=agent_filter,
            command_filter=command_filter,
            skill_filter=skill_filter,
            mcp_filter=mcp_filter,
            language=language,
        )
        if not success:
            all_success = False

    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
