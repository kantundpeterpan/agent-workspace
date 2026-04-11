#!/bin/bash
# Installation script for agent-workspace
# Supports scope-based installation and optional config file.
#
# Usage:
#   bash scripts/install.sh                                  # install all (no filters)
#   bash scripts/install.sh --scope stats                    # single scope
#   bash scripts/install.sh --scope stats --scope university # multiple scopes
#   bash scripts/install.sh --scope stats --language r       # R-only stats agents
#   bash scripts/install.sh --config install.config.yaml     # use config file
#   bash scripts/install.sh --target claude                  # single platform
#   bash scripts/install.sh --dry-run                        # preview only
#   bash scripts/install.sh --interactive                    # launch Python wizard

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(pwd)"

# ---- Defaults ----
SCOPES=()
LANGUAGE="python"
TARGET="all"
CONFIG_FILE=""
DRY_RUN=false
INTERACTIVE=false
NO_SYMLINKS=false
SKIP_TRANSPILE=false

# ---- Argument parsing ----
while [[ $# -gt 0 ]]; do
    case "$1" in
        --scope)
            SCOPES+=("$2")
            shift 2
            ;;
        --language)
            LANGUAGE="$2"
            shift 2
            ;;
        --target)
            TARGET="$2"
            shift 2
            ;;
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --interactive|-i)
            INTERACTIVE=true
            shift
            ;;
        --no-symlinks)
            NO_SYMLINKS=true
            shift
            ;;
        --skip-transpile)
            SKIP_TRANSPILE=true
            shift
            ;;
        --help|-h)
            echo "Usage: bash scripts/install.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --scope SCOPE       Scope to install: coding | stats | university | study"
            echo "                      Repeat for multiple: --scope stats --scope university"
            echo "  --language LANG     Language for stats agents: python | r | both  (default: python)"
            echo "  --target TARGET     Platform: opencode | continue | claude | all  (default: all)"
            echo "  --config PATH       Path to install.config.yaml"
            echo "  --dry-run           Preview without writing files"
            echo "  --interactive, -i   Launch the interactive Python install wizard"
            echo "  --no-symlinks       Run transpile only, skip symlink creation"
            echo "  --skip-transpile    Set up symlinks only, skip transpile"
            echo "  --help              Show this help"
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "   Run 'bash scripts/install.sh --help' for usage."
            exit 1
            ;;
    esac
done

echo "🚀 agent-workspace install"
echo "   Workspace: $WORKSPACE_DIR"
echo "   Project:   $PROJECT_ROOT"
echo ""

# ---- Validate platform dirs exist ----
if [ ! -d "$WORKSPACE_DIR/platforms" ] && [ "$SKIP_TRANSPILE" = false ]; then
    echo "❌ Error: Cannot find platforms directory at $WORKSPACE_DIR/platforms"
    echo "   Make sure you're running this from your project root"
    exit 1
fi

# ---- Interactive mode: delegate to Python wizard ----
if [ "$INTERACTIVE" = true ]; then
    PYTHON="$(command -v python3 || command -v python)"
    if [ -z "$PYTHON" ]; then
        echo "❌ Python 3 not found. Install Python 3.9+ to use the interactive wizard."
        exit 1
    fi
    echo "🐍 Launching interactive install wizard..."
    INSTALL_ARGS=("$WORKSPACE_DIR/scripts/install.py")
    [ "$DRY_RUN" = true ] && INSTALL_ARGS+=("--dry-run")
    [ "$NO_SYMLINKS" = true ] && INSTALL_ARGS+=("--no-symlinks")
    exec "$PYTHON" "${INSTALL_ARGS[@]}"
fi

