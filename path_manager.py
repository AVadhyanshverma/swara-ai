import os
import platform
from pathlib import Path

# Set to True for development mode (local project paths)
# Set to False for production mode (user home directory paths)
DEV = False

def get_base_dir() -> Path:
    """Returns the base directory for the application."""
    if DEV:
        # In DEV mode, use the current project directory (where this file is located)
        return Path(__file__).resolve().parent
    else:
        # In PROD mode, use the user's home directory + .SWARA_hackathon
        # Path.home() automatically detects OS and gives C:\Users\<User> on Windows 
        # and /home/<User> on Linux.
        return Path.home() / ".SWARA_hackathon"

def get_agent_workspace(session_id: str) -> Path:
    """Returns the workspace directory for a specific chat session."""
    return get_base_dir() / "agent_workplace" / str(session_id)

def get_playwright_mcp_dir(session_id: str) -> Path:
    """Returns the Playwright MCP directory for a specific chat session."""
    return get_agent_workspace(session_id) / "playwright_mcp"

def get_mindmaps_dir(session_id: str) -> Path:
    """Returns the mind maps directory for a specific chat session."""
    return get_agent_workspace(session_id) / "generate_mindmaps"

def get_chats_dir() -> Path:
    """Returns the directory where chat history is stored."""
    return get_base_dir() / "chats"

def get_brain_dir() -> Path:
    """Returns the directory where the vector database (brain) is stored."""
    return get_base_dir() / "brain"

def ensure_session_paths(session_id: str):
    """Utility to ensure all necessary directories exist for a given session."""
    dirs = [
        get_agent_workspace(session_id),
        get_playwright_mcp_dir(session_id),
        get_mindmaps_dir(session_id),
        get_chats_dir(),
        get_brain_dir()
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
