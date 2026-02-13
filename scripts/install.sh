#!/bin/bash
# Installation script for agent-workspace submodule
# Creates symlinks from platforms to tool-specific locations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(pwd)"

echo "🚀 Setting up agent-workspace..."
echo "   Workspace: $WORKSPACE_DIR"
echo "   Project: $PROJECT_ROOT"
echo ""

# Function to create symlink
create_symlink() {
    local src="$1"
    local dst="$2"
    
    if [ -L "$dst" ]; then
        echo "  ✓ $dst already linked"
        return 0
    fi
    
    if [ -e "$dst" ]; then
        echo "  ⚠️  $dst exists but is not a symlink. Backup to ${dst}.backup"
        mv "$dst" "${dst}.backup"
    fi
    
    ln -s "$src" "$dst"
    echo "  ✓ Linked $dst -> $src"
}

# Check if running from project root
if [ ! -d "$WORKSPACE_DIR/platforms" ]; then
    echo "❌ Error: Cannot find platforms directory"
    echo "   Make sure you're running this from your project root"
    exit 1
fi

# Setup OpenCode
echo "🔧 Setting up OpenCode..."
if [ -d "$WORKSPACE_DIR/platforms/opencode" ]; then
    create_symlink "$WORKSPACE_DIR/platforms/opencode" "$PROJECT_ROOT/.opencode"
    mkdir -p "$PROJECT_ROOT/.opencode/skills"
else
    echo "  ⚠️  OpenCode platform not found"
fi

# Setup Continue
echo "🔧 Setting up Continue.dev..."
if [ -d "$WORKSPACE_DIR/platforms/continue" ]; then
    create_symlink "$WORKSPACE_DIR/platforms/continue" "$PROJECT_ROOT/.continue"
    mkdir -p "$PROJECT_ROOT/.continue/skills"
else
    echo "  ⚠️  Continue platform not found"
fi

# Setup Claude Code
echo "🔧 Setting up Claude Code..."
if [ -f "$WORKSPACE_DIR/platforms/claude/CLAUDE.md" ]; then
    create_symlink "$WORKSPACE_DIR/platforms/claude/CLAUDE.md" "$PROJECT_ROOT/CLAUDE.md"
else
    echo "  ⚠️  Claude Code CLAUDE.md not found"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Your project now has symlinks to:"
echo "  - .opencode/ -> agent-workspace/platforms/opencode/"
echo "  - .continue/ -> agent-workspace/platforms/continue/"
echo "  - CLAUDE.md -> agent-workspace/platforms/claude/CLAUDE.md"
echo ""
echo "To update to latest:"
echo "  git submodule update --remote"
echo ""
echo "Note: Don't edit files in the symlinked directories directly."
echo "      Edit files in agent-workspace/core/ instead."
