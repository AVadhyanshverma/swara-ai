import os
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from firecrawl import Firecrawl

# ---------------------------------------------------------------------------
# INITIALIZATION
# ---------------------------------------------------------------------------
FIRECRAWL_API_KEY = "fc-622a00f04c77417589271736496ce31c"

_client = None
def get_client():
    global _client
    if not _client:
        if not FIRECRAWL_API_KEY:
            raise ValueError("FIRECRAWL_API_KEY environment variable not set.")
        from firecrawl import Firecrawl
        _client = Firecrawl(api_key=FIRECRAWL_API_KEY)
    return _client

# ==========================================
# 1. Search the Net Tool
# ==========================================
class SearchNetInput(BaseModel):
    query: str = Field(..., description="The search query.")
    limit: Optional[int] = Field(3, description="Number of results to return. KEEP THIS LOW (2-3) to avoid token limit errors.")
    only_main_content: Optional[bool] = Field(True, description="Whether to extract only the main content. Always keep True.")

from difflib import SequenceMatcher

def deduplicate_lines(text: str, threshold: float = 0.85) -> str:
    """Remove near-duplicate lines (boilerplate)."""
    lines = text.split('\n')
    unique_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        is_duplicate = any(
            SequenceMatcher(None, line, existing).ratio() > threshold
            for existing in unique_lines[-20:]  # Check last 20 lines
        )
        if not is_duplicate:
            unique_lines.append(line)
    
    return '\n'.join(unique_lines)

def compress_markdown(text: str, max_tokens: int = 1500) -> str:
    """Aggressive but structure-preserving compression."""
    lines = text.split('\n')
    result = []
    current_tokens = 0
    words_per_token = 0.75
    
    for line in lines:
        words = len(line.split())
        line_tokens = int(words / words_per_token)
        
        if current_tokens + line_tokens > max_tokens:
            # Prioritize headings, lists, and tables
            if line.startswith('#') or line.startswith('-') or line.startswith('|'):
                result.append(line)
                current_tokens += line_tokens
            continue
        
        result.append(line)
        current_tokens += line_tokens
    
    return '\n'.join(result)

def analyze_with_nim(text: str, prompt: str) -> str:
    import httpx
    try:
        combined = f"{prompt}\n\nContent:\n{text}"
        # Make request to our proxy's /analyze route
        resp = httpx.post("http://localhost:8000/analyze", data={"text": combined}, timeout=120.0)
        resp.raise_for_status()
        return resp.json().get("result", "")
    except Exception as e:
        return f"[NIM Analysis Failed or Key Missing: {str(e)}] - Raw text length: {len(text)}"

@tool("search_the_net", args_schema=SearchNetInput)
def search_the_net(
    query: str, 
    limit: int = 3, 
    only_main_content: bool = True,
    max_tokens_per_result: int = 1500
) -> str:
    """
    Search the web for a query and return top results with their scraped content.
    """
    try:
        response_model = get_client().search(
            query=query,
            limit=limit,
            scrape_options={
                "formats": ["markdown"],
                "onlyMainContent": only_main_content,
                "excludeTags": ['nav', 'footer', 'aside', 'header', 'script', 'style']
            }
        )
        
        import json
        response = response_model.model_dump()
        formatted_results = []
        
        # Firecrawl's latest SDK puts search results under 'web', older SDKs used 'data'
        search_items = response.get("web", response.get("data", []))
        
        for item in search_items:
            raw_md = item.get("markdown", "")
            
            cleaned_md = ""
            if raw_md:
                cleaned_md = deduplicate_lines(raw_md)
                cleaned_md = compress_markdown(cleaned_md, max_tokens=max_tokens_per_result)
                
                # Send to DeepSeek via NIM for refined extraction
                nim_prompt = "You are a data extractor. Extract the most important details, key facts, and any relevant links from the following search result. Keep it concise."
                extracted_info = analyze_with_nim(cleaned_md, nim_prompt)
                
                # Fallback to raw if NIM fails
                if "NIM Analysis Failed" in extracted_info:
                    extracted_info = cleaned_md + f"\n\n{extracted_info}"
                    
                cleaned_md = extracted_info
            
            metadata = item.get("metadata", {})
            formatted_results.append({
                "url": item.get("url") or metadata.get("url"),
                "title": item.get("title") or metadata.get("title"),
                "description": item.get("description") or metadata.get("description"),
                "content": cleaned_md
            })
            
        return json.dumps(formatted_results, indent=2)
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
    max_tokens: Optional[int] = Field(3000, description="Max tokens of markdown to keep if not using extraction_prompt. Increase for deeper context.")

