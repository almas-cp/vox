"""Configuration management for Vox — API key storage, model selection, and onboarding."""

import json
import os
import sys
import stat

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich import box

console = Console()

CONFIG_DIR = os.path.expanduser("~/.vox")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# ── API Providers ──────────────────────────────────────────────────────────────

PROVIDERS = {
    "groq": {
        "name": "Groq",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key_url": "https://console.groq.com/keys",
        "key_prefix": "gsk_",
    },
    "digitalocean": {
        "name": "DigitalOcean Gradient",
        "url": "https://inference.do-ai.run/v1/chat/completions",
        "key_url": "https://cloud.digitalocean.com/gradient",
        "key_prefix": "sk-do-",
    },
}

DEFAULT_PROVIDER = "groq"

# ── Models (ordered lightest → heaviest per provider) ──────────────────────────

MODELS = {
    "groq": [
        ("openai/gpt-oss-20b",                          "GPT-OSS 20B",           "fast, lightweight"),
        ("llama-3.1-8b-instant",                         "Llama 3.1 8B",          "fastest, instant"),
        ("qwen/qwen3-32b",                               "Qwen 3 32B",            "good balance"),
        ("llama-3.3-70b-versatile",                      "Llama 3.3 70B",         "powerful, versatile"),
        ("openai/gpt-oss-120b",                          "GPT-OSS 120B",          "most powerful"),
        ("meta-llama/llama-4-scout-17b-16e-instruct",    "Llama 4 Scout",         "preview, latest gen"),
        ("meta-llama/llama-4-maverick-17b-128e-instruct","Llama 4 Maverick",      "preview, latest gen"),
        ("moonshotai/kimi-k2-instruct-0905",             "Kimi K2",               "preview, reasoning"),
    ],
    "digitalocean": [
        ("llama3-8b-instruct",           "Llama 3 8B",           "fastest, lightweight"),
        ("mistral-nemo-instruct-2407",   "Mistral Nemo",         "fast, efficient"),
        ("alibaba-qwen3-32b",           "Qwen 3 32B",           "good balance"),
        ("llama3.3-70b-instruct",       "Llama 3.3 70B",        "powerful, open-source"),
        ("deepseek-r1-distill-llama-70b","DeepSeek R1 70B",      "reasoning focused"),
        ("anthropic-claude-3.5-haiku",  "Claude 3.5 Haiku",     "fast, premium"),
        ("openai-gpt-4o-mini",          "GPT-4o Mini",          "fast, premium"),
        ("anthropic-claude-3.7-sonnet", "Claude 3.7 Sonnet",    "powerful, premium"),
        ("openai-gpt-4o",               "GPT-4o",               "powerful, premium"),
        ("anthropic-claude-opus-4.6",   "Claude Opus 4.6",      "top-tier"),
        ("openai-gpt-5",                "GPT-5",                "top-tier"),
    ],
}

DEFAULT_MODELS = {
    "groq": "llama-3.3-70b-versatile",
    "digitalocean": "llama3.3-70b-instruct",
}


