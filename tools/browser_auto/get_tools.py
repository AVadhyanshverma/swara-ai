import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient


async def get_tool_descriptions():
    client = MultiServerMCPClient({
        "playwright": {"url": "http://localhost:8931/sse", "transport": "sse"}
    })
    
    tools = await client.get_tools()
    print(f"🔧 Found {len(tools)} tools\n")
    
    for t in tools:
        print(f"Tool: {t.name}")
        print(f"Description: {t.description[:300]}...")
        print(f"Args: {t.args}")
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(get_tool_descriptions())