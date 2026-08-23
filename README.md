# Swara AI - Advanced Agentic Workflow Framework

![Swara AI Banner](ui/static/img/bg.jpeg)

## Overview
Swara AI is an advanced, autonomous AI agent framework designed to bridge the gap between Large Language Models (LLMs) and local machine execution. Built with **FastAPI**, **LangGraph concepts**, and a highly modular tool ecosystem, Swara AI acts as a sophisticated digital assistant capable of reading files, writing code, executing scripts, solving math, creating interactive mindmaps, and managing its own memory securely.

Whether you prefer a lightweight **Terminal CLI** or a rich, interactive **Web UI**, Swara AI provides a seamless, cross-platform experience. It is fully packaged for standalone distribution using PyInstaller and automated via GitHub Actions.

## Key Features

### 🧠 Autonomous Agent Engine
- **Tool-Augmented Generation**: The core LLM is augmented with a suite of dynamic tools located in the `tools/` directory. It can autonomously decide when to use a tool, parse the output, and iteratively solve problems.
- **Dynamic Context Management**: Implements sophisticated token management to ensure the LLM doesn't hallucinate or exceed context windows when processing large codebases or datasets.

### 💻 Dual Interfaces
- **Web UI (`ui/main.py`)**: A modern, dark-themed FastAPI web interface. It features real-time token streaming, markdown rendering, syntax highlighting, and dynamic rendering of mindmaps/charts.
- **Terminal CLI (`chat_cli.py`)**: A fast, stream-capable command-line interface for developers who prefer living in the terminal.

### 🔒 Secure & Persistent Memory
- **SQLCipher Integration**: All chat histories and agent memories are stored locally in `reverie_chats.db` and encrypted using SQLCipher. Your data never leaves your machine unless explicitly sent to the LLM provider.
- **Vector Database**: Swara AI utilizes a custom vector storage engine (`memory/vector_db/`) for semantic search, allowing it to recall long-term context from past conversations and project files.

### 🛠️ Extensive Tool Ecosystem
- **PyX-Builder & Execution (`pyx_executor.py`)**: Safe execution of generated Python code in an isolated environment.
- **Browser Automation**: Integrates Playwright via a Model Context Protocol (MCP) server for deep web scraping and automated browser testing.
- **Interactive Visualizations**: Autonomously generates interactive HTML mindmaps and architectures (`interactive_gui_or_mindsmaps_and_charts/`).
- **Mathematical Solver**: A dedicated multi-step arithmetic solver for precise computational tasks.

### 🚀 CI/CD & Cross-Platform Builds
- **GitHub Actions**: Fully automated release pipelines for both Windows and Linux.
- **Standalone Executables**: Built with PyInstaller, meaning users do not need Python installed to run Swara AI. Just download the artifact and run.

---

## Repository Architecture

```text
Reverie/
├── agent_dir/               # Core LLM orchestration and LangGraph state management
├── tools/                   # Modular tools for the AI (Memory, Web, Math, Execution)
│   ├── browser_auto/        # Playwright MCP server for web automation
│   ├── chat_his/            # Encrypted chat history and SQLCipher logic
│   ├── memory/              # Vector database and semantic search engine
│   ├── PyX-Builder/         # Secure execution environment builder
│   └── interactive_gui_.../ # HTML/JS generators for mindmaps
├── ui/                      # FastAPI Web Server and Static Assets
│   ├── static/              # CSS, JS, Manifest, Images
│   ├── index.html           # Main chat interface
│   └── main.py              # FastAPI application entry point
├── chat_cli.py              # Terminal interface entry point
├── build.spec               # PyInstaller configuration file
└── .github/workflows/       # CI/CD Pipelines for automated releases
```

## Installation & Setup (For Developers)

### Prerequisites
- Python 3.10+
- `git`

### 1. Clone the Repository
```bash
git clone https://github.com/AVadhyanshverma/swara-ai.git
cd swara-ai
```

### 2. Set Up Virtual Environment
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On Linux/Mac
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
# Ensure you have uvicorn, fastapi, langchain, pyinstaller, etc.
```

### 4. Run the Application
**For the Web UI:**
```bash
python ui/main.py
# The server will start at http://localhost:8000
```
**For the Terminal CLI:**
```bash
python chat_cli.py
```

## Automated Releases via GitHub Actions

Swara AI uses GitHub Actions to automatically build and publish release binaries whenever a new tag is pushed.

### How to trigger a release:
1. Ensure your code is pushed to `main`.
2. Create and push a new Git tag (e.g., `v1.0.0`):
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. The `.github/workflows/release.yml` action will trigger, build the Windows and Linux executables, and automatically create a GitHub Release with the binaries attached.

## Contribution Guidelines
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## License
Distributed under the MIT License. See `LICENSE` for more information.
