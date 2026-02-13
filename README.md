# Vox

Natural language to shell commands. Type what you want in plain English, get the exact command.

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
pip install -e .
```

## Setup

On first run, you'll be prompted for your [DigitalOcean Gradient](https://www.digitalocean.com/products/ai) API key. Or run manually:

```bash
vox --setup
```

## Usage

```bash
vox list all files in this directory
vox show disk usage sorted by size
vox compress this folder into a tar.gz
vox find files larger than 100mb
vox kill the process running on port 3000
```

Vox detects your OS, shell, and current directory to generate the right command. It shows you the command first — you confirm before it runs.

## Flags

| Flag | Description |
|---|---|
| `--setup` | Configure API key |
| `--reset` | Remove stored configuration |
| `--version` | Show version |

## How It Works

1. You type a request in natural language
2. Vox detects your OS, shell, and current directory
3. Sends context + request to an LLM via [DigitalOcean Gradient](https://www.digitalocean.com/products/ai)
4. Shows you the generated command
5. On confirmation, executes it — output appears cleanly as if you typed it yourself

## Requirements

- Python 3.8+
- A [DigitalOcean Gradient](https://www.digitalocean.com/products/ai) model access key

## License

[MIT](LICENSE)
