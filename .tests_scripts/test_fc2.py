import inspect
from firecrawl import FirecrawlApp
app = FirecrawlApp(api_key="fc-622a00f04c77417589271736496ce31c")
print(inspect.signature(app.parse))
