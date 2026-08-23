import sys
sys.path.insert(0, '/home/adhyansh/Projects/SWARA')
from agent_dir.tools.firecrawl_tools import get_client

client = get_client()
res = client.search(query="Apple", limit=1)
d = res.model_dump()
print(f"Data length: {len(d.get('data', []))}")
