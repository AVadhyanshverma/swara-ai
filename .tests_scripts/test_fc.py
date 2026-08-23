import os
from firecrawl import FirecrawlApp
import sys

app = FirecrawlApp(api_key="fc-622a00f04c77417589271736496ce31c")
# see methods
print([m for m in dir(app) if 'parse' in m.lower()])
