import sys
sys.path.insert(0, '/home/adhyansh/Projects/SWARA')
from firecrawl import Firecrawl
from firecrawl.v2.types import ScrapeOptions

app = Firecrawl(api_key="fc-622a00f04c77417589271736496ce31c")

# Create a dummy PDF
import fitz
doc = fitz.open()
page = doc.new_page()
page.insert_text((50, 50), "Hello world from test document.")
doc.save("test_dummy.pdf")
doc.close()

try:
    doc = app.parse(
        "./test_dummy.pdf",
        options=ScrapeOptions(
            only_main_content=True,
            formats=["markdown"],
        ),
    )
    print("Markdown extracted:")
    print(doc.markdown)
except Exception as e:
    print(f"Error: {e}")
