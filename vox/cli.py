"""CLI handler for Vox — argument parsing, command execution, UX flow."""

import os
import subprocess
import sys
import time

from vox import __version__
from vox.config import get_api_key, run_setup, reset_config
from vox.llm_client import generate_command

# ANSI escape codes
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
DIM = "\033[2m"
RESET = "\033[0m"

# Terminal control
CURSOR_UP = "\033[A"
CLEAR_LINE = "\033[2K"


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
""")


def _add_to_shell_history(command: str):
    """Append the command to the shell's history file so up-arrow retrieves it."""
    try:
        shell = os.environ.get("SHELL", "")
        home = os.path.expanduser("~")

        if "zsh" in shell:
            history_file = os.path.join(home, ".zsh_history")
            # zsh extended history format: : timestamp:0;command
            entry = f": {int(time.time())}:0;{command}\n"
        else:
            # bash or other
            history_file = os.path.join(home, ".bash_history")
            entry = f"{command}\n"

        with open(history_file, "a") as f:
            f.write(entry)
    except (IOError, OSError):
        pass  # non-critical, don't break the flow


def _run_command(command: str):
    """Execute a shell command and stream output to the terminal."""
    _add_to_shell_history(command)
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=None,  # inherit current directory
        )
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print()
        sys.exit(130)


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
        # Clear the 4 vox UI lines so only command output remains
        _clear_lines(4)
        _run_command(command)
    else:
        # Cancel silently
        _clear_lines(4)


if __name__ == "__main__":
    main()
