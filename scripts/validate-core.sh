#!/bin/bash
# Pre-commit validation script
# Run this before committing changes to core/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔍 Running pre-commit validation..."
echo ""

cd "$WORKSPACE_DIR"

# Install dependencies if needed
if ! python -c "import yaml" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -q pyyaml
fi

# Run validation
echo "📋 Validating core definitions..."
if python build/validate.py; then
    echo ""
    echo "✅ Validation passed!"
else
    echo ""
    echo "❌ Validation failed. Please fix the errors above."
    exit 1
fi

# Check dependencies
echo ""
echo "🔗 Checking dependencies..."
if python build/check-dependencies.py; then
    echo ""
    echo "✅ All dependencies satisfied!"
else
    echo ""
    echo "⚠️  Some dependencies are missing."
    echo "   Make sure all referenced MCP servers and tools exist."
    exit 1
fi

# Test transpilation
echo ""
echo "🔨 Testing transpilation..."
mkdir -p /tmp/agent-workspace-test
if python build/transpile.py --target all --input core/ --output /tmp/agent-workspace-test/; then
    echo ""
    echo "✅ Transpilation successful!"
    rm -rf /tmp/agent-workspace-test
else
    echo ""
    echo "❌ Transpilation failed."
    exit 1
fi

echo ""
echo "✨ All checks passed! Ready to commit."
