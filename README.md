# Swara AI

Swara AI is an advanced AI agent framework and chat interface designed to provide a highly interactive and intelligent experience. It features both a terminal CLI and a web-based UI powered by FastAPI.

## Features

- **Agent Framework**: Built to support complex reasoning, memory, and specialized tool-use.
- **Web UI**: A FastAPI-based interactive user interface for seamless chat and exploration.
- **Terminal CLI**: A lightweight and stream-capable command line interface (`chat_cli.py`).
- **Cross-Platform**: Built to be packaged for both Windows and Linux (Kali) using PyInstaller.
- **GitHub Actions**: Automated CI/CD pipelines to build standalone executables on every push.

## Setup

1. Create a virtual environment: `python -m venv .venv`
2. Activate the environment: `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows)
3. Install requirements (if provided).
4. Run the application:
   - For Terminal CLI: `python chat_cli.py`
   - For UI Server: `python main.py` or `python ui/main.py`

## Build from Source

You can build the executable yourself using PyInstaller:
```bash
pyinstaller build.spec
```
This will generate the standalone executable in the `dist/` directory.

## Automated Builds

This repository is configured with GitHub Actions to automatically build standalone binaries for Windows and Linux. Check the [Actions](../../actions) tab on GitHub to download the latest artifacts.
