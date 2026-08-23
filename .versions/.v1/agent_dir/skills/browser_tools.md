# Browser Tools Skill

## Tools
- `execute_browser_tool(tool_name: str, args_json: str)`
- `list_browser_tools()`

## Usage Instructions
Browser tools allow the agent to directly interact with a live Chromium browser session using Playwright. 
You can navigate to URLs, take snapshots, click on elements, and fill forms.

1. **Discover Tools:** Use `list_browser_tools()` to see all the available browser operations (e.g., `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_fill_form`, etc.) and their specific JSON schemas.
2. **Execute Actions:** Use `execute_browser_tool` to interact with the browser. 
   - `tool_name`: The specific action you want to take (e.g., "browser_navigate").
   - `args_json`: A JSON string matching the required schema for that action.

**Example Flow:**
1. Call `list_browser_tools()` to see what's available.
2. Navigate to a page: `execute_browser_tool("browser_navigate", '{"url": "https://example.com"}')`
3. Click an element: `execute_browser_tool("browser_click", '{"selector": "#submit-btn"}')`
