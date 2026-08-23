import sys
sys.path.insert(0, '/home/adhyansh/Projects/SWARA')
from agent_dir.tools.firecrawl_tools import get_client

client = get_client()
res = client.batch_scrape_urls(urls=['https://en.wikipedia.org/wiki/Elon_Musk'], formats=['markdown'])
d = res.model_dump()
print(d.keys())
