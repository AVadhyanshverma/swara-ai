import os
import subprocess
from langchain_core.tools import tool

# Path to the PyX binary inside the workspace tools folder
PYX_BIN = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "tools", "PyX-Builder", "pyx_linux"
))

@tool
def execute_python_with_pyx(code: str) -> str:
    """Executes arbitrary Python code safely using the PyX portable executable."""
    if not os.path.exists(PYX_BIN):
        return f"Execution error: PyX binary not found at {PYX_BIN}. Did you build it?"
        
    temp_file = os.path.join(os.path.dirname(__file__), "temp_pyx.py")
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(code)
    try:
        result = subprocess.run([PYX_BIN, temp_file], capture_output=True, text=True, timeout=15)
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except Exception as e:
        return f"Execution error: {str(e)}"
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
