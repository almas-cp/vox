"""LLM API client for Vox — prompt building, API calls, response cleaning."""

import os
import platform
import re
import requests

API_URL = "https://inference.do-ai.run/v1/chat/completions"
MODEL = "llama3.3-70b-instruct"


def _get_context() -> dict:
    """Gather system context: OS, shell, current working directory."""
    return {
        "os": platform.system() + " " + platform.release(),
        "shell": os.environ.get("SHELL", os.environ.get("COMSPEC", "unknown")),
        "cwd": os.getcwd(),
    }


def _build_system_prompt(ctx: dict) -> str:
    """Build the system prompt with injected context."""
    return (
        f"You are a shell command generator for {ctx['os']} running {ctx['shell']}.\n"
        f"The user's current directory is: {ctx['cwd']}\n"
        "Output ONLY the exact shell command. No explanations, no markdown, no code blocks.\n"
        "If multiple commands are needed, chain them with && or ;."
    )


def _clean_response(text: str) -> str:
    """Strip markdown code blocks, backticks, and extra whitespace from LLM response."""
    # Remove ```lang ... ``` blocks
    text = re.sub(r"```[\w]*\n?", "", text)
    # Remove inline backticks
    text = text.strip("`").strip()
    return text


def generate_command(query: str, api_key: str) -> str:
    """Send a natural language query to the LLM and return the generated shell command.

    Raises:
        ConnectionError: API is unreachable.
        PermissionError: Invalid API key.
        RuntimeError: Empty or unexpected response.
    """
    ctx = _get_context()
    system_prompt = _build_system_prompt(ctx)

    try:
        response = requests.post(
            API_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                "max_tokens": 400,
            },
            timeout=30,
        )
    except requests.ConnectionError:
        raise ConnectionError("Cannot reach the API. Check your internet connection.")
    except requests.Timeout:
        raise ConnectionError("API request timed out. Try again.")

    if response.status_code == 401:
        # 401 can mean invalid key OR model not available on subscription tier
        try:
            err_msg = response.json().get("error", {}).get("message", "")
        except Exception:
            err_msg = ""
        if "model" in err_msg.lower() and "tier" in err_msg.lower():
            raise PermissionError(f"Model '{MODEL}' is not available on your subscription tier.")
        raise PermissionError("Invalid API key. Run `vox --setup` to reconfigure.")
    if response.status_code == 429:
        raise RuntimeError("Rate limited. Please wait a moment and try again.")
    if response.status_code != 200:
        raise RuntimeError(f"API returned HTTP {response.status_code}.")

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("Unexpected response format from API.")

    command = _clean_response(content)
    if not command:
        raise RuntimeError("Empty response from API. Try rephrasing your request.")

    return command
