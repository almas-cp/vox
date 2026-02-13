#!/bin/bash
# Vox installer — installs vox system-wide and sets up shell integration

set -e

echo ""
echo "  Installing vox..."
echo ""

# Install into system Python (persists across reboots)
pip install --break-system-packages . 2>/dev/null || pip install .

# Verify
if ! command -v vox &> /dev/null; then
    echo ""
    echo "  ✗ Install finished but 'vox' not found in PATH"
    echo "  Try: export PATH=\$PATH:\$HOME/.local/bin"
    echo ""
    exit 1
fi

echo ""
echo "  ✓ vox installed"

# Shell integration — add wrapper function for history support
SHELL_INIT='eval "$(vox --shell-init)"'
MARKER="# vox shell integration"

add_to_rc() {
    local rc_file="$1"
    if [ -f "$rc_file" ]; then
        if ! grep -qF "$MARKER" "$rc_file"; then
            echo "" >> "$rc_file"
            echo "$MARKER" >> "$rc_file"
            echo "$SHELL_INIT" >> "$rc_file"
            echo "  ✓ Added shell integration to $rc_file"
        else
            echo "  · Shell integration already in $rc_file"
        fi
    fi
}

# Add to whichever rc files exist
if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/bin/zsh" ] || [ "$SHELL" = "/usr/bin/zsh" ]; then
    add_to_rc "$HOME/.zshrc"
else
    add_to_rc "$HOME/.bashrc"
fi

# Also add to the other if it exists (user might switch shells)
[ -f "$HOME/.zshrc" ] && add_to_rc "$HOME/.zshrc"
[ -f "$HOME/.bashrc" ] && add_to_rc "$HOME/.bashrc"

echo ""
echo "  To activate now, run:  source ~/.zshrc  (or ~/.bashrc)"
echo "  Then run:              vox --setup"
echo ""