@tool("read_the_page", args_schema=ReadPageInput)
def read_the_page(
    url: str, 
    only_main_content: bool = True, 
    formats: List[str] = None,
    extraction_prompt: Optional[str] = None,
    extraction_schema: Optional[Dict[str, Any]] = None,
    max_tokens: int = 3000
) -> str:
    """
    Scrape a single URL. 
    CRITICAL INSTRUCTION: To avoid Token Limit Errors, you MUST use 'extraction_prompt' 
    whenever you are looking for specific information. This tells the Firecrawl server 
    to extract ONLY the core details you need instead of dumping the entire page text into your context.
    """
    import json
    try:
        if extraction_prompt or extraction_schema:
            if not extraction_prompt:
                extraction_prompt = "Extract key information based on the schema."
            response_model = get_client().extract(
                urls=[url],
                prompt=extraction_prompt,
                schema=extraction_schema
            )
            return json.dumps(response_model.model_dump(), indent=2)
        else:
            if not formats:
                formats = ["markdown"]
            response = get_client().scrape_url(
                url, 
                formats=formats, 
                onlyMainContent=only_main_content
            )
            
            if hasattr(response, "model_dump"):
                response = response.model_dump()
            elif hasattr(response, "dict"):
                response = response.dict()
                
            raw_md = response.get("markdown", "")
            if raw_md:
                cleaned_md = deduplicate_lines(raw_md)
                cleaned_md = compress_markdown(cleaned_md, max_tokens=max_tokens)
                
                if len(cleaned_md.split()) * 0.75 >= max_tokens:
                     cleaned_md += f"\n\n... [TRUNCATED at {max_tokens} tokens. Use extraction_prompt to get specific data.]"
                response["markdown"] = cleaned_md
                
            return json.dumps(response, indent=2)
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
) -> str:
    """
    Scrape multiple URLs concurrently. 
    """
    import json
    try:
        if extraction_prompt or extraction_schema:
            if not extraction_prompt:
                extraction_prompt = "Extract key information based on the schema."
            response_model = get_client().extract(
                urls=urls,
                prompt=extraction_prompt,
                schema=extraction_schema
            )
            return json.dumps(response_model.model_dump(), indent=2)
        else:
            if not formats:
                formats = ["markdown"]
            
            batch_resp = get_client().batch_scrape_urls(
                urls, 
                formats=formats, 
                onlyMainContent=only_main_content
            )
            
            # Note: batch_scrape_urls returns dict or object depending on SDK
            if hasattr(batch_resp, "model_dump"):
                batch_resp = batch_resp.model_dump()
            elif hasattr(batch_resp, "dict"):
                batch_resp = batch_resp.dict()
                
            results = []
            nim_prompt = "You are a data extractor. Extract the most important details, key facts, and any relevant links from the following web page content. Keep it concise and structured."
            
            batch_items = batch_resp.get("web", batch_resp.get("data", []))
            
            for item in batch_items:
                raw_md = item.get("markdown", "")
                if raw_md:
                    cleaned_md = deduplicate_lines(raw_md)
                    cleaned_md = compress_markdown(cleaned_md, max_tokens=3000)
                    
                    extracted_info = analyze_with_nim(cleaned_md, nim_prompt)
                    
                    if "NIM Analysis Failed" in extracted_info:
                        extracted_info = cleaned_md + f"\n\n{extracted_info}"
                        
                    metadata = item.get("metadata", {})
                    results.append({
                        "url": item.get("url") or metadata.get("url"),
                        "extracted_info": extracted_info
                    })
                
            return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"
