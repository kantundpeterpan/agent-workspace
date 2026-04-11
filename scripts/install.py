#!/usr/bin/env python3
"""
Interactive CLI install assistant for agent-workspace.

Usage:
    python scripts/install.py                          # fully interactive
    python scripts/install.py --config install.config.yaml  # use saved config
    python scripts/install.py --scopes stats university --language r
    python scripts/install.py --dry-run               # preview without writing files
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

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
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interactive install assistant for agent-workspace.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--config", metavar="PATH",
        help="Load configuration from a YAML file instead of running the wizard."
    )
    parser.add_argument(
        "--scopes", nargs="*", metavar="SCOPE",
        help="Scopes to install (coding, stats, university, study)."
    )
    parser.add_argument(
        "--language", choices=["python", "r", "both"], default=None,
        help="Language variant for stats/DS agents."
    )
    parser.add_argument(
        "--target", choices=["opencode", "continue", "claude", "all"], default=None,
        help="Platform target."
    )
    parser.add_argument(
        "--project-root", metavar="PATH", default=None,
        help="Project root to install symlinks into (default: current directory)."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would be done without writing any files."
    )
    parser.add_argument(
        "--no-symlinks", action="store_true",
        help="Run transpile but skip symlink creation."
    )

    args = parser.parse_args()

    workspace = _find_workspace_root()
    project_root = Path(args.project_root).resolve() if args.project_root else Path.cwd()
    available = _load_available_items(workspace)

    console.print(f"[dim]Workspace: {workspace}[/]")
    console.print(f"[dim]Project:   {project_root}[/]\n")

    # ---- Load or collect config ----
    if args.config:
        # Load from file
        import yaml as _yaml
        config_path = Path(args.config)
        if not config_path.exists():
            console.print(f"[red]❌ Config file not found: {config_path}[/]")
            sys.exit(1)
        with open(config_path) as f:
            config = _yaml.safe_load(f) or {}
        console.print(f"📄 Loaded config from [bold]{config_path}[/]")
    elif args.scopes or args.language or args.target:
        # Non-interactive mode from CLI flags
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
        # Full interactive wizard
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

    # ---- Save config ----
    if config.pop("_save", False) and not args.dry_run:
        _save_config(config, project_root / "install.config.yaml", dry_run=False)

    # ---- Transpile ----
    console.print("\n[bold]⚙  Running transpile...[/]")
    success = _run_transpile(workspace, config, dry_run=args.dry_run)
    if not success:
        console.print("[red]❌ Transpile failed. Check output above.[/]")
        sys.exit(1)

    # ---- Symlinks ----
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
