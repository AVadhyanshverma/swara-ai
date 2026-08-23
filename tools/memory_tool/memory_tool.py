import sys
import os
import json
import argparse

# Ensure the memory_engine can be imported from the memory folder
memory_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "memory"))
sys.path.insert(0, memory_dir)

from memory_engine import MemoryEngine

# Initialize the vector DB in the central brain directory
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
try:
    from path_manager import get_brain_dir
    DB_PATH = str(get_brain_dir())
    os.makedirs(DB_PATH, exist_ok=True)
except ImportError:
    # Fallback
    DB_PATH = os.path.join(memory_dir, "vector_db")

# Read optional resource limits from environment variables
max_mem = os.environ.get("MEMORY_ENGINE_MAX_MB")
max_cpu = os.environ.get("MEMORY_ENGINE_MAX_CPU")

engine = MemoryEngine(
    path=DB_PATH,
    max_memory_mb=int(max_mem) if max_mem else None,
    max_cpu_percent=float(max_cpu) if max_cpu else None
)

def store_memory(text: str, metadata_json: str = "{}"):
    try:
        metadata = json.loads(metadata_json)
    except json.JSONDecodeError as e:
        print(json.dumps({
            "status": "error",
            "message": f"Invalid metadata JSON: {str(e)}"
        }))
        sys.exit(1)
        
    doc_id, _ = engine.add_document(text=text, doc_metadata=metadata)
    print(json.dumps({
        "status": "success",
        "doc_id": doc_id,
        "message": "Successfully stored memory."
    }))

def store_file(file_path: str, metadata_json: str = "{}"):
    if not os.path.exists(file_path):
        print(json.dumps({
            "status": "error",
            "message": f"File not found: {file_path}"
        }))
        sys.exit(1)

    try:
        metadata = json.loads(metadata_json)
    except json.JSONDecodeError as e:
        print(json.dumps({
            "status": "error",
            "message": f"Invalid metadata JSON: {str(e)}"
        }))
        sys.exit(1)
        
    doc_id, _ = engine.add_file(file_path=file_path, doc_metadata=metadata)
    print(json.dumps({
        "status": "success",
        "doc_id": doc_id,
        "message": f"Successfully stored memory from file {file_path}."
    }))

def search_memory(query: str, limit: int = 5):
    results = engine.search(query=query, limit=limit)
    if not results:
        print(json.dumps({"status": "success", "results": []}))
        return
    
    output = []
    for res in results:
        output.append({
            "id": res.get("id", ""),
            "doc_id": res.get("doc_id", ""),
            "score": res.get("score", 0),
            "text": res.get("text", ""),
            "metadata": res.get("metadata", {})
        })
        
    print(json.dumps({
        "status": "success",
        "results": output
    }))

def delete_memory(doc_id: str):
    try:
        engine.delete_document(doc_id)
        print(json.dumps({
            "status": "success",
            "message": f"Successfully deleted document {doc_id}."
        }))
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": f"Failed to delete document: {str(e)}"
        }))
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Memory Tool for AI Agents")
    subparsers = parser.add_subparsers(dest="action", required=True, help="Action to perform")

    # Store subparser
    store_parser = subparsers.add_parser("store", help="Store text in the vector database")
    store_parser.add_argument("text", type=str, help="The text content to store")
    store_parser.add_argument("--metadata", type=str, default="{}", help="Optional JSON string of metadata key-value pairs")

    # Store file subparser
    store_file_parser = subparsers.add_parser("store-file", help="Store contents of a file in the vector database")
    store_file_parser.add_argument("file_path", type=str, help="The absolute or relative path to the file")
    store_file_parser.add_argument("--metadata", type=str, default="{}", help="Optional JSON string of metadata key-value pairs")

    # Search subparser
    search_parser = subparsers.add_parser("search", help="Search the vector database")
    search_parser.add_argument("query", type=str, help="The search query string")
    search_parser.add_argument("--limit", type=int, default=5, help="Maximum number of results to return")

    # Delete subparser
    delete_parser = subparsers.add_parser("delete", help="Delete a document and all its chunks by doc_id")
    delete_parser.add_argument("doc_id", type=str, help="The document ID to delete")

    args = parser.parse_args()

    if args.action == "store":
        store_memory(args.text, args.metadata)
    elif args.action == "store-file":
        store_file(args.file_path, args.metadata)
    elif args.action == "search":
        search_memory(args.query, args.limit)
    elif args.action == "delete":
        delete_memory(args.doc_id)

if __name__ == "__main__":
    main()
