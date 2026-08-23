#!/usr/bin/env python3
import sys
import json
import asyncio
import base64
import os
from mcp import ClientSession
from mcp.client.sse import sse_client

async def main():
    print("Connecting to Playwright MCP...", flush=True)
    try:
        async with sse_client("http://localhost:8931/sse") as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("Connected! Enter commands in format: <tool_name> <args_json>", flush=True)
                
                # We will read from stdin asynchronously
                loop = asyncio.get_running_loop()
                while True:
                    line = await loop.run_in_executor(None, sys.stdin.readline)
                    if not line:
                        break # EOF
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split(" ", 1)
                    tool_name = parts[0]
                    args_json = parts[1] if len(parts) > 1 else "{}"
                    
                    try:
                        args = json.loads(args_json)
                        
                        try:
                            result = await session.call_tool(tool_name, args)
                            if result.isError:
                                print("ERROR:", result.content, flush=True)
                            else:
                                for content in result.content:
                                    if content.type == 'text':
                                        print(content.text, flush=True)
                                    elif content.type == 'image':
                                        print("Received Image Data (Base64)", flush=True)
                                    else:
                                        print(content, flush=True)
                        except Exception as call_e:
                            print("Tool call failed:", call_e, flush=True)
                            
                    except json.JSONDecodeError:
                        print("Error: Invalid JSON arguments.", flush=True)
                    
                    print("---COMMAND_COMPLETE---", flush=True)
                    
    except Exception as e:
        print("EXCEPTION:", e, flush=True)

if __name__ == "__main__":
    asyncio.run(main())
