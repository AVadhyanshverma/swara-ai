# Firecrawl Search Tools Skill

## Tools
- `search_the_net(query: str, limit: int)`
- `batch_read_pages(urls: list[str])`
- `read_the_page(url: str)`

## Usage Instructions
These tools use the Firecrawl API to search the web and scrape pages into clean Markdown. The text is automatically processed, deduplicated, and summarized by an LLM (Llama 3.1 8B) to extract key facts before being returned to you.

1. **`search_the_net`**: Use this to run a Google search. It returns the top `limit` results (up to 10), complete with URLs, titles, and summarized content.
2. **`batch_read_pages`**: Pass a list of URLs. It will concurrently scrape and summarize all the pages.
3. **`read_the_page`**: Pass a single URL to read its content natively without the LLM summarization. 

*Tip: For deep research, always use `search_the_net` first to gather links, then `batch_read_pages` to dive deeper into the best sources.*
