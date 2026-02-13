#!/bin/bash
# Vox installer — installs vox system-wide so it persists across reboots

set -e

echo ""
echo "  Installing vox..."
echo ""

# Install into system Python (persists across reboots)
pip install --break-system-packages . 2>/dev/null || pip install .

# Verify
if command -v vox &> /dev/null; then
    echo ""
    echo "  ✓ vox installed successfully"
    echo "  Run 'vox --setup' to configure your API key"
    echo ""
else
    echo ""
    echo "  ✗ Install finished but 'vox' not found in PATH"
    echo "  Try: export PATH=\$PATH:\$HOME/.local/bin"
    echo "  Then add that line to your ~/.bashrc or ~/.zshrc"
    echo ""
fi
