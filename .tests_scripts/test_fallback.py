import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        resp = await client.post("http://127.0.0.1:8000/analyze", data={"text": "Summarize this: 'Binod is cool.'"}, timeout=60.0)
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text}")

asyncio.run(main())
