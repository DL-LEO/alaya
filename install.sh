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

# Check if setup wizard exists
WIZARD="$SCRIPT_DIR/scripts/setup_wizard.py"
if [ -f "$WIZARD" ]; then
    echo ""
    echo "Run setup wizard? (y/n)"
    read -r RUN_WIZARD
    if [ "$RUN_WIZARD" = "y" ] || [ "$RUN_WIZARD" = "Y" ]; then
        $PYTHON "$WIZARD"
    fi
else
    echo "Setup wizard not found. You can run it later."
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Place your knowledge cards in wiki/"
echo "  2. Say 'alaya init' or 'scan cards' to your Agent"
echo "  3. Start chatting: 'Enable Alaya'"
