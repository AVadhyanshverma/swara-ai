import os
import json
import asyncio
import subprocess
import time
import urllib.request
import urllib.error
from langchain_core.tools import tool

import threading

# Path to the Playwright MCP executable
PLAYWRIGHT_MCP = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "tools", "browser_auto", "dist", "playwright-mcp.run"
))
BROWSER_CLI = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "tools", "browser_auto", "browser_cli.py"
))

# Global reference to the server process if we start it
_SERVER_PROC = None
_CLI_PROC = None
_CLI_LOCK = threading.Lock()

def ensure_server_running():
    global _SERVER_PROC
    # Check if port 8931 is responding
    try:
        urllib.request.urlopen("http://localhost:8931/sse", timeout=1)
        return True
    except urllib.error.URLError as e:
        if isinstance(e.reason, ConnectionRefusedError):
            pass
        else:
            return True
    except Exception:
        pass

    if not os.path.exists(PLAYWRIGHT_MCP):
        raise FileNotFoundError(f"Playwright MCP not found at {PLAYWRIGHT_MCP}. Please build it first.")
    
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from path_manager import get_playwright_mcp_dir, ensure_session_paths
    
    # We will use a default session for the global server, or a passed one if available
    session_id = time.strftime("%Y%m%d_%H%M%S") # In a real implementation this might come from context
    ensure_session_paths(session_id)
    playwright_dir = str(get_playwright_mcp_dir(session_id))
    
    print("Starting Playwright MCP Server on port 8931...", flush=True)
    _SERVER_PROC = subprocess.Popen(
        [PLAYWRIGHT_MCP, "--port", "8931", "--browser", "chromium", "--shared-browser-context", "--viewport-size", "1920x1080"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=playwright_dir
    )
    
    for _ in range(15):
        try:
            urllib.request.urlopen("http://localhost:8931/sse", timeout=1)
            return True
        except Exception:
            time.sleep(1)
            
    raise RuntimeError("Failed to start Playwright MCP Server on port 8931.")

def get_cli_process():
    global _CLI_PROC
    if _CLI_PROC is not None and _CLI_PROC.poll() is None:
        return _CLI_PROC
    
    ensure_server_running()
    
    import sys
    # Start the CLI wrapper
    _CLI_PROC = subprocess.Popen(
        [sys.executable, BROWSER_CLI],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Wait for "Connected!"
    for line in _CLI_PROC.stdout:
        if "Connected!" in line:
            break
            
    return _CLI_PROC

def execute_cli_command(command: str) -> str:
    with _CLI_LOCK:
        proc = get_cli_process()
        proc.stdin.write(command + "\n")
        proc.stdin.flush()
        
        output = []
        for line in proc.stdout:
            stripped = line.strip()
            if stripped == "---COMMAND_COMPLETE---":
                break
            output.append(stripped)
            
        return "\n".join(output)

@tool
def execute_browser_tool(tool_name: str, args_json: str) -> str:
    """Executes a browser automation tool on the Playwright MCP server.
    Available tools: browser_navigate, browser_snapshot, browser_click, browser_fill_form, etc.
    """
    try:
        # Validate JSON and re-encode to a single line without newlines
        parsed = json.loads(args_json)
        single_line_json = json.dumps(parsed)
        
        # Execute via persistent CLI wrapper
        cmd = f"{tool_name} {single_line_json}"
        return execute_cli_command(cmd)
    except Exception as e:
        return f"Error executing browser tool: {str(e)}"

@tool
def list_browser_tools() -> str:
    """Lists available browser automation tools and their required JSON schemas."""
    # We can fetch tools natively here or via a special command, but since it's just info,
    # doing it ad-hoc is fine, but wait, browser_cli.py doesn't have a list command built-in.
    # Let's just do a quick ad-hoc connection for listing tools, since it doesn't affect browser state.
    try:
        ensure_server_running()
        from mcp import ClientSession
        from mcp.client.sse import sse_client
        
        async def call_mcp():
            async with sse_client("http://localhost:8931/sse") as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    out = []
                    for t in tools.tools:
                        out.append(f"Tool: {t.name}\nDescription: {t.description}\nSchema: {json.dumps(t.inputSchema)}")
                    return "\n\n".join(out)
        return asyncio.run(call_mcp())
    except Exception as e:
        return f"Error listing browser tools: {str(e)}"
