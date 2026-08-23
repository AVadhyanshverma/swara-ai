import os
from tools.chat_his.encrypted_chat_engine import EncryptedChatEngine

DB_PATH = "/run/media/adhyansh/EFC6-61EA/datasets/code/chat_history.db"

engine = EncryptedChatEngine(DB_PATH)

print("Searching for 'nvidia'...")
results = engine.search_messages("nvidia")
for msg in results:
    text = msg['content'].get('content', '')[:200]
    print(f"[{msg['thread_id']}] {msg['role']}: {text}...")

print("-" * 50)
print("Searching for 'black screen'...")
results2 = engine.search_messages("black screen")
for msg in results2:
    text = msg['content'].get('content', '')[:200]
    print(f"[{msg['thread_id']}] {msg['role']}: {text}...")

engine.close()