def _ensure_config_dir():
    """Create ~/.vox directory if it doesn't exist."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, mode=0o700)


def _save_config(config: dict):
    """Save config to disk with restricted permissions."""
    _ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
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
    """Get the stored model, or default for current provider."""
    config = load_config()
    provider = get_provider()
    if config and "model" in config:
        return config["model"]
    return DEFAULT_MODELS.get(provider, "llama-3.3-70b-versatile")


def get_provider() -> str:
    """Get the stored provider, or default."""
    config = load_config()
    if config and "provider" in config:
        return config["provider"]
    return DEFAULT_PROVIDER


def get_api_url() -> str:
    """Get the API URL for the current provider."""
    provider = get_provider()
    return PROVIDERS[provider]["url"]


def _pick_provider() -> str:
    """Interactive provider selection."""
    console.print()
    table = Table(
        box=box.ROUNDED,
        title="[bold]API Provider[/bold]",
        title_style="cyan",
        show_header=True,
        header_style="bold dim",
        padding=(0, 2),
    )
    table.add_column("#", style="cyan", width=3)
    table.add_column("Provider", style="bold white")
    table.add_column("Get Key", style="dim")

    for i, (key, info) in enumerate(PROVIDERS.items(), 1):
        default = " [green]← default[/green]" if key == DEFAULT_PROVIDER else ""
        table.add_row(str(i), f"{info['name']}{default}", info["key_url"])

    console.print(table)
    console.print()

    while True:
        choice = Prompt.ask(
            "  [dim]Choice[/dim]",
            default="1",
        )
        try:
            idx = int(choice) - 1
            providers = list(PROVIDERS.keys())
            if 0 <= idx < len(providers):
                selected = providers[idx]
                console.print(f"  [green]✓[/green] {PROVIDERS[selected]['name']}")
                return selected
        except ValueError:
            pass
        console.print(f"  [red]Enter 1 or {len(PROVIDERS)}[/red]")


def _pick_model(provider: str) -> str:
    """Interactive model selection menu."""
    models = MODELS.get(provider, [])
    default_model = DEFAULT_MODELS.get(provider, "")

    console.print()
    table = Table(
        box=box.ROUNDED,
        title="[bold]Select Model[/bold] [dim](lightest → heaviest)[/dim]",
        title_style="cyan",
        show_header=True,
        header_style="bold dim",
        padding=(0, 2),
    )
    table.add_column("#", style="cyan", width=3)
    table.add_column("Model", style="bold white", min_width=22)
    table.add_column("Description", style="dim")

    for i, (model_id, name, desc) in enumerate(models, 1):
        default = " [green]← default[/green]" if model_id == default_model else ""
        table.add_row(str(i), f"{name}{default}", desc)

    console.print(table)
    console.print()

    while True:
        choice = Prompt.ask(
            "  [dim]Choice[/dim]",
            default=str(next(
                (i for i, (mid, _, _) in enumerate(models, 1) if mid == default_model),
                1
            )),
        )
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                selected = models[idx]
                console.print(f"  [green]✓[/green] {selected[1]} [dim]({selected[0]})[/dim]")
                return selected[0]
        except ValueError:
            pass
        console.print(f"  [red]Enter a number between 1 and {len(models)}[/red]")


def run_setup():
    """Interactive first-run onboarding / reconfiguration."""
    console.print()
    console.print(
        Panel(
            "[bold white]Vox Setup[/bold white]\n[dim]Config stored in ~/.vox/config.json[/dim]",
            border_style="cyan",
            padding=(1, 4),
        )
    )

    config = load_config() or {}

    # 1. Provider selection
    provider = _pick_provider()
    config["provider"] = provider

    # 2. API key
    console.print()
    provider_info = PROVIDERS[provider]
    current_key = config.get("api_key", "")

    if current_key:
        masked = current_key[:8] + "..." + current_key[-4:]
        console.print(f"  [dim]Current key: {masked}[/dim]")

    console.print(f"  [dim]Get a key at: {provider_info['key_url']}[/dim]")
    api_key = Prompt.ask(
        "  API key [dim](Enter to keep current)[/dim]",
        default=current_key if current_key else ...,
        show_default=False,
    )

    if not api_key:
        console.print("  [red]Key cannot be empty.[/red]")
        return

    config["api_key"] = api_key

    # 3. Model selection
    config["model"] = _pick_model(provider)

    _save_config(config)
    console.print()
    console.print(
        Panel(
            "[green]✓ Saved![/green] Run [bold cyan]vox <request>[/bold cyan] to get started.",
            border_style="green",
            padding=(0, 2),
        )
    )
    console.print()


def reset_config():
    """Delete stored configuration."""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
        console.print("[green]✓ Configuration reset.[/green] Run [cyan]vox --setup[/cyan] to reconfigure.")
    else:
        console.print("[dim]No configuration found.[/dim]")
