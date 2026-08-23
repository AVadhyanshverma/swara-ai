import os
import shutil
import time
from langchain_core.tools import tool
from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel, Field

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from path_manager import get_agent_workspace, ensure_session_paths

def get_session_dir(config: RunnableConfig = None):
    session_id = None
    if config and "configurable" in config:
        session_id = config["configurable"].get("thread_id")
    
    if not session_id:
        session_id = time.strftime("%Y%m%d_%H%M%S")
    
    ensure_session_paths(session_id)
    return str(get_agent_workspace(session_id))

def _resolve_path(relative_path: str, config: RunnableConfig = None) -> str:
    base = get_session_dir(config)
    target = os.path.abspath(os.path.join(base, relative_path))
    if not target.startswith(base):
        raise ValueError("Access denied: Path is outside the agent workspace.")
    return target

class CreateFileInput(BaseModel):
    filepath: str = Field(..., description="Relative path (e.g. 'script.py').")
    content: str = Field(..., description="Content to write to the file.")

@tool("create_file", args_schema=CreateFileInput)
def create_file(filepath: str, content: str, config: RunnableConfig) -> str:
    """Creates a new file with the given content in the agent's workspace."""
    try:
        target = _resolve_path(filepath, config)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File created successfully at: {target}"
    except Exception as e:
        return f"Error creating file: {str(e)}"

class ListDirInput(BaseModel):
    directory: str = Field(default="", description="Relative directory path to list. Leave empty for root.")

@tool("list_directory", args_schema=ListDirInput)
def list_directory(directory: str, config: RunnableConfig) -> str:
    """Lists all files and folders in a specified directory within the agent's workspace."""
    try:
        target = _resolve_path(directory, config)
        if not os.path.exists(target):
            return f"Directory not found: {target}"
        if not os.path.isdir(target):
            return f"Not a directory: {target}"
            
        items = os.listdir(target)
        if not items:
            return "Directory is empty."
            
        result = []
        for item in items:
            full_path = os.path.join(target, item)
            item_type = "DIR" if os.path.isdir(full_path) else "FILE"
            result.append(f"[{item_type}] {item}")
        return "\n".join(result)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

class DeleteFileInput(BaseModel):
    filepath: str = Field(..., description="Relative path of the file to delete.")

@tool("delete_file", args_schema=DeleteFileInput)
def delete_file(filepath: str, config: RunnableConfig) -> str:
    """Deletes a file from the agent's workspace."""
    try:
        target = _resolve_path(filepath, config)
        if not os.path.exists(target):
            return "File not found."
        if os.path.isdir(target):
            shutil.rmtree(target)
            return f"Directory deleted: {target}"
        else:
            os.remove(target)
            return f"File deleted: {target}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"
