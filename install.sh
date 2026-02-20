#!/bin/bash
# Vox installer — one-liner or local install
#
#   curl -fsSL https://raw.githubusercontent.com/almas-cp/vox/refs/heads/main/install.sh | bash
#
# Works on all Debian-based distros (Ubuntu, Kali, Debian, Pop!_OS, etc.)

set -e

REPO_URL="https://github.com/almas-cp/vox.git"
BOLD="\033[1m"
GREEN="\033[32m"
RED="\033[31m"
CYAN="\033[36m"
DIM="\033[2m"
RESET="\033[0m"

info()  { echo -e "  ${CYAN}›${RESET} $1"; }
ok()    { echo -e "  ${GREEN}✓${RESET} $1"; }
fail()  { echo -e "  ${RED}✗${RESET} $1"; exit 1; }

echo ""
echo -e "  ${BOLD}Installing vox${RESET}"
echo ""

# ── Check for root / sudo ─────────────────────────────────────────────────────
SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    if command -v sudo &> /dev/null; then
        SUDO="sudo"
    else
        fail "This script needs root privileges. Run with sudo or as root."
    fi
fi

# ── Install system dependencies (Debian/Ubuntu/Kali) ──────────────────────────
install_if_missing() {
    if ! command -v "$1" &> /dev/null; then
        info "Installing $1..."
        $SUDO apt-get update -qq > /dev/null 2>&1
        $SUDO apt-get install -y -qq "$2" > /dev/null 2>&1
        ok "$1 installed"
    fi
}

install_if_missing git git
install_if_missing python3 python3
install_if_missing pip python3-pip

# ── Determine install source ──────────────────────────────────────────────────
# If running via curl pipe (or the project dir doesn't exist here), clone it
CLEANUP_DIR=""
if [ ! -f "pyproject.toml" ] || ! grep -q 'name = "vox"' pyproject.toml 2>/dev/null; then
    TMPDIR=$(mktemp -d)
    CLEANUP_DIR="$TMPDIR"
    info "Cloning vox..."
    git clone --depth 1 --quiet "$REPO_URL" "$TMPDIR/vox"
    cd "$TMPDIR/vox"
    ok "Repository cloned"
fi

# ── Install vox ───────────────────────────────────────────────────────────────
info "Installing vox via pip..."
pip install --break-system-packages . 2>/dev/null || pip install . 2>/dev/null || pip install --user . 2>/dev/null || fail "pip install failed"

# Verify
if ! command -v vox &> /dev/null; then
    # Check common pip install locations
    if [ -f "$HOME/.local/bin/vox" ]; then
        export PATH="$PATH:$HOME/.local/bin"
        info "vox installed to ~/.local/bin (adding to PATH)"
    else
        echo ""
        fail "Install finished but 'vox' not found in PATH. Try: export PATH=\$PATH:\$HOME/.local/bin"
    fi
fi

ok "vox installed"

# ── Shell integration ─────────────────────────────────────────────────────────
SHELL_INIT='eval "$(vox --shell-init)"'
MARKER="# vox shell integration"

add_to_rc() {
    local rc_file="$1"
    if [ -f "$rc_file" ]; then
        if ! grep -qF "$MARKER" "$rc_file"; then
            echo "" >> "$rc_file"
            echo "$MARKER" >> "$rc_file"
            echo "$SHELL_INIT" >> "$rc_file"
            ok "Added shell integration to $rc_file"
        else
            info "Shell integration already in $rc_file"
        fi
    fi
}

# Detect shell and add integration
if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/bin/zsh" ] || [ "$SHELL" = "/usr/bin/zsh" ]; then
    add_to_rc "$HOME/.zshrc"
else
    add_to_rc "$HOME/.bashrc"
fi

# Also add to the other if it exists
[ -f "$HOME/.zshrc" ] && add_to_rc "$HOME/.zshrc"
[ -f "$HOME/.bashrc" ] && add_to_rc "$HOME/.bashrc"

# ── Cleanup temp directory ────────────────────────────────────────────────────
if [ -n "$CLEANUP_DIR" ]; then
    rm -rf "$CLEANUP_DIR"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "  ${GREEN}${BOLD}vox is ready!${RESET}"
echo ""
echo -e "  ${DIM}1.${RESET} Reload your shell:  ${CYAN}source ~/.bashrc${RESET}  ${DIM}(or ~/.zshrc)${RESET}"
echo -e "  ${DIM}2.${RESET} First-time setup:   ${CYAN}vox --setup${RESET}"
echo -e "  ${DIM}3.${RESET} Start using it:     ${CYAN}vox list all files here${RESET}"
echo ""
