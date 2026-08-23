import os
import json
import textwrap
from tools.chat_his.encrypted_chat_engine import EncryptedChatEngine

engine = EncryptedChatEngine("/run/media/adhyansh/EFC6-61EA/datasets/code/chat_history.db")
msgs = engine.cursor.execute("SELECT thread_id, role, content FROM chat_messages").fetchall()

print("Scanning for Linux/Nvidia/Black Screen/Error issues...")
for tid, role, content_str in msgs:
    try:
        content_json = json.loads(content_str)
        text = content_json.get("content", "").lower()
        
        # We are looking for issues related to linux/nvidia/black screen
        if ("linux" in text or "nvidia" in text) and ("black" in text or "screen" in text or "error" in text or "crash" in text or "display" in text):
            print(f"\n--- THREAD: {tid} | ROLE: {role} ---")
            print(textwrap.shorten(text, 800))
    except:
        pass
        
engine.close()
