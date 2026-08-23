import os
import subprocess
from langchain_core.tools import tool

MINDMAP_SCRIPT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 
    "..", "..", "tools", "interactive_gui_or_mindsmaps_and_charts", "mindmap_tool.py"
))

from langchain_core.runnables.config import RunnableConfig

@tool
def generate_mindmap(markdown_content: str, config: RunnableConfig, title: str = "AI Generated Mindmap") -> str:
    """
    Generates a beautiful, interactive HTML mindmap from Markdown text and saves it automatically.
    The markdown content should use standard headings (#, ##, ###) or bullet lists (-, *, +) to represent the hierarchy of the mindmap.
    
    Args:
        markdown_content: The markdown structure for the mindmap.
        title: The title of the mindmap.
        
    Returns:
        A string indicating the file path where the mindmap was saved, or an error message.
    """
    try:
        session_id = None
        if config and "configurable" in config:
            session_id = config["configurable"].get("thread_id")
            
        cmd = ["python3", MINDMAP_SCRIPT, "--title", title, "--markdown", markdown_content]
        if session_id:
            cmd.extend(["--session", session_id])
            
        # Run the mindmap_tool.py script via subprocess
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            return f"Mindmap successfully created!\nOutput: {process.stdout}"
        else:
            return f"Error creating mindmap:\nSTDOUT: {process.stdout}\nSTDERR: {process.stderr}"
    except Exception as e:
        return f"Exception occurred while calling mindmap tool: {str(e)}"
