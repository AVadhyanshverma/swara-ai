import os
import io
import httpx
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class AnalyzeDocumentInput(BaseModel):
    file_path: str = Field(..., description="Absolute path to the document (PDF, image, etc.)")
    instruction: str = Field(default="Analyze this page in detail.", description="Instructions for the vision model.")

@tool("analyze_document", args_schema=AnalyzeDocumentInput)
def analyze_document(file_path: str, instruction: str = "Analyze this page in detail.") -> str:
    """
    Analyzes a document, image, or video and stores the extracted text into the agent's Vector Database.
    For documents (PDFs, Word, etc.), it uses Firecrawl parsing.
    For images and videos, it sends them to the local vision model proxy.
    """
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"
        
    try:
        from agent_dir.tools.memory_tools import get_engine
        engine = get_engine()
    except Exception as e:
        return f"Error initializing Vector DB: {str(e)}"
        
    ext = os.path.splitext(file_path)[1].lower()
    image_video_exts = {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".gif"}
    
    try:
        if ext in image_video_exts:
            # Use local proxy for images/videos
            with open(file_path, "rb") as f:
                file_bytes = f.read()
                
            mime_type = "image/jpeg"
            if ext == ".png": mime_type = "image/png"
            elif ext == ".mp4": mime_type = "video/mp4"
            elif ext == ".webp": mime_type = "image/webp"
            elif ext == ".gif": mime_type = "image/gif"
                
            files = {'file': (os.path.basename(file_path), file_bytes, mime_type)}
            data = {'text': instruction}
            
            resp = httpx.post("http://localhost:8000/analyze", data=data, files=files, timeout=120.0)
            if resp.status_code == 200:
                text = resp.json().get("result", "")
                content_to_store = f"Source: {os.path.basename(file_path)}\nContent: {text}"
                engine.add_document(text=content_to_store, doc_metadata={"source": file_path})
                return f"File analyzed and stored successfully.\nExtracted: {text}"
            else:
                return f"Failed: {resp.text}"
        else:
            # Use Firecrawl parse for documents
            from firecrawl import Firecrawl
            from firecrawl.v2.types import ScrapeOptions
            from agent_dir.tools.firecrawl_tools import FIRECRAWL_API_KEY
            
            app = Firecrawl(api_key=FIRECRAWL_API_KEY)
            
            doc = app.parse(
                file_path,
                options=ScrapeOptions(
                    only_main_content=True,
                    formats=["markdown"],
                ),
            )
            
            text = doc.markdown
            if not text:
                return "Firecrawl returned empty markdown for this document."
                
            content_to_store = f"Source: {os.path.basename(file_path)}\nContent: {text}"
            engine.add_document(text=content_to_store, doc_metadata={"source": file_path})
            
            return f"Document parsed via Firecrawl and stored successfully.\nLength: {len(text)} characters."

    except Exception as e:
        return f"Error during document analysis: {str(e)}"
