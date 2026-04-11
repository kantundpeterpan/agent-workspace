#!/usr/bin/env python3
"""
Agent-workspace environment management CLI.

Subcommands
-----------
  (no subcommand / install)   Run the interactive install wizard  [default]
  status                      Show current config and installed items
  list   [category]           List available items (✓ = active, ~ = via scope, ○ = inactive)
  add    <category> <name>…   Add items to the active config and retranspile
  remove <category> <name>…   Remove items from the active config and retranspile
  apply  [-y]                 Sync the environment to the saved config: removes stale files,
                              then retranspiles.  Use -y to skip the removal prompt.
  set    <key> <value>        Update a scalar setting (language, target) and retranspile

Categories: agent · skill · command · mcp · scope

Examples
--------
    python scripts/install.py                              # interactive wizard
    python scripts/install.py --config install.config.yaml
    python scripts/install.py --scopes stats university --language r
    python scripts/install.py --dry-run

    python scripts/install.py status
    python scripts/install.py list
    python scripts/install.py list agents
    python scripts/install.py add agent classical-stats-analyst
    python scripts/install.py remove mcp filesystem
    python scripts/install.py set language r
    python scripts/install.py set target opencode
    python scripts/install.py apply
    python scripts/install.py apply -y
    python scripts/install.py apply --dry-run
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

# ---------------------------------------------------------------------------
# Dependency check — give a clear message if questionary/rich are missing
# ---------------------------------------------------------------------------
try:
    import questionary
    from questionary import Style
    import yaml
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import print as rprint
except ImportError as e:
    print(
        f"\n❌ Missing dependency: {e}\n"
        "   Install with:\n"
        "     pip install -r scripts/requirements-install.txt\n"
    )
    sys.exit(1)

console = Console()

CUSTOM_STYLE = Style([
    ("qmark", "fg:#00bfff bold"),
    ("question", "bold"),
    ("answer", "fg:#00ff7f bold"),
    ("pointer", "fg:#00bfff bold"),
    ("highlighted", "fg:#00bfff bold"),
    ("selected", "fg:#00ff7f"),
    ("separator", "fg:#555555"),
    ("instruction", "fg:#888888"),
])

SCOPE_DESCRIPTIONS = {
    "coding": "Code review, refactoring, testing, deployment — software engineering",
    "stats":  "EDA, classical & Bayesian modelling, ML, causal inference, time series",
    "university": "Reports, presentations, literature, lecture notes, Obsidian vault",
    "study":  "Flashcards, revision planning, exam coaching, concept explanation",
}

LANGUAGE_DESCRIPTIONS = {
    "python": "Python only (pandas, statsmodels, PyMC, scikit-learn…)",
    "r":      "R only (tidyverse, lme4, brms, forecast…)",
    "both":   "Bilingual: Python + R in every agent",
}

TARGET_DESCRIPTIONS = {
    "all":      "All platforms: OpenCode + Continue.dev + Claude Code",
    "opencode": "OpenCode only",
    "continue": "Continue.dev only",
    "claude":   "Claude Code only",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_workspace_root() -> Path:
    """Walk up from the current file to find the workspace root."""
    candidate = Path(__file__).resolve().parent.parent
    if (candidate / "core").exists() and (candidate / "build").exists():
        return candidate
    # Fall back to cwd
    cwd = Path.cwd()
    if (cwd / "core").exists():
        return cwd
    # Try submodule pattern
    for sub in cwd.iterdir():
        if sub.is_dir() and (sub / "core").exists() and (sub / "build").exists():
            return sub
    return candidate


def _load_available_items(workspace: Path) -> Dict[str, List[str]]:
    """Discover available agents, skills, commands, and scopes."""
    return {
        "scopes": sorted(p.stem for p in (workspace / "core" / "scopes").glob("*.yaml")),
        "agents": sorted(p.stem for p in (workspace / "core" / "agents").glob("*.yaml")),
        "skills": sorted(
            p.name for p in (workspace / "core" / "skills").iterdir() if p.is_dir()
        ),
        "commands": sorted(p.stem for p in (workspace / "core" / "commands").glob("*.yaml")),
        "mcp_servers": sorted(
            p.stem for p in (workspace / "core" / "mcp-servers").glob("*.json")
        ),
    }


def _scope_needs_language(scopes: List[str]) -> bool:
    """Return True if any selected scope includes stats/DS agents."""
    return bool(set(scopes) & {"stats", "university", "study"})


def _create_symlink(src: Path, dst: Path, dry_run: bool = False) -> None:
    """Create a symlink, backing up existing files."""
    if dst.is_symlink():
        console.print(f"  [yellow]↩  {dst} already linked[/]")
        return
    if dst.exists():
        backup = dst.with_suffix(dst.suffix + ".backup")
        console.print(f"  [yellow]⚠  {dst} exists — backed up to {backup.name}[/]")
        if not dry_run:
            shutil.move(str(dst), str(backup))
    if not dry_run:
        os.symlink(src, dst)
    console.print(f"  [green]✓  {dst} → {src}[/]")


def _run_transpile(workspace: Path, config: Dict, dry_run: bool = False) -> bool:
    """Call build/scope_filter.py with the resolved config."""
    scope_filter = workspace / "build" / "scope_filter.py"
    if not scope_filter.exists():
        console.print(f"[red]❌ scope_filter.py not found at {scope_filter}[/]")
        return False

    cmd = [sys.executable, str(scope_filter)]

    scopes = config.get("scopes") or []
    if scopes:
        cmd += ["--scopes"] + scopes

    language = config.get("language", "python")
    cmd += ["--language", language]

    target = config.get("target", "all")
    cmd += ["--target", target]

    cmd += ["--input", str(workspace / "core")]
    cmd += ["--output", str(workspace / "platforms")]

    console.print(f"\n[dim]$ {' '.join(cmd)}[/]")
    if dry_run:
        console.print("[yellow]  (dry-run — command not executed)[/]")
        return True

    result = subprocess.run(cmd, cwd=workspace)
    return result.returncode == 0


def _setup_symlinks(workspace: Path, project_root: Path, target: str, dry_run: bool) -> None:
    """Set up platform symlinks in the project root."""
    console.print("\n[bold]🔗 Setting up symlinks...[/]")

    targets = ["opencode", "continue", "claude"] if target == "all" else [target]

    for t in targets:
        if t == "opencode":
            _create_symlink(
                workspace / "platforms" / "opencode",
                project_root / ".opencode",
                dry_run,
            )
            _create_symlink(
                workspace / "platforms" / "opencode",
                project_root / ".agents",
                dry_run,
            )
        elif t == "continue":
            _create_symlink(
                workspace / "platforms" / "continue",
                project_root / ".continue",
                dry_run,
            )
        elif t == "claude":
            _create_symlink(
                workspace / "platforms" / "claude" / "CLAUDE.md",
                project_root / "CLAUDE.md",
                dry_run,
            )


def _save_config(config: Dict, path: Path, dry_run: bool) -> None:
    """Save the resolved config to a YAML file."""
    if dry_run:
        console.print(f"\n[yellow]  (dry-run — config not saved to {path})[/]")
        return
    with open(path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    console.print(f"\n[green]💾 Config saved to {path}[/]")


def _load_config(path: Path) -> Optional[Dict]:
    """Load install.config.yaml, normalising all list fields.  Returns None if missing."""
    if not path.exists():
        return None
    with open(path) as f:
        cfg = yaml.safe_load(f) or {}
    # Normalise every list field to an actual list
    for key in ("scopes", "agents", "skills", "commands", "mcp_servers"):
        val = cfg.get(key)
        if val is None:
            cfg[key] = []
        elif isinstance(val, str):
            cfg[key] = [val]
    cfg.setdefault("language", "python")
    cfg.setdefault("target", "all")
    return cfg


def _default_config() -> Dict:
    """Return a config skeleton with empty lists and sensible defaults."""
    return {
        "scopes": [],
        "language": "python",
        "target": "all",
        "agents": [],
        "skills": [],
        "commands": [],
        "mcp_servers": [],
    }


# Category name → config key mapping
_CATEGORY_MAP: Dict[str, str] = {
    "agent":    "agents",
    "agents":   "agents",
    "skill":    "skills",
    "skills":   "skills",
    "command":  "commands",
    "commands": "commands",
    "mcp":      "mcp_servers",
    "mcp_servers": "mcp_servers",
    "scope":    "scopes",
    "scopes":   "scopes",
}

# Category singular label → available key in _load_available_items()
_AVAILABLE_KEY: Dict[str, str] = {
    "agents":      "agents",
    "skills":      "skills",
    "commands":    "commands",
    "mcp_servers": "mcp_servers",
    "scopes":      "scopes",
}


def _scope_items(workspace: Path, scope_names: List[str]) -> Dict[str, Set[str]]:
    """Return the union of all items brought in by the given scopes."""
    result: Dict[str, Set[str]] = {
        "agents": set(), "skills": set(), "commands": set(), "mcp_servers": set()
    }
    scopes_dir = workspace / "core" / "scopes"
    for name in scope_names:
        path = scopes_dir / f"{name}.yaml"
        if not path.exists():
            continue
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        for key in result:
            for item in data.get(key, []):
                result[key].add(item)
    return result


def _compute_stale_output_files(workspace: Path, config: Dict) -> List[Path]:
    """
    Return a list of output files that exist in platforms/ but would NOT be
    regenerated given the current config.  These are the stale artefacts that
    ``apply`` needs to clean up.

    Only the per-item flat files are checked (agents/*.md, commands/*.md).
    Aggregate files (opencode.json, config.yaml, CLAUDE.md) and the skills/
    directory are always fully regenerated by the transpile step and therefore
    never stale.
    """
    # ------------------------------------------------------------------
    # 1. Resolve the filter sets that the transpile step would use
    # ------------------------------------------------------------------
    scope_derived = _scope_items(workspace, config.get("scopes") or [])
    has_scopes = bool(config.get("scopes"))

    def _build_filter(scope_key: str, cfg_key: str) -> Optional[Set[str]]:
        """Replicate scope_filter.py resolve_filters logic for one category."""
        filt: Optional[Set[str]] = None
        if has_scopes:
            scope_set = scope_derived[scope_key]
            if scope_set:
                filt = set(scope_set)
        items: List[str] = config.get(cfg_key) or []
        if items:
            if filt is None:
                filt = set(items)
            else:
                filt.update(items)
        return filt  # None → no filter → everything passes

    agent_filter = _build_filter("agents", "agents")
    command_filter = _build_filter("commands", "commands")

    # ------------------------------------------------------------------
    # 2. Determine which core names *would* be generated
    # ------------------------------------------------------------------
    def _passing_names(core_subdir: str, filt: Optional[Set[str]]) -> Set[str]:
        names: Set[str] = set()
        for yaml_file in (workspace / "core" / core_subdir).glob("*.yaml"):
            with open(yaml_file) as fh:
                data = yaml.safe_load(fh) or {}
            name = data.get("name", yaml_file.stem)
            if filt is None or name in filt:
                names.add(name)
        return names

    expected_agents = _passing_names("agents", agent_filter)
    expected_commands = _passing_names("commands", command_filter)

    # ------------------------------------------------------------------
    # 3. Walk the platforms output dirs and collect stale files
    # ------------------------------------------------------------------
    target = config.get("target", "all")
    active_targets = ["opencode", "continue", "claude"] if target == "all" else [target]
    platforms = workspace / "platforms"
    stale: List[Path] = []

    if "opencode" in active_targets:
        for candidate in (platforms / "opencode" / "agents").glob("*.md"):
            if candidate.stem not in expected_agents:
                stale.append(candidate)
        for candidate in (platforms / "opencode" / "commands").glob("*.md"):
            if candidate.stem not in expected_commands:
                stale.append(candidate)

    if "claude" in active_targets:
        claude_cmds = platforms / "claude" / ".claude" / "commands"
        for candidate in claude_cmds.glob("*.md"):
            if candidate.stem not in expected_commands:
                stale.append(candidate)

    return sorted(stale)


# ---------------------------------------------------------------------------
# Interactive wizard
# ---------------------------------------------------------------------------

def run_wizard(workspace: Path, available: Dict) -> Dict:
    """Run the full interactive install wizard and return the resolved config."""
    console.print(Panel.fit(
        "[bold cyan]agent-workspace install assistant[/]\n"
        "[dim]Navigate with arrows · Space to select · Enter to confirm[/]",
        border_style="cyan",
    ))

    # 1. Scopes
    scope_choices = [
        questionary.Choice(
            title=f"{name:12s}  {desc}",
            value=name,
        )
        for name, desc in SCOPE_DESCRIPTIONS.items()
        if name in available["scopes"]
    ]
    selected_scopes: List[str] = questionary.checkbox(
        "Which scopes do you want to install?",
        choices=scope_choices,
        style=CUSTOM_STYLE,
    ).ask() or []

    if not selected_scopes:
        console.print("[yellow]⚠  No scopes selected — all agents/skills/commands will be installed.[/]")

    # 2. Language (only if stats/university/study selected)
    language = "python"
    if _scope_needs_language(selected_scopes):
        lang_choices = [
            questionary.Choice(title=f"{k:8s} {v}", value=k)
            for k, v in LANGUAGE_DESCRIPTIONS.items()
        ]
        language = questionary.select(
            "Language for statistics / data-science agents:",
            choices=lang_choices,
            default="python",
            style=CUSTOM_STYLE,
        ).ask() or "python"

    # 3. Target platform
    target_choices = [
        questionary.Choice(title=f"{k:10s} {v}", value=k)
        for k, v in TARGET_DESCRIPTIONS.items()
    ]
    target = questionary.select(
        "Which platform(s) to install for?",
        choices=target_choices,
        default="all",
        style=CUSTOM_STYLE,
    ).ask() or "all"

    # 4. Optional granular additions
    add_extra = questionary.confirm(
        "Do you want to add specific agents/skills/commands beyond the scope defaults?",
        default=False,
        style=CUSTOM_STYLE,
    ).ask()

    extra_agents: List[str] = []
    extra_skills: List[str] = []
    extra_commands: List[str] = []
    extra_mcp: List[str] = []

    if add_extra:
        extra_agents = questionary.checkbox(
            "Extra agents (in addition to scope):",
            choices=sorted(available["agents"]),
            style=CUSTOM_STYLE,
        ).ask() or []

        extra_skills = questionary.checkbox(
            "Extra skills:",
            choices=sorted(available["skills"]),
            style=CUSTOM_STYLE,
        ).ask() or []

        extra_commands = questionary.checkbox(
            "Extra commands:",
            choices=sorted(available["commands"]),
            style=CUSTOM_STYLE,
        ).ask() or []

        extra_mcp = questionary.checkbox(
            "MCP servers to include:",
            choices=sorted(available["mcp_servers"]),
            style=CUSTOM_STYLE,
        ).ask() or []

    # 5. Save config?
    save_config = questionary.confirm(
        "Save this configuration to install.config.yaml?",
        default=True,
        style=CUSTOM_STYLE,
    ).ask()

    config = {
        "scopes": selected_scopes,
        "language": language,
        "target": target,
        "agents": extra_agents,
        "skills": extra_skills,
        "commands": extra_commands,
        "mcp_servers": extra_mcp,
        "_save": save_config,
    }
    return config


# ---------------------------------------------------------------------------
# Summary display
# ---------------------------------------------------------------------------

def show_summary(config: Dict, available: Dict) -> None:
    """Print a rich summary table of what will be installed."""
    table = Table(title="Installation Summary", border_style="cyan", show_header=True)
    table.add_column("Setting", style="bold")
    table.add_column("Value")

    table.add_row("Scopes", ", ".join(config.get("scopes") or ["(all)"]))
    table.add_row("Language", config.get("language", "python"))
    table.add_row("Target", config.get("target", "all"))

    if config.get("agents"):
        table.add_row("Extra agents", ", ".join(config["agents"]))
    if config.get("skills"):
        table.add_row("Extra skills", ", ".join(config["skills"]))
    if config.get("commands"):
        table.add_row("Extra commands", ", ".join(config["commands"]))
    if config.get("mcp_servers"):
        table.add_row("MCP servers", ", ".join(config["mcp_servers"]))

    console.print()
    console.print(table)
    console.print()


# ---------------------------------------------------------------------------
# Management subcommand implementations
# ---------------------------------------------------------------------------

def cmd_status(workspace: Path, project_root: Path, config_path: Path) -> None:
    """Show the current configuration and which items are active."""
    config = _load_config(config_path)
    if config is None:
        console.print(
            f"[yellow]⚠  No config found at [bold]{config_path}[/bold].\n"
            "   Run [bold]python scripts/install.py[/bold] to create one.[/]"
        )
        return

    scope_derived = _scope_items(workspace, config.get("scopes", []))

    table = Table(title="Current Configuration", border_style="cyan", show_header=True)
    table.add_column("Setting", style="bold")
    table.add_column("Value")
    table.add_row("Config file", str(config_path))
    table.add_row("Scopes", ", ".join(config.get("scopes") or ["(none)"]))
    table.add_row("Language", config.get("language", "python"))
    table.add_row("Target", config.get("target", "all"))
    console.print()
    console.print(table)

    for label, config_key in [
        ("Agents", "agents"),
        ("Skills", "skills"),
        ("Commands", "commands"),
        ("MCP servers", "mcp_servers"),
    ]:
        explicit: List[str] = config.get(config_key) or []
        via_scope: List[str] = sorted(scope_derived.get(config_key, set()) - set(explicit))

        if not explicit and not via_scope:
            continue

        t = Table(title=label, border_style="dim", show_header=True)
        t.add_column("Name")
        t.add_column("Source", style="dim")

        for item in sorted(explicit):
            t.add_row(item, "[green]explicit[/]")
        for item in via_scope:
            t.add_row(item, "[cyan]scope[/]")

        console.print(t)

    console.print()


def cmd_list(
    workspace: Path,
    project_root: Path,
    config_path: Path,
    category: Optional[str],
) -> None:
    """List available items, marking those active in the current config."""
    available = _load_available_items(workspace)
    config = _load_config(config_path) or _default_config()
    scope_derived = _scope_items(workspace, config.get("scopes", []))

    # Normalise requested category
    config_key: Optional[str] = None
    if category:
        config_key = _CATEGORY_MAP.get(category.lower())
        if config_key is None:
            console.print(
                f"[red]❌ Unknown category '{category}'. "
                f"Choose from: agent, skill, command, mcp, scope[/]"
            )
            sys.exit(1)

    def _print_category(label: str, cfg_key: str, avail_key: str) -> None:
        items = available.get(avail_key, [])
        explicit_set = set(config.get(cfg_key) or [])
        scope_set = scope_derived.get(cfg_key, set()) if cfg_key != "scopes" else set()

        t = Table(title=label, border_style="dim", show_header=True)
        t.add_column("Name")
        t.add_column("Status")

        for item in items:
            if item in explicit_set:
                t.add_row(item, "[green]✓ explicit[/]")
            elif item in scope_set:
                t.add_row(item, "[cyan]~ scope[/]")
            else:
                t.add_row(item, "[dim]○[/]")

        console.print(t)

    categories = [
        ("Scopes",      "scopes",      "scopes"),
        ("Agents",      "agents",      "agents"),
        ("Skills",      "skills",      "skills"),
        ("Commands",    "commands",    "commands"),
        ("MCP servers", "mcp_servers", "mcp_servers"),
    ]

    console.print()
    for label, cfg_key, avail_key in categories:
        if config_key is None or config_key == cfg_key:
            _print_category(label, cfg_key, avail_key)
    console.print()


def cmd_add(
    workspace: Path,
    project_root: Path,
    config_path: Path,
    category: Optional[str],
    names: List[str],
    dry_run: bool,
    no_symlinks: bool,
) -> None:
    """Add one or more items to the config and retranspile."""
    available = _load_available_items(workspace)

    # Prompt for category if missing
    if not category:
        category = questionary.select(
            "Which category do you want to add to?",
            choices=["agent", "skill", "command", "mcp", "scope"],
            style=CUSTOM_STYLE,
        ).ask()
        if not category:
            console.print("[yellow]Cancelled.[/]")
            sys.exit(0)

    config_key = _CATEGORY_MAP.get(category.lower())
    if config_key is None:
        console.print(
            f"[red]❌ Unknown category '{category}'. "
            f"Choose from: agent, skill, command, mcp, scope[/]"
        )
        sys.exit(1)

    avail_key = _AVAILABLE_KEY[config_key]
    valid = available.get(avail_key, [])

    # Prompt for names if missing
    if not names:
        config = _load_config(config_path) or _default_config()
        existing: List[str] = config.get(config_key) or []
        choices = [n for n in valid if n not in existing]
        if not choices:
            console.print(f"[yellow]All available {config_key} are already in your config.[/]")
            sys.exit(0)
        names = questionary.checkbox(
            f"Select {category}(s) to add:",
            choices=sorted(choices),
            style=CUSTOM_STYLE,
        ).ask() or []
        if not names:
            console.print("[yellow]Nothing selected — cancelled.[/]")
            sys.exit(0)

    valid_set = set(valid)
    unknown = [n for n in names if n not in valid_set]
    if unknown:
        console.print(
            f"[red]❌ Unknown {category}(s): {', '.join(unknown)}\n"
            f"   Available: {', '.join(sorted(valid_set))}[/]"
        )
        sys.exit(1)

    config = _load_config(config_path)
    if config is None:
        console.print(f"[yellow]⚠  No config found at {config_path} — creating a default one.[/]")
        config = _default_config()

    existing = config.get(config_key) or []
    added = []
    for name in names:
        if name not in existing:
            existing.append(name)
            added.append(name)
        else:
            console.print(f"  [yellow]↩  {name} already in {config_key}[/]")

    config[config_key] = existing

    if added:
        console.print(f"  [green]✓  Added to {config_key}: {', '.join(added)}[/]")

    _save_config(config, config_path, dry_run=dry_run)

    console.print("\n[bold]⚙  Retranspiling...[/]")
    if not _run_transpile(workspace, config, dry_run=dry_run):
        console.print("[red]❌ Transpile failed.[/]")
        sys.exit(1)

    if not no_symlinks:
        _setup_symlinks(workspace, project_root, config.get("target", "all"), dry_run=dry_run)


def cmd_remove(
    workspace: Path,
    project_root: Path,
    config_path: Path,
    category: Optional[str],
    names: List[str],
    dry_run: bool,
    no_symlinks: bool,
) -> None:
    """Remove one or more items from the explicit config and retranspile."""
    # Prompt for category if missing
    if not category:
        category = questionary.select(
            "Which category do you want to remove from?",
            choices=["agent", "skill", "command", "mcp", "scope"],
            style=CUSTOM_STYLE,
        ).ask()
        if not category:
            console.print("[yellow]Cancelled.[/]")
            sys.exit(0)

    config_key = _CATEGORY_MAP.get(category.lower())
    if config_key is None:
        console.print(
            f"[red]❌ Unknown category '{category}'. "
            f"Choose from: agent, skill, command, mcp, scope[/]"
        )
        sys.exit(1)

    config = _load_config(config_path)
    if config is None:
        console.print(f"[red]❌ No config found at {config_path}. Nothing to remove.[/]")
        sys.exit(1)

    # Prompt for names if missing
    if not names:
        explicit_items: List[str] = config.get(config_key) or []
        if not explicit_items:
            console.print(
                f"[yellow]No explicit {config_key} in your config to remove.[/]"
            )
            sys.exit(0)
        names = questionary.checkbox(
            f"Select {category}(s) to remove:",
            choices=sorted(explicit_items),
            style=CUSTOM_STYLE,
        ).ask() or []
        if not names:
            console.print("[yellow]Nothing selected — cancelled.[/]")
            sys.exit(0)

    existing: List[str] = config.get(config_key) or []
    removed = []
    for name in names:
        if name in existing:
            existing.remove(name)
            removed.append(name)
        else:
            scope_derived = _scope_items(workspace, config.get("scopes", []))
            in_scope = name in scope_derived.get(config_key, set())
            hint = " (it is included via a scope — remove the scope instead)" if in_scope else ""
            console.print(f"  [yellow]⚠  {name} not found in explicit {config_key}{hint}[/]")

    config[config_key] = existing

    if removed:
        console.print(f"  [green]✓  Removed from {config_key}: {', '.join(removed)}[/]")

    _save_config(config, config_path, dry_run=dry_run)

    console.print("\n[bold]⚙  Retranspiling...[/]")
    if not _run_transpile(workspace, config, dry_run=dry_run):
        console.print("[red]❌ Transpile failed.[/]")
        sys.exit(1)

    if not no_symlinks:
        _setup_symlinks(workspace, project_root, config.get("target", "all"), dry_run=dry_run)


def cmd_apply(
    workspace: Path,
    project_root: Path,
    config_path: Path,
    dry_run: bool,
    no_symlinks: bool,
    yes: bool,
) -> None:
    """Retranspile using the saved config — remove stale artefacts first."""
    config = _load_config(config_path)
    if config is None:
        console.print(
            f"[red]❌ No config found at {config_path}.\n"
            "   Run the install wizard first: python scripts/install.py[/]"
        )
        sys.exit(1)

    console.print(f"📄 Loaded config from [bold]{config_path}[/]")
    show_summary(config, _load_available_items(workspace))

    if dry_run:
        console.print("[yellow]🔍 Dry run — no files will be written.[/]")

    # ------------------------------------------------------------------
    # Detect and remove stale output files
    # ------------------------------------------------------------------
    stale = _compute_stale_output_files(workspace, config)
    if stale:
        console.print(
            f"\n[yellow]⚠  {len(stale)} stale file(s) found that are no longer in the config:[/]"
        )
        for f in stale:
            console.print(f"  [dim]🗑  {f.relative_to(workspace)}[/]")

        if not yes and not dry_run:
            proceed = questionary.confirm(
                "Remove these files so the environment matches the config?",
                default=True,
                style=CUSTOM_STYLE,
            ).ask()
            if not proceed:
                console.print("[yellow]Apply cancelled.[/]")
                sys.exit(0)

        for f in stale:
            if dry_run:
                console.print(f"  [dim](dry-run) would remove {f.name}[/]")
            else:
                f.unlink()
                console.print(f"  [red]🗑  Removed {f.relative_to(workspace)}[/]")
    else:
        console.print("\n[green]✓  No stale files — environment already in sync.[/]")

    # ------------------------------------------------------------------
    # Regenerate
    # ------------------------------------------------------------------
    console.print("\n[bold]⚙  Running transpile...[/]")
    if not _run_transpile(workspace, config, dry_run=dry_run):
        console.print("[red]❌ Transpile failed.[/]")
        sys.exit(1)

    if not no_symlinks:
        _setup_symlinks(workspace, project_root, config.get("target", "all"), dry_run=dry_run)

    console.print(Panel.fit(
        "[bold green]✅ Apply complete![/]",
        border_style="green",
    ))


def cmd_set(
    workspace: Path,
    project_root: Path,
    config_path: Path,
    key: Optional[str],
    value: Optional[str],
    dry_run: bool,
    no_symlinks: bool,
) -> None:
    """Update a scalar setting in the config and retranspile."""
    allowed: Dict[str, List[str]] = {
        "language": ["python", "r", "both"],
        "target":   ["opencode", "continue", "claude", "all"],
    }

    # Prompt for key if missing
    if not key:
        key = questionary.select(
            "Which setting do you want to change?",
            choices=list(allowed.keys()),
            style=CUSTOM_STYLE,
        ).ask()
        if not key:
            console.print("[yellow]Cancelled.[/]")
            sys.exit(0)

    if key not in allowed:
        console.print(
            f"[red]❌ Unknown key '{key}'. Settable keys: {', '.join(allowed)}[/]"
        )
        sys.exit(1)

    # Prompt for value if missing
    if not value:
        value = questionary.select(
            f"New value for '{key}':",
            choices=allowed[key],
            style=CUSTOM_STYLE,
        ).ask()
        if not value:
            console.print("[yellow]Cancelled.[/]")
            sys.exit(0)

    if value not in allowed[key]:
        console.print(
            f"[red]❌ Invalid value '{value}' for '{key}'. "
            f"Allowed: {', '.join(allowed[key])}[/]"
        )
        sys.exit(1)

    config = _load_config(config_path)
    if config is None:
        console.print(f"[yellow]⚠  No config found at {config_path} — creating a default one.[/]")
        config = _default_config()

    old_value = config.get(key)
    config[key] = value
    console.print(f"  [green]✓  {key}: {old_value!r} → {value!r}[/]")

    _save_config(config, config_path, dry_run=dry_run)

    console.print("\n[bold]⚙  Retranspiling...[/]")
    if not _run_transpile(workspace, config, dry_run=dry_run):
        console.print("[red]❌ Transpile failed.[/]")
        sys.exit(1)

    if not no_symlinks:
        _setup_symlinks(workspace, project_root, config.get("target", "all"), dry_run=dry_run)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

# Subcommand names — used for backward-compat fallback injection
_SUBCOMMANDS = {"install", "status", "list", "add", "remove", "apply", "set"}


def main() -> None:
    # ------------------------------------------------------------------
    # Backward-compat: if the first positional arg is not a known
    # subcommand (or there are no positional args), prepend "install"
    # so existing invocations like `install.py --config foo.yaml` keep
    # working unchanged.
    # ------------------------------------------------------------------
    raw = sys.argv[1:]
    if not raw or raw[0].startswith("-") or raw[0] not in _SUBCOMMANDS:
        raw = ["install"] + raw

    # ------------------------------------------------------------------
    # Top-level parser — shared flags
    # ------------------------------------------------------------------
    top = argparse.ArgumentParser(
        description="Agent-workspace environment management CLI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    top.add_argument(
        "--project-root", metavar="PATH", default=None,
        help="Project root to install symlinks into (default: current directory).",
    )

    subs = top.add_subparsers(dest="subcommand")

    # ------------------------------------------------------------------
    # install (default / wizard)
    # ------------------------------------------------------------------
    p_install = subs.add_parser(
        "install", help="Run the interactive install wizard (default)."
    )
    p_install.add_argument(
        "--config", metavar="PATH",
        help="Load configuration from a YAML file instead of running the wizard.",
    )
    p_install.add_argument(
        "--scopes", nargs="*", metavar="SCOPE",
        help="Scopes to install (coding, stats, university, study).",
    )
    p_install.add_argument(
        "--language", choices=["python", "r", "both"], default=None,
        help="Language variant for stats/DS agents.",
    )
    p_install.add_argument(
        "--target", choices=["opencode", "continue", "claude", "all"], default=None,
        help="Platform target.",
    )
    p_install.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would be done without writing any files.",
    )
    p_install.add_argument(
        "--no-symlinks", action="store_true",
        help="Run transpile but skip symlink creation.",
    )

    # ------------------------------------------------------------------
    # status
    # ------------------------------------------------------------------
    p_status = subs.add_parser(
        "status", help="Show the current config and active items."
    )
    p_status.add_argument(
        "--config", metavar="PATH", default=None,
        help="Config file to inspect (default: install.config.yaml in project root).",
    )

    # ------------------------------------------------------------------
    # list
    # ------------------------------------------------------------------
    p_list = subs.add_parser(
        "list", help="List available items with their activation status."
    )
    p_list.add_argument(
        "category", nargs="?", default=None,
        metavar="CATEGORY",
        help="Filter to a single category: agent, skill, command, mcp, scope.",
    )
    p_list.add_argument(
        "--config", metavar="PATH", default=None,
        help="Config file to read active items from.",
    )

    # ------------------------------------------------------------------
    # add
    # ------------------------------------------------------------------
    p_add = subs.add_parser(
        "add", help="Add items to the active config and retranspile."
    )
    p_add.add_argument(
        "category", nargs="?", default=None, metavar="CATEGORY",
        help="Category to add to: agent, skill, command, mcp, scope. "
             "Omit to be prompted interactively.",
    )
    p_add.add_argument(
        "names", nargs="*", metavar="NAME",
        help="Item name(s) to add. Omit to be prompted interactively.",
    )
    p_add.add_argument(
        "--config", metavar="PATH", default=None,
        help="Config file to modify (default: install.config.yaml).",
    )
    p_add.add_argument("--dry-run", action="store_true")
    p_add.add_argument("--no-symlinks", action="store_true")

    # ------------------------------------------------------------------
    # remove
    # ------------------------------------------------------------------
    p_remove = subs.add_parser(
        "remove", help="Remove items from the explicit config and retranspile."
    )
    p_remove.add_argument(
        "category", nargs="?", default=None, metavar="CATEGORY",
        help="Category to remove from: agent, skill, command, mcp, scope. "
             "Omit to be prompted interactively.",
    )
    p_remove.add_argument(
        "names", nargs="*", metavar="NAME",
        help="Item name(s) to remove. Omit to be prompted interactively.",
    )
    p_remove.add_argument(
        "--config", metavar="PATH", default=None,
        help="Config file to modify (default: install.config.yaml).",
    )
    p_remove.add_argument("--dry-run", action="store_true")
    p_remove.add_argument("--no-symlinks", action="store_true")

    # ------------------------------------------------------------------
    # apply
    # ------------------------------------------------------------------
    p_apply = subs.add_parser(
        "apply", help="Retranspile using the saved install.config.yaml — no prompts."
    )
    p_apply.add_argument(
        "--config", metavar="PATH", default=None,
        help="Config file to apply (default: install.config.yaml).",
    )
    p_apply.add_argument("--dry-run", action="store_true")
    p_apply.add_argument("--no-symlinks", action="store_true")
    p_apply.add_argument(
        "-y", "--yes", action="store_true",
        help="Skip confirmation prompt when removing stale files.",
    )

    # ------------------------------------------------------------------
    # set
    # ------------------------------------------------------------------
    p_set = subs.add_parser(
        "set", help="Update a scalar setting (language, target) and retranspile."
    )
    p_set.add_argument(
        "key", nargs="?", default=None, metavar="KEY",
        help="Setting to change: language, target. Omit to be prompted interactively.",
    )
    p_set.add_argument(
        "value", nargs="?", default=None, metavar="VALUE",
        help="New value. Omit to be prompted interactively.",
    )
    p_set.add_argument(
        "--config", metavar="PATH", default=None,
        help="Config file to modify (default: install.config.yaml).",
    )
    p_set.add_argument("--dry-run", action="store_true")
    p_set.add_argument("--no-symlinks", action="store_true")

    # ------------------------------------------------------------------
    # Parse
    # ------------------------------------------------------------------
    args = top.parse_args(raw)

    workspace = _find_workspace_root()
    project_root = Path(args.project_root).resolve() if args.project_root else Path.cwd()

    console.print(f"[dim]Workspace: {workspace}[/]")
    console.print(f"[dim]Project:   {project_root}[/]\n")

    # Resolve config path for management commands
    def _resolve_config_path(explicit: Optional[str]) -> Path:
        if explicit:
            return Path(explicit).resolve()
        return project_root / "install.config.yaml"

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------
    if args.subcommand == "status":
        cmd_status(workspace, project_root, _resolve_config_path(args.config))

    elif args.subcommand == "list":
        cmd_list(workspace, project_root, _resolve_config_path(args.config), args.category)

    elif args.subcommand == "add":
        cmd_add(
            workspace, project_root,
            _resolve_config_path(args.config),
            args.category, args.names,
            args.dry_run, args.no_symlinks,
        )

    elif args.subcommand == "remove":
        cmd_remove(
            workspace, project_root,
            _resolve_config_path(args.config),
            args.category, args.names,
            args.dry_run, args.no_symlinks,
        )

    elif args.subcommand == "apply":
        cmd_apply(
            workspace, project_root,
            _resolve_config_path(args.config),
            args.dry_run, args.no_symlinks, args.yes,
        )

    elif args.subcommand == "set":
        cmd_set(
            workspace, project_root,
            _resolve_config_path(args.config),
            args.key, args.value,
            args.dry_run, args.no_symlinks,
        )

    else:
        # "install" subcommand — original wizard logic
        available = _load_available_items(workspace)

        if args.config:
            config_path = Path(args.config)
            if not config_path.exists():
                console.print(f"[red]❌ Config file not found: {config_path}[/]")
                sys.exit(1)
            config = _load_config(config_path) or {}
            console.print(f"📄 Loaded config from [bold]{config_path}[/]")
        elif args.scopes or args.language or args.target:
            config = {
                "scopes": args.scopes or [],
                "language": args.language or "python",
                "target": args.target or "all",
                "agents": [],
                "skills": [],
                "commands": [],
                "mcp_servers": [],
                "_save": False,
            }
        else:
            config = run_wizard(workspace, available)

        # Apply CLI overrides on top of loaded config
        if args.language:
            config["language"] = args.language
        if args.target:
            config["target"] = args.target

        show_summary(config, available)

        if args.dry_run:
            console.print("[yellow]🔍 Dry run — no files will be written.[/]")

        # Confirm before proceeding (only in interactive mode)
        if not args.config and not args.scopes and not args.language and not args.target:
            proceed = questionary.confirm(
                "Proceed with installation?", default=True, style=CUSTOM_STYLE
            ).ask()
            if not proceed:
                console.print("[yellow]Installation cancelled.[/]")
                sys.exit(0)

        # Save config
        if config.pop("_save", False) and not args.dry_run:
            _save_config(config, project_root / "install.config.yaml", dry_run=False)

        # Transpile
        console.print("\n[bold]⚙  Running transpile...[/]")
        success = _run_transpile(workspace, config, dry_run=args.dry_run)
        if not success:
            console.print("[red]❌ Transpile failed. Check output above.[/]")
            sys.exit(1)

        # Symlinks
        if not args.no_symlinks:
            target = config.get("target", "all")
            _setup_symlinks(workspace, project_root, target, dry_run=args.dry_run)

        console.print(Panel.fit(
            "[bold green]✅ Installation complete![/]\n\n"
            "Your project now has access to the selected agents, skills, and commands.\n"
            "[dim]To update: git submodule update --remote && python scripts/install.py[/]",
            border_style="green",
        ))


if __name__ == "__main__":
    main()
