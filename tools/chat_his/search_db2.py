import os
from tools.chat_his.encrypted_chat_engine import EncryptedChatEngine

DB_PATH = "/run/media/adhyansh/EFC6-61EA/datasets/code/chat_history.db"
engine = EncryptedChatEngine(DB_PATH)

# Search for threads that have both 'nvidia' and 'black screen' or 'linux'
print("Advanced query across DB...")

query = """
    SELECT thread_id, group_concat(json_extract(content, '$.content')) as full_thread
    FROM chat_messages
    GROUP BY thread_id
    HAVING LOWER(full_thread) LIKE '%nvidia%'
       AND LOWER(full_thread) LIKE '%linux%'
"""
engine.cursor.execute(query)
results = engine.cursor.fetchall()

for row in results:
    thread_id = row[0]
    print(f"FOUND MATCH IN THREAD: {thread_id}")

engine.close()
