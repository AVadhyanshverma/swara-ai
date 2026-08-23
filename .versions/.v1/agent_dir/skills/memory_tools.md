# Memory Tools Skill

## Tools
- `add_memory(content: str, metadata: dict)`
- `retrieve_memory(query: str, top_k: int)`

## Usage Instructions
The agent has a persistent Vector Database (ChromaDB) to store and retrieve long-term context, documents, and research data across sessions.

1. **`add_memory`**: Use this to manually store important facts, user preferences, or specific notes. (Note: `analyze_document` automatically uses this tool behind the scenes).
   - `content`: The text you want to remember.
   - `metadata`: A dictionary with any helpful keys (e.g., `{"source": "user_chat", "topic": "preferences"}`).
2. **`retrieve_memory`**: Use this to search your Vector DB for relevant context.
   - `query`: A semantic search string.
   - `top_k`: How many results to return (default is 5).

*Always search memory before asking the user for information they may have provided in the past!*
