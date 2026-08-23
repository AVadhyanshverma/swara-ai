# Reverie AI Agent: Current Architecture & Capabilities

This document provides a comprehensive overview of the Reverie AI Agent architecture, its module structure, storage mechanisms, and the specialized tools it currently possesses.

## 🧠 Core Architecture
The brain of the agent is built upon **LangGraph** combined with `ChatOpenAI` models. It utilizes a state graph to manage multi-turn conversations, tool invocations, and memory persistence. 
- **Main Engine:** `agent_dir/agent.py` orchestrates the flow of messages and tool calls.
- **Interfaces:** Users can interact via a CLI (`chat_cli.py`) or a dedicated UI (`ui/main.py`).

## 📁 Environment & Path Management
A centralized `path_manager.py` elegantly handles the difference between Development and Production environments:
- **Development Mode (`DEV = True`)**: Stores all data (workspaces, memory, chats) locally in the project root.
- **Production Mode (`DEV = False`)**: Automatically detects the OS (Linux vs. Windows) and utilizes standard user home directories (e.g., `~/.reverie_hackathon/` or `C:\Users\<User>\.reverie_hackathon\`).

## 🔒 Storage & Memory Subsystems

### 1. Encrypted Chat Engine (`tools/chat_his/encrypted_chat_engine.py`)
- **Ultra-Fast & Secure:** Uses SQLite with SQLCipher to store chat histories.
- **Hardware-locked Encryption:** Generates a deterministic, device-specific 256-bit encryption key utilizing CPU, MAC address, and motherboard UUIDs.
- **High-Performance JSON Search:** Leverages SQLite JSON expression indexes for lightning-fast keyword searches across complex message objects.

### 2. Long-Term Vector Memory (`tools/memory/`)
- A centralized Vector Database (Brain) stores agent contexts, file contents, and conversation summaries.
- It is equipped with dynamic summarization rules to prune context windows and inject long-term insights seamlessly into active prompts.

## 🛠️ Specialized Tool Arsenal

### Web & Document Processing
- **Firecrawl Tools (`firecrawl_tools.py`)**: Advanced web scraping, recursive crawling, search, and LLM-driven structured data extraction.
- **Document Tools (`document_tools.py`)**: Can ingest PDFs, Word documents, images, and videos. It routes standard documents to Firecrawl and media to a local multimodal vision proxy model.

### Advanced Browser Automation (MCP)
- **Playwright MCP (`browser_tools.py`)**: The agent commands an isolated, headless Chromium browser instance via a Model Context Protocol (MCP) Server using Server-Sent Events (SSE). It handles navigation, clicking, form-filling, and snapshotting.

### Filesystem & Execution
- **File Tools (`file_tools.py`)**: Safe, workspace-scoped file creation, listing, and deletion tools that prevent directory traversal attacks.
- **PyX Executor (`pyx_executor.py` / `PyX-Builder`)**: Allows the agent to run generated Python code safely inside portable, bundled execution environments (both Linux and Windows support).

### Logic & Visualization
- **Math Arithmetic & Grading (`solve maths arithmetic`)**: Step-by-step arithmetic calculators that can solve complex problems chronologically or act as a "grader" to verify a student's working.
- **Mindmap Generator (`mindmap_tool.py`)**: An interactive GUI tool that allows the agent to take Markdown representations of complex ideas and render them into portable, standalone HTML mindmap files.

---
**Status:** The system is highly modular, deeply integrated with advanced tooling, securely architected, and ready for multi-modal, agentic workloads.
