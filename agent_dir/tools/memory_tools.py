import os
import sys
import json
from langchain_core.tools import tool

# Inject the memory directory into sys.path to import MemoryEngine
memory_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tools", "memory"))
if memory_dir not in sys.path:
    sys.path.insert(0, memory_dir)

try:
    from memory_engine import MemoryEngine
except ImportError as e:
    MemoryEngine = None
    print(f"Failed to import MemoryEngine: {e}")

try:
    from path_manager import get_brain_dir
    DB_PATH = str(get_brain_dir())
    os.makedirs(DB_PATH, exist_ok=True)
except ImportError:
    DB_PATH = os.path.join(memory_dir, "vector_db")


def get_engine():
    if not MemoryEngine:
        raise ImportError("MemoryEngine not loaded.")
    max_mem = os.environ.get("MEMORY_ENGINE_MAX_MB")
    max_cpu = os.environ.get("MEMORY_ENGINE_MAX_CPU")
    return MemoryEngine(
        path=DB_PATH,
        max_memory_mb=int(max_mem) if max_mem else None,
        max_cpu_percent=float(max_cpu) if max_cpu else None
    )

@tool
def memory_store(text: str, metadata_json: str = "{}") -> str:
    """Stores text in the memory vector database."""
    try:
        engine = get_engine()
        metadata = json.loads(metadata_json)
        doc_id, _ = engine.add_document(text=text, doc_metadata=metadata)
        return json.dumps({
            "status": "success",
            "doc_id": doc_id,
            "message": "Successfully stored memory."
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

@tool
def memory_search(query: str, limit: int = 5) -> str:
    """Searches the memory vector database."""
    try:
        engine = get_engine()
        results = engine.search(query=query, limit=limit)
        if not results:
            return json.dumps({"status": "success", "results": []})
        
        output = []
        for res in results:
            output.append({
                "id": res.get("id", ""),
                "doc_id": res.get("doc_id", ""),
                "score": res.get("score", 0),
                "text": res.get("text", ""),
                "metadata": res.get("metadata", {})
            })
            
        return json.dumps({
            "status": "success",
            "results": output
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        })
