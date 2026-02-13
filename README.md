# Vox

Natural language to shell commands. Type what you want in plain English, get the exact command.

Powered by [Groq](https://groq.com) for blazing-fast inference. Also supports [DigitalOcean Gradient](https://www.digitalocean.com/products/ai).

```
$ vox find all python files modified today

  find . -name "*.py" -mtime 0

  Run? (Y/n): y

./script.py
./utils/helpers.py
```

## Install

```bash
git clone https://github.com/almas-cp/vox.git
cd vox
chmod +x install.sh
./install.sh
```

This installs `vox` system-wide so it **persists across reboots**. To uninstall:

```bash
./uninstall.sh
```

## Setup

On first run, you'll be prompted to pick a provider, enter your API key, and choose a model:

```bash
vox --setup
```

Get a free Groq API key at [console.groq.com/keys](https://console.groq.com/keys).

Your config is stored in `~/.vox/config.json`.

## Usage

```bash
vox list all files in this directory
vox show disk usage sorted by size
vox compress this folder into a tar.gz
vox find files larger than 100mb
vox kill the process running on port 3000
```

Vox detects your OS, shell, and current directory to generate the right command. It shows you the command first — you confirm before it runs.

## Supported Providers

| Provider | Models | Speed |
|---|---|---|
| **Groq** (default) | Llama 3.3 70B, GPT-OSS 120B, Qwen 3, Llama 4 | ⚡ Ultra-fast |
| DigitalOcean Gradient | Llama, Claude, GPT-4o/5, Mistral | Fast |

## Flags

| Flag | Description |
|---|---|
| `--setup` | Configure provider, API key & model |
| `--reset` | Remove stored configuration |
| `--version` | Show version |
| `--shell-init` | Print shell wrapper (for history integration) |

## How It Works

1. You type a request in natural language
2. Vox detects your OS, shell, and current directory
3. Sends context + request to the LLM API
4. Shows you the generated command
5. On confirmation, executes it — output appears cleanly as if you typed it yourself

## Requirements

- Python 3.8+
- An API key from [Groq](https://console.groq.com/keys) (free) or [DigitalOcean Gradient](https://cloud.digitalocean.com/gradient)

## License

[MIT](LICENSE)
