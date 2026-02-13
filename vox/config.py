"""Configuration management for Vox — API key storage and first-run onboarding."""

import json
import os
import sys
import stat

CONFIG_DIR = os.path.expanduser("~/.vox")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# ANSI colors
YELLOW = "\033[33m"
RED = "\033[31m"
GREEN = "\033[32m"
DIM = "\033[2m"
RESET = "\033[0m"


def _ensure_config_dir():
    """Create ~/.vox directory if it doesn't exist."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, mode=0o700)


def _save_config(config: dict):
    """Save config to disk with restricted permissions."""
    _ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    # Set file permissions to 600 (owner read/write only)
    os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)


def load_config() -> dict | None:
    """Load config from disk. Returns None if no config exists."""
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def get_api_key() -> str | None:
    """Get the stored API key, or None if not configured."""
    config = load_config()
    if config and "api_key" in config:
        return config["api_key"]
    return None


def run_setup():
    """Interactive first-run onboarding / reconfiguration."""
    print(f"\n{YELLOW}Vox Setup{RESET}")
    print(f"{DIM}Your API key will be stored in ~/.vox/config.json{RESET}\n")

    try:
        api_key = input("  Enter your API key: ").strip()
    except (KeyboardInterrupt, EOFError):
        print(f"\n{DIM}Setup cancelled.{RESET}")
        sys.exit(0)

    if not api_key:
        print(f"  {RED}Key cannot be empty.{RESET}")
        return

    _save_config({"api_key": api_key})
    print(f"\n  {GREEN}✓ Saved.{RESET} Run `vox <request>` to get started.\n")


def reset_config():
    """Delete stored configuration."""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
        print(f"{GREEN}✓ Configuration reset.{RESET} Run `vox --setup` to reconfigure.")
    else:
        print(f"{DIM}No configuration found.{RESET}")
