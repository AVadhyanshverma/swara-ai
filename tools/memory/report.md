# 🧠 Agentic Memory Engine (Hackathon Report)

## 🎯 The Objective
Building a long-term memory system for an AI Agent that runs **entirely locally** without relying on expensive, rate-limited external APIs (like OpenAI), while guaranteeing that massive data ingestion *never* freezes the chat interface for the user.

## 🛠️ The Tech Stack
- **Vector Database:** `Qdrant` (Running in-memory/local disk for lightning-fast semantic retrieval).
- **Embedding Model:** `BAAI/bge-small-en-v1.5` via `fastembed`. 
- **The "Why":** We intentionally avoided massive `PyTorch` or `SentenceTransformers` installations. By using `fastembed`, the model runs directly on the highly optimized `ONNX Runtime`, allowing the engine to run on heavily constrained hardware (like a 1GB RAM / 1-Core server) without crashing.

---

## 🏗️ Core Architectural Breakthroughs

### 1. Dynamic Resource Allocation
We built the engine to be **environmentally aware**. Upon initialization, it queries the Linux kernel for hardware limits and scales itself automatically:
- **CPU Scaling:** It detects total system cores and allocates a safe percentage of threads to the ONNX engine.
- **RAM Scaling:** It reserves ~250MB for the base ML model, then dynamically calculates the mathematically optimal `batch_size` based on the remaining free memory, completely eliminating Out-Of-Memory (OOM) crashes.

### 2. The Agent Hardware Calibration Script (`test_benchmark.py`)
Because ML embedding speeds vary wildly between a Macbook M3 (600+ words/sec) and a cheap cloud VPS (30 words/sec), we built a 1-second calibration script. 
When the Agent boots, it runs this script to determine its hardware's raw `words_per_second` capacity.

### 3. The 5-Second UX Protection Formula
To prevent the UI from freezing when a user pastes a massive document, the Agent uses the calibration data to set a hard synchronous limit:
```python
MAX_SYNC_WORDS = words_per_sec * 5
```
If an operation takes less than 5 seconds, it is embedded synchronously. If it exceeds this threshold, the agent employs **Dynamic Degradation**—instantly offloading the heavy processing to a background worker queue so the user can continue chatting uninterrupted.

### 4. Hierarchical "Summary Indexing"
Instead of blindly chunking and dumping 50,000 words into the Vector DB (which causes context bloat and slow retrieval), the Agent acts as a smart filter. 
The Agent synthesizes large texts into high-level summaries. Only the *summaries* are embedded into Qdrant, acting as a highly efficient "Table of Contents" that links back to the raw data stored on cheap standard storage.

### 5. Shared Swarm Memory (Cross-Session)
The engine doesn't just isolate memory per chat. It acts as a global brain. 
When an agent completes a task, it tags the memory using Qdrant payloads:
```json
{
  "agent_id": "Agent_A",
  "session_id": "chat_8891",
  "topic": "Martian Infrastructure"
}
```
Later, *Agent B* in a completely different session can run a semantic search and leverage Agent A's exact findings, or use strict metadata filters to only query specific past sessions.

---

## 🚀 How to Rebuild / Run

1. **Environment Setup**
   Ensure you are using the local virtual environment to isolate dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install qdrant-client fastembed
   ```

2. **Core Files**
   - `memory_engine.py`: Contains the `MemoryEngine` class with dynamic chunking, overlapping sliding windows, and OOM-safe file streaming.
   - `test_benchmark.py`: The rapid calibration script that outputs the JSON hardware profile for the Agent's routing logic.

3. **Running the Calibration**
   ```bash
   python memory/test_benchmark.py
   ```
   *(Review the JSON output to see your hardware's exact `words_per_second` limit.)*