# ---- Transpile with scope/config filters ----
if [ "$SKIP_TRANSPILE" = false ]; then
    PYTHON="$(command -v python3 || command -v python || echo "")"

    if [ -n "$PYTHON" ] && [ -f "$WORKSPACE_DIR/build/scope_filter.py" ]; then
        echo "⚙  Running scope-filtered transpile..."

        TRANSPILE_ARGS=("$WORKSPACE_DIR/build/scope_filter.py")
        TRANSPILE_ARGS+=("--input" "$WORKSPACE_DIR/core")
        TRANSPILE_ARGS+=("--output" "$WORKSPACE_DIR/platforms")
        TRANSPILE_ARGS+=("--target" "$TARGET")
        TRANSPILE_ARGS+=("--language" "$LANGUAGE")

        if [ -n "$CONFIG_FILE" ]; then
            TRANSPILE_ARGS+=("--config" "$CONFIG_FILE")
        fi

        if [ ${#SCOPES[@]} -gt 0 ]; then
            TRANSPILE_ARGS+=("--scopes" "${SCOPES[@]}")
        fi

        if [ "$DRY_RUN" = true ]; then
            echo "  (dry-run — transpile command would be:)"
            echo "  $PYTHON ${TRANSPILE_ARGS[*]}"
        else
            "$PYTHON" "${TRANSPILE_ARGS[@]}"
        fi
    else
        echo "  ⚠️  Python not found or scope_filter.py missing — skipping transpile."
        echo "     Install Python 3.9+ and run: pip install -r build/requirements.txt"
    fi
fi

# ---- Helper: create symlink ----
create_symlink() {
    local src="$1"
    local dst="$2"

    if [ "$DRY_RUN" = true ]; then
        echo "  (dry-run) would link: $dst -> $src"
        return 0
    fi

    if [ -L "$dst" ]; then
        echo "  ✓ $dst already linked"
        return 0
    fi

    if [ -e "$dst" ]; then
        echo "  ⚠️  $dst exists — backed up to ${dst}.backup"
        mv "$dst" "${dst}.backup"
    fi

    ln -s "$src" "$dst"
    echo "  ✓ $dst -> $src"
}

# ---- Set up symlinks ----
if [ "$NO_SYMLINKS" = false ]; then
    echo ""
    SETUP_OPENCODE=false
    SETUP_CONTINUE=false
    SETUP_CLAUDE=false

    case "$TARGET" in
        all)
            SETUP_OPENCODE=true
            SETUP_CONTINUE=true
            SETUP_CLAUDE=true
            ;;
        opencode)
            SETUP_OPENCODE=true
            ;;
        continue)
            SETUP_CONTINUE=true
            ;;
        claude)
            SETUP_CLAUDE=true
            ;;
    esac

    if [ "$SETUP_OPENCODE" = true ]; then
        echo "🔧 Setting up OpenCode..."
        if [ -d "$WORKSPACE_DIR/platforms/opencode" ]; then
            create_symlink "$WORKSPACE_DIR/platforms/opencode" "$PROJECT_ROOT/.agents"
            create_symlink "$WORKSPACE_DIR/platforms/opencode" "$PROJECT_ROOT/.opencode"
        else
            echo "  ⚠️  OpenCode platform not found (run transpile first)"
        fi
    fi

    if [ "$SETUP_CONTINUE" = true ]; then
        echo "🔧 Setting up Continue.dev..."
        if [ -d "$WORKSPACE_DIR/platforms/continue" ]; then
            create_symlink "$WORKSPACE_DIR/platforms/continue" "$PROJECT_ROOT/.continue"
        else
            echo "  ⚠️  Continue platform not found (run transpile first)"
        fi
    fi

    if [ "$SETUP_CLAUDE" = true ]; then
        echo "🔧 Setting up Claude Code..."
        if [ -f "$WORKSPACE_DIR/platforms/claude/CLAUDE.md" ]; then
            create_symlink "$WORKSPACE_DIR/platforms/claude/CLAUDE.md" "$PROJECT_ROOT/CLAUDE.md"
        else
            echo "  ⚠️  CLAUDE.md not found (run transpile first)"
        fi
    fi
fi

echo ""
if [ "$DRY_RUN" = true ]; then
    echo "🔍 Dry run complete — no files were written."
else
    echo "✅ Setup complete!"
    echo ""
    if [ ${#SCOPES[@]} -gt 0 ]; then
        echo "   Scopes:   ${SCOPES[*]}"
    fi
    echo "   Language: $LANGUAGE"
    echo "   Target:   $TARGET"
    echo ""
    echo "To update to latest:"
    echo "  git submodule update --remote"
    echo "  bash scripts/install.sh --scope ${SCOPES[*]:-(all)} --language $LANGUAGE"
    echo ""
    echo "For full interactive setup:"
    echo "  bash scripts/install.sh --interactive"
fi
