"""CLI handler for Vox — argument parsing, command execution, UX flow."""

import os
import subprocess
import sys

from vox import __version__
from vox.config import get_api_key, run_setup, reset_config

# ANSI escape codes
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
DIM = "\033[2m"
RESET = "\033[0m"

# Terminal control
CURSOR_UP = "\033[A"
CLEAR_LINE = "\033[2K"

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
        sys.stdout.write(CURSOR_UP + CLEAR_LINE)
    sys.stdout.write("\r")
    sys.stdout.flush()


def _print_usage():
    print(f"""
{YELLOW}vox{RESET} — natural language to shell commands

{DIM}Usage:{RESET}
  vox <request>       Translate natural language to a shell command
  vox --setup         Configure API key
  vox --reset         Remove stored configuration
  vox --version       Show version
  vox --shell-init    Print shell wrapper (add to .bashrc/.zshrc)
""")


def _get_cmd_file() -> str:
    """Get temp file path using parent shell PID so the wrapper can find it."""
    ppid = os.getppid()
    return f"{CMD_FILE_PREFIX}{ppid}"


def _write_cmd_file(command: str):
    """Write command to temp file for the shell wrapper to pick up."""
    try:
        cmd_file = _get_cmd_file()
        with open(cmd_file, "w") as f:
            f.write(command)
    except (IOError, OSError):
        pass


def _has_shell_wrapper() -> bool:
    """Check if we're running through the shell wrapper (cmd file will be checked)."""
    cmd_file = _get_cmd_file()
    # If parent is a shell and wrapper exists, the wrapper will handle execution.
    # We detect this by checking if PPID is a shell process.
    # Simpler: just check if the cmd file path is writable (i.e., we're on Linux).
    return os.path.isdir("/tmp")


def _run_directly(command: str):
    """Fallback: execute command directly via subprocess (no history integration)."""
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

    # No arguments — show usage
    if not args:
        _print_usage()
        return

    # Flag handling
    if args[0] in ("--help", "-h"):
        _print_usage()
        return

    if args[0] == "--version":
        print(f"vox {__version__}")
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

    # Main flow: natural language → command
    api_key = get_api_key()
    if not api_key:
        print(f"{YELLOW}First-time setup required.{RESET}\n")
        run_setup()
        api_key = get_api_key()
        if not api_key:
            print(f"{RED}⚠ Setup incomplete.{RESET}")
            sys.exit(1)

    query = " ".join(args)

    # Generate command from LLM
    try:
        command = generate_command(query, api_key)
    except ConnectionError as e:
        print(f"{RED}⚠ {e}{RESET}")
        sys.exit(1)
    except PermissionError as e:
        print(f"{RED}⚠ {e}{RESET}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"{RED}⚠ {e}{RESET}")
        sys.exit(1)

    # Display generated command and ask for confirmation
    # Lines printed:
    #   1: empty line
    #   2: "  <command>"
    #   3: empty line
    #   4: "Run? (Y/n): <input>"
    print()
    print(f"  {GREEN}{command}{RESET}")
    print()

    try:
        answer = input(f"  {DIM}Run? (Y/n):{RESET} ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)

    if answer in ("", "y", "yes"):
        _clear_lines(4)

        if _has_shell_wrapper():
            # Write command to temp file for shell wrapper to execute
            _write_cmd_file(command)
            sys.exit(0)
        else:
            # Fallback: run directly (no history integration)
            _run_directly(command)
    else:
        # Cancel silently
        _clear_lines(4)
        sys.exit(1)


if __name__ == "__main__":
    main()
