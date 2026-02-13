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
BOLD = "\033[1m"
CYAN = "\033[36m"
RESET = "\033[0m"

# Available models, ordered lightest → heaviest
MODELS = [
    ("llama3-8b-instruct",           "Llama 3 8B",              "fastest, lightweight"),
    ("mistral-nemo-instruct-2407",   "Mistral Nemo",            "fast, efficient"),
    ("alibaba-qwen3-32b",           "Qwen 3 32B",              "good balance"),
    ("llama3.3-70b-instruct",       "Llama 3.3 70B",           "powerful, open-source"),
    ("deepseek-r1-distill-llama-70b","DeepSeek R1 70B",         "reasoning focused"),
    ("anthropic-claude-3.5-haiku",  "Claude 3.5 Haiku",        "fast, premium"),
    ("openai-gpt-4o-mini",          "GPT-4o Mini",             "fast, premium"),
    ("anthropic-claude-3.7-sonnet", "Claude 3.7 Sonnet",       "powerful, premium"),
    ("openai-gpt-4o",               "GPT-4o",                  "powerful, premium"),
    ("anthropic-claude-opus-4.6",   "Claude Opus 4.6",         "top-tier"),
    ("openai-gpt-5-mini",           "GPT-5 Mini",              "latest gen"),
    ("openai-gpt-5",                "GPT-5",                   "top-tier"),
]

DEFAULT_MODEL = "llama3.3-70b-instruct"


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


def get_model() -> str:
    """Get the stored model, or default."""
    config = load_config()
    if config and "model" in config:
        return config["model"]
    return DEFAULT_MODEL


def _pick_model() -> str:
    """Interactive model selection menu."""
    print(f"\n  {BOLD}Select a model{RESET} {DIM}(lightest → heaviest):{RESET}\n")

    for i, (model_id, name, desc) in enumerate(MODELS, 1):
        marker = f" {GREEN}← current default{RESET}" if model_id == DEFAULT_MODEL else ""
        print(f"  {CYAN}{i:>2}{RESET}  {name:<24} {DIM}{desc}{RESET}{marker}")

    print()

    while True:
        try:
            choice = input(f"  Choice [1-{len(MODELS)}]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{DIM}Setup cancelled.{RESET}")
            sys.exit(0)

        if not choice:
            # Default selection
            return DEFAULT_MODEL

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(MODELS):
                selected = MODELS[idx]
                print(f"  {GREEN}✓{RESET} {selected[1]} ({selected[0]})")
                return selected[0]
        except ValueError:
            pass

        print(f"  {RED}Enter a number between 1 and {len(MODELS)}{RESET}")


def run_setup():
    """Interactive first-run onboarding / reconfiguration."""
    print(f"\n{YELLOW}Vox Setup{RESET}")
    print(f"{DIM}Config stored in ~/.vox/config.json{RESET}")

    # Load existing config to preserve values
    config = load_config() or {}

    # API key
    print()
    current_key = config.get("api_key", "")
    if current_key:
        masked = current_key[:8] + "..." + current_key[-4:]
        print(f"  {DIM}Current key: {masked}{RESET}")
    try:
        api_key = input("  Enter API key (or press Enter to keep current): ").strip()
    except (KeyboardInterrupt, EOFError):
        print(f"\n{DIM}Setup cancelled.{RESET}")
        sys.exit(0)

    if api_key:
        config["api_key"] = api_key
    elif not current_key:
        print(f"  {RED}Key cannot be empty.{RESET}")
        return

    # Model selection
    config["model"] = _pick_model()

    _save_config(config)
    print(f"\n  {GREEN}✓ Saved.{RESET} Run `vox <request>` to get started.\n")


def reset_config():
    """Delete stored configuration."""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
        print(f"{GREEN}✓ Configuration reset.{RESET} Run `vox --setup` to reconfigure.")
    else:
        print(f"{DIM}No configuration found.{RESET}")
