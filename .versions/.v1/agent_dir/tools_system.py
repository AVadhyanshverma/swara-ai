import os
import sys
import json
import asyncio
import subprocess
import importlib.util
from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

# Path to the user's tools directory (now inside agent_dir)
TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "tools"))

# ==========================================
# DYNAMIC LOADER FOR NATIVE @TOOL DECORATED SCRIPTS
# ==========================================
def load_all_tools():
    """
    Dynamically loads all LangChain tools (instances of BaseTool) from the 
    python files in the workspace tools/ directory.
    """
    loaded_tools = []
    root_dir = os.path.abspath(os.path.join(TOOLS_DIR, ".."))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
        
    for root, dirs, files in os.walk(TOOLS_DIR):
        for file in files:
            if file.endswith(".py") and not file.startswith("test_"):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, root_dir)
                module_name = "dynamic_tools_" + rel_path.replace(os.path.sep, "_").replace(".py", "")
                
                try:
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[module_name] = module
                        spec.loader.exec_module(module)
                        
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if isinstance(attr, BaseTool):
                                if not any(t.name == attr.name for t in loaded_tools):
                                    loaded_tools.append(attr)
                except Exception as e:
                    pass
    return loaded_tools

# Export all tools
available_tools = load_all_tools()
