#!/bin/bash
# Alaya · 识海 — Setup Script (Mac/Linux/WSL)
# Usage: bash install.sh

set -e

echo "=== Alaya · 识海 Setup ==="
echo ""

# Resolve script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "ERROR: Python 3 not found. Please install Python 3.8+."
    exit 1
fi

echo "Python found: $($PYTHON --version)"

VERIFY="$SCRIPT_DIR/scripts/verify_installation.py"
$PYTHON "$VERIFY" --root "$SCRIPT_DIR"

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Say 'alaya init' or '初始化识海' to choose a separate knowledge-base location."
echo "  2. The skill installation has not created or modified a knowledge base."
