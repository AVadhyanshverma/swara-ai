from encrypted_chat_engine import EncryptedChatEngine

# 1. Initialize engine (automatically handles keys!)
engine = EncryptedChatEngine("my_secure_chat.db")
print("Engine initialized successfully.")

# 2. Add some rich JSON messages
thread = "session_1"
engine.add_message(thread, "user", {"text": "Hello, here is my file", "files": ["report.pdf"]})
engine.add_message(thread, "agent", {"text": "I received report.pdf. What should I do with it?"})
engine.add_message("session_2", "user", {"text": "Different thread!"})

# 3. Fast retrieval
print("\n--- Messages in session_1 ---")
for msg in engine.get_messages(thread):
    print(f"[{msg['role'].upper()}] {msg['content']['text']}")

# 4. Ultra-fast JSON Search
print("\n--- Searching for 'report' ---")
for msg in engine.search_messages("report"):
    print(f"Found in {msg['thread_id']}: {msg['content']}")

# 5. LangGraph Checkpointer Integration
memory = engine.get_langgraph_checkpointer()
print("\nLangGraph checkpointer ready:", type(memory))

engine.close()
