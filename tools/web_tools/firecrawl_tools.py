import os
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from firecrawl import Firecrawl

# ---------------------------------------------------------------------------
# INITIALIZATION
# ---------------------------------------------------------------------------
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")
if not FIRECRAWL_API_KEY:
    raise ValueError("FIRECRAWL_API_KEY environment variable not set. Please add it to your proxy env.")

client = Firecrawl(api_key=FIRECRAWL_API_KEY)


# ==========================================
# 1. Search the Net Tool
# ==========================================
class SearchNetInput(BaseModel):
    query: str = Field(..., description="The search query.")
    limit: Optional[int] = Field(5, description="Number of results to return.")
    only_main_content: Optional[bool] = Field(True, description="Whether to extract only the main content.")

@tool("search_the_net", args_schema=SearchNetInput)
def search_the_net(
    query: str, 
    limit: int = 5, 
    only_main_content: bool = True, 
) -> Union[Dict[str, Any], str]:
    """
    Search the web for a query and return top results with their scraped content.
    """
    try:
        response = client.search(
            query=query,
            limit=limit,
            scrape_options={
                "formats": ["markdown"],
                "onlyMainContent": only_main_content
            }
        )
        return response.model_dump()
    except Exception as e:
        return f"Error: {str(e)}"


# ==========================================
# 2. Read Page Tool
# ==========================================
class ReadPageInput(BaseModel):
    url: str = Field(..., description="The URL to scrape.")
    only_main_content: Optional[bool] = Field(True, description="Whether to extract only the main content.")
    formats: Optional[List[str]] = Field(default=["markdown"], description="Formats to return. e.g. ['markdown'] or ['json'].")
    extraction_prompt: Optional[str] = Field(None, description="Instructions for extraction.")
    extraction_schema: Optional[Dict[str, Any]] = Field(None, description="JSON schema for extraction.")

@tool("read_the_page", args_schema=ReadPageInput)
def read_the_page(
    url: str, 
    only_main_content: bool = True, 
    formats: List[str] = None,
    extraction_prompt: Optional[str] = None,
    extraction_schema: Optional[Dict[str, Any]] = None
) -> Union[Dict[str, Any], str]:
    """
    Scrape a single URL. Use extraction_prompt to let Firecrawl's LLM summarize or extract data directly.
    """
    try:
        if extraction_prompt or extraction_schema:
            if not extraction_prompt:
                extraction_prompt = "Extract key information based on the schema."
            response = client.extract(
                urls=[url],
                prompt=extraction_prompt,
                schema=extraction_schema
            )
            return response.model_dump()
        else:
            if not formats:
                formats = ["markdown"]
            response = client.scrape_url(
                url, 
                formats=formats, 
                onlyMainContent=only_main_content
            )
            return response
    except Exception as e:
        return f"Error: {str(e)}"


# ==========================================
# 3. Batch Read Pages Tool
# ==========================================
class BatchReadPagesInput(BaseModel):
    urls: List[str] = Field(..., description="List of URLs to scrape concurrently.")
    only_main_content: Optional[bool] = Field(True, description="Whether to extract only the main content.")
    formats: Optional[List[str]] = Field(default=["markdown"], description="Formats to return.")
    extraction_prompt: Optional[str] = Field(None, description="Instructions for extraction.")
    extraction_schema: Optional[Dict[str, Any]] = Field(None, description="JSON schema for extraction.")

@tool("batch_read_pages", args_schema=BatchReadPagesInput)
def batch_read_pages(
    urls: List[str], 
    only_main_content: bool = True, 
    formats: List[str] = None,
    extraction_prompt: Optional[str] = None,
    extraction_schema: Optional[Dict[str, Any]] = None
) -> Union[Dict[str, Any], str]:
    """
    Scrape multiple URLs concurrently. Use extraction_prompt for LLM-driven data extraction across all pages.
    """
    try:
        if extraction_prompt or extraction_schema:
            if not extraction_prompt:
                extraction_prompt = "Extract key information based on the schema."
            response = client.extract(
                urls=urls,
                prompt=extraction_prompt,
                schema=extraction_schema
            )
            return response.model_dump()
        else:
            if not formats:
                formats = ["markdown"]
            response = client.batch_scrape_urls(
                urls, 
                formats=formats, 
                onlyMainContent=only_main_content
            )
            return response
    except Exception as e:
        return f"Error: {str(e)}"
