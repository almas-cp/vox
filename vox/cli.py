"""CLI handler for Vox — argument parsing, command execution, UX flow."""

import os
import subprocess
import sys
import time

from rich.console import Console
from rich.panel import Panel

from vox import __version__
from vox.config import get_api_key, run_setup, reset_config
from vox.llm_client import generate_command

console = Console()

# Temp file for passing command to shell wrapper
CMD_FILE_PREFIX = "/tmp/.vox_cmd_"

# Shell wrapper function that users source in their .bashrc/.zshrc
SHELL_INIT_BASH = r'''
vox() {
    local cmd_file="/tmp/.vox_cmd_$$"
    command vox "$@"
    local rc=$?
    if [ $rc -eq 0 ] && [ -f "$cmd_file" ]; then
        local cmd
        cmd=$(cat "$cmd_file")
        rm -f "$cmd_file"
        if [ -n "$cmd" ]; then
            history -s "$cmd"
            eval "$cmd"
        fi
    fi
    return $rc
}
'''

SHELL_INIT_ZSH = r'''
vox() {
    local cmd_file="/tmp/.vox_cmd_$$"
    command vox "$@"
    local rc=$?
    if [ $rc -eq 0 ] && [ -f "$cmd_file" ]; then
        local cmd
        cmd=$(cat "$cmd_file")
        rm -f "$cmd_file"
        if [ -n "$cmd" ]; then
            print -s "$cmd"
            eval "$cmd"
        fi
    fi
    return $rc
}
'''


def _clear_lines(n: int):
    """Move the cursor up n lines and clear each one."""
    for _ in range(n):
        sys.stdout.write("\033[A\033[2K")
    sys.stdout.write("\r")
    sys.stdout.flush()


def _print_usage():
    console.print()
    console.print(
        Panel(
            "[bold cyan]vox[/bold cyan] — natural language to shell commands\n\n"
            "[dim]Usage:[/dim]\n"
            "  [cyan]vox[/cyan] [white]<request>[/white]       Translate to a shell command\n"
            "  [cyan]vox[/cyan] [white]--setup[/white]         Configure API key & model\n"
            "  [cyan]vox[/cyan] [white]--reset[/white]         Remove stored configuration\n"
            "  [cyan]vox[/cyan] [white]--version[/white]       Show version\n"
            "  [cyan]vox[/cyan] [white]--shell-init[/white]    Print shell wrapper function",
            border_style="dim",
            padding=(1, 3),
        )
    )
    console.print()


def _get_cmd_file() -> str:
    """Get temp file path using parent shell PID."""
    ppid = os.getppid()
    return f"{CMD_FILE_PREFIX}{ppid}"


def _write_cmd_file(command: str):
    """Write command to temp file for the shell wrapper to pick up."""
    try:
        with open(_get_cmd_file(), "w") as f:
            f.write(command)
    except (IOError, OSError):
        pass


def _has_shell_wrapper() -> bool:
    """Check if we're on a system where the shell wrapper can work."""
    return os.path.isdir("/tmp")


def _run_directly(command: str):
    """Fallback: execute command directly via subprocess."""
    try:
        result = subprocess.run(command, shell=True)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print()
        sys.exit(130)


def _print_shell_init():
    """Print the shell wrapper function for the user's shell."""
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        print(SHELL_INIT_ZSH.strip())
    else:
        print(SHELL_INIT_BASH.strip())


def main():
    args = sys.argv[1:]

    if not args:
        _print_usage()
        return

    if args[0] in ("--help", "-h"):
        _print_usage()
        return

    if args[0] == "--version":
        console.print(f"[cyan]vox[/cyan] [bold]{__version__}[/bold]")
        return

    if args[0] == "--setup":
        run_setup()
        return

    if args[0] == "--reset":
        reset_config()
        return

    if args[0] == "--shell-init":
        _print_shell_init()
        return

    # ── Main flow ──────────────────────────────────────────────────────────────
    api_key = get_api_key()
    if not api_key:
        console.print("[yellow]First-time setup required.[/yellow]\n")
        run_setup()
        api_key = get_api_key()
        if not api_key:
            console.print("[red]⚠ Setup incomplete.[/red]")
            sys.exit(1)

    query = " ".join(args)

    # Generate command from LLM
    with console.status("[dim]Thinking...[/dim]", spinner="dots"):
        try:
            command = generate_command(query, api_key)
        except (ConnectionError, PermissionError, RuntimeError) as e:
            console.print(f"\n[red]⚠ {e}[/red]")
            sys.exit(1)

    # Display generated command and ask for confirmation
    console.print()
    console.print(f"  [bold green]{command}[/bold green]")
    console.print()

    try:
        answer = console.input("  [dim]Run? (Y/n):[/dim] ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)

    if answer in ("", "y", "yes"):
        _clear_lines(4)
        # Re-print the command so it's visible above the output
        console.print(f"[dim]$[/dim] [bold]{command}[/bold]")

        if _has_shell_wrapper():
            _write_cmd_file(command)
            sys.exit(0)
        else:
            _run_directly(command)
    else:
        _clear_lines(4)
        sys.exit(1)


if __name__ == "__main__":
    main()
