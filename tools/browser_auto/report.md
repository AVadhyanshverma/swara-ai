# Playwright MCP Browser Automation: Complete Setup & Usage Guide

This guide explains how to build, configure, and use the Playwright MCP (Model Context Protocol) server for reliable AI-driven browser automation. It covers both native AI agent integration and a Python-based interactive CLI tool.

## 1. Building the Portable MCP Server

You can package the Microsoft Playwright MCP into a portable, single-file Linux executable (`playwright-mcp.run`) using a custom build script. This eliminates dependency issues and makes it easy to distribute.

Create and run `build.sh`:

```bash
#!/bin/bash
set -e
echo "🔧 Building self-extracting Playwright MCP..."
rm -rf build dist
mkdir -p dist

git clone --depth 1 https://github.com/microsoft/playwright-mcp.git build
cd build && npm install && cd ..

mkdir -p dist/playwright-mcp
cp -r build/{package.json,cli.js,index.js,src,node_modules} dist/playwright-mcp/

wget -q -O dist/node.tar.xz https://nodejs.org/dist/v20.11.1/node-v20.11.1-linux-x64.tar.xz
tar -xf dist/node.tar.xz -C dist/
mv dist/node-v20.11.1-linux-x64/bin/node dist/playwright-mcp/node
rm -rf dist/node.tar.xz dist/node-v20.11.1-linux-x64

cat > dist/playwright-mcp.run << 'SCRIPT'
#!/bin/bash
set -e
TMPDIR=$(mktemp -d /tmp/playwright-mcp-XXXXXX)
START=$(awk '/^__ARCHIVE_BELOW__/ {print NR + 1; exit 0;}' "$0")
tail -n +$START "$0" | tar -xJ -C "$TMPDIR"
"$TMPDIR/playwright-mcp/node" "$TMPDIR/playwright-mcp/cli.js" "$@"
rm -rf "$TMPDIR"
exit 0
__ARCHIVE_BELOW__
SCRIPT

tar -cJf - -C dist playwright-mcp >> dist/playwright-mcp.run
chmod +x dist/playwright-mcp.run
echo "✅ Build Complete: ./dist/playwright-mcp.run"
```

> [!IMPORTANT]
> Before running it for the first time, you must install Chromium:
> `./dist/playwright-mcp/node ./dist/playwright-mcp/node_modules/playwright-core/cli.js install chromium`

---

## 2. Launching the Server (Headed Mode)

To allow the browser to pop up visibly on your screen (headed mode) and prevent "cropped" or "zoomed" layouts, launch the server with a specific viewport size and omit the `--headless` flag.

```bash
# Start the persistent SSE server on port 8931
./dist/playwright-mcp.run \
  --port 8931 \
  --browser chromium \
  --shared-browser-context \
  --viewport-size 1920x1080 \
  --output-dir ./output_screens
```

> [!TIP]
> Add `--user-agent "Mozilla/5.0..."` if you need to bypass strict bot protections like Cloudflare. 
> The `--shared-browser-context` flag ensures that multiple API calls maintain the same browser tab, session, and cookies.

---

## 3. Interactive Python CLI Wrapper

To control the browser dynamically (either as a human or an AI agent), use this stateful Python CLI wrapper. It reads commands via standard input, executes them on the running Playwright SSE server, and prints the output.

**`browser_cli.py`**:
```python
#!/usr/bin/env python3
import sys, json, asyncio, base64
from mcp import ClientSession
from mcp.client.sse import sse_client

async def main():
    print("Connecting to Playwright MCP...", flush=True)
    try:
        async with sse_client("http://localhost:8931/sse") as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("Connected! Enter commands in format: <tool_name> <args_json>", flush=True)
                
                loop = asyncio.get_running_loop()
                while True:
                    line = await loop.run_in_executor(None, sys.stdin.readline)
                    if not line: break
                    
                    parts = line.strip().split(" ", 1)
                    if not parts or not parts[0]: continue
                    tool_name, args_json = parts[0], parts[1] if len(parts) > 1 else "{}"
                    
                    try:
                        args = json.loads(args_json)
                        result = await session.call_tool(tool_name, args)
                        if result.isError:
                            print("ERROR:", result.content, flush=True)
                        else:
                            for content in result.content:
                                if content.type == 'text':
                                    print(content.text, flush=True)
                                elif content.type == 'image':
                                    print("Received Image Data (Base64)", flush=True)
                    except Exception as e:
                        print(f"Tool call failed: {e}", flush=True)
                    
                    print("---COMMAND_COMPLETE---", flush=True)
    except Exception as e:
        print("EXCEPTION:", e, flush=True)

if __name__ == "__main__":
    asyncio.run(main())
```

### Usage Example
Run `python browser_cli.py`, then feed it JSON commands:
```text
browser_navigate {"url": "https://huggingface.co/login"}
browser_fill_form {"fields":[{"target":"e171","name":"Username","type":"textbox","value":"test@email.com"}]}
browser_take_screenshot {}
```

---

## 4. Native AI Agent Integration (Tool Schema)

If you want an AI agent to use the browser tools natively, you can expose the Playwright MCP server directly using an `mcp_config.json` file. 

Place this in `~/.gemini/config/mcp_config.json` or `.agents/plugins/browser/mcp_config.json`:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "/path/to/dist/playwright-mcp.run",
      "args": [
        "--browser", 
        "chromium",
        "--viewport-size", 
        "1920x1080"
      ]
    }
  }
}
```
*(Note: Using standard I/O ("command") is highly recommended for native agent workflows over SSE, as it manages the lifecycle automatically without network bridging.)*

### Core Tool Schemas for Agents
When correctly integrated, the agent automatically receives 24 tools. Here are the schemas for the most critical ones:

**1. `browser_navigate`**
*   **Description:** Navigate to a specific URL.
*   **Arguments:** `{"url": "string"}`

**2. `browser_snapshot`**
*   **Description:** Retrieve the accessibility tree (DOM) of the current page. **Critical:** Always run this before attempting to click or type, to retrieve the current `ref` IDs (e.g., `e15`).
*   **Arguments:** `{}`

**3. `browser_fill_form`**
*   **Description:** Atomically fill multiple form fields. Far more reliable than sequential typing.
*   **Arguments:** 
    ```json
    {
      "fields": [
        {"target": "e171", "name": "Username", "type": "textbox", "value": "my_user"}
      ]
    }
    ```

**4. `browser_click`**
*   **Description:** Click on an element based on its `ref` ID from the snapshot.
*   **Arguments:** `{"target": "e12", "element": "Human description"}`

## 5. The Golden Workflow

AI agents must strictly follow the **Observe → Act → Verify** pattern:
1. **Observe:** Call `browser_navigate` or `browser_wait_for`, then IMMEDIATELY call `browser_snapshot` to read the DOM tree and locate `ref` target IDs.
2. **Act:** Use `browser_click` or `browser_fill_form` on the identified target IDs. *Never hallucinate or guess a ref ID.*
3. **Verify:** Call `browser_snapshot` or `browser_take_screenshot` to confirm the state changed successfully before moving to the next step.