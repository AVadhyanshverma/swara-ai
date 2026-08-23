import asyncio
import httpx
import json

async def main():
    headers = {
        "Authorization": "Bearer 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",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-ai/deepseek-v4-flash-0731",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 50
    }
    async with httpx.AsyncClient(base_url="https://integrate.api.nvidia.com", timeout=30.0) as client:
        try:
            resp = await client.post("/v1/chat/completions", json=payload, headers=headers)
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text}")
            resp.raise_for_status()
            data = resp.json()
            print(data["choices"][0]["message"]["content"])
        except Exception as e:
            print(f"Error type: {type(e)}")
            print(f"Error string: '{str(e)}'")

asyncio.run(main())
