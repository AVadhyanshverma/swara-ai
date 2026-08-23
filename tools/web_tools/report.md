# Firecrawl LangGraph Tools: Implementation Report

This document outlines the architecture, decisions, and capabilities of the Firecrawl tools built in `firecrawl_tools.py`. It is designed to serve as a reference for anyone needing to use, modify, or recode these tools for AI agent workflows (like LangChain or LangGraph).

## Overview

The tools are built as LangChain-compatible `@tool` decorators wrapped around direct Python `requests` calls to the **Firecrawl v2 API**. 

**Why direct API calls instead of the official Python SDK?**
By using `requests`, we bypass potential SDK version conflicts, dependency bloat, and get 100% control over the exact JSON payloads sent to the server. This allows us to implement cutting-edge v2 features immediately.

---

## 1. The Tools Built

### `search_the_net`
- **Endpoint:** `POST /v2/search`
- **Purpose:** Conducts web searches and returns metadata and snippets.
- **Key Parameters:** 
  - `query` (str): The search term.
  - `limit` (int): Number of results (defaults to 10).
  - `tbs` (str): Time-based filters (e.g., `qdr:d` for the past day, `qdr:w` for the past week).

### `read_the_page`
- **Endpoint:** `POST /v2/scrape`
- **Purpose:** Scrapes a single webpage synchronously. Designed to be extremely robust for LLM context limits.

### `batch_read_pages`
- **Endpoint:** `POST /v2/batch/scrape`
- **Purpose:** Takes a list of URLs and scrapes them all asynchronously on Firecrawl's servers. 
- **Implementation Detail:** This tool is a "blocking" tool from the Agent's perspective. It submits the batch job and automatically polls `GET /v2/batch/scrape/{id}` every 5 seconds until the job completes or hits a configurable timeout (default 300 seconds).

---

## 2. Advanced Scrape Parameters

Both scraping tools were injected with advanced parameters to give agents surgical precision over the data they extract and to drastically minimize LLM token bloat:

- `wait_for` (int): Waits X milliseconds before taking the HTML snapshot. Crucial for React/Vue Single Page Applications (SPAs).
- `include_tags` (List[str]): Forces the scraper to *only* return content inside specific tags (e.g., `["article"]`).
- `exclude_tags` (List[str]): Strips out noisy tags before processing (e.g., `["nav", "footer"]`).
- `remove_base64_images` (bool): Defaults to `True`. Automatically strips heavy inline Base64 images from the Markdown to save massive amounts of context tokens.

---

## 3. Structural Formats & Image Preservation

The tools use a dynamic `formats` array (defaulting to `["markdown"]`). 

**Image Preservation:** 
If an agent needs to "see" or download images, it can pass `formats=["markdown", "images"]`. Firecrawl will process the images and return a structured array of image URLs and `alt` text.

**Dynamic Return Logic:**
To keep the context window as clean as possible for the LLM:
1. If the agent *only* requests `["markdown"]` (and no extraction schema), the tool returns a flat Markdown string.
2. If the agent requests multiple formats (like `["markdown", "images"]`), the tool intelligently returns the full dictionary so the agent can access `data["images"]`.

---

## 4. LLM JSON Extraction (Bypassing Local Token Limits)

Instead of the local LangGraph agent trying to read a 40,000-word webpage and crashing its context window, we leverage Firecrawl's LLM extraction.

**How it was implemented (v2 syntax):**
In Firecrawl v2, extraction schemas are NOT passed at the root of the JSON body. They are passed inside the `formats` array as a JSON object:
```json
"formats": [
  "markdown",
  {
    "type": "json",
    "schema": {
      "type": "object",
      "properties": {
        "title": { "type": "string" }
      }
    }
  }
]
```
The python code automatically detects if `extraction_schema` or `extraction_prompt` is provided, constructs this object, and appends it to the `formats` array.

**Graceful Fallbacks:**
If a page is so massive that it exceeds Firecrawl's *own* LLM token limit (like large Wikipedia pages), Firecrawl returns a `"warning"`. The code catches this error gracefully and falls back to returning the raw Markdown, ensuring the LangGraph agent never crashes unexpectedly.
