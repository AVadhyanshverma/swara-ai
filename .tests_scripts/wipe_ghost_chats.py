import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(BASE_DIR))
from agent_dir.agent import chat_engine

cursor = chat_engine.conn.cursor()

# Find threads that have no messages
cursor.execute("""
    SELECT thread_id, title FROM threads_metadata 
    WHERE thread_id NOT IN (SELECT thread_id FROM chat_messages)
""")
ghost_threads = cursor.fetchall()

print(f"Found {len(ghost_threads)} completely empty threads.")

for tid, title in ghost_threads:
    print(f"Deleting empty thread: {tid} ({title})")
    cursor.execute("DELETE FROM threads_metadata WHERE thread_id = ?", (tid,))

chat_engine.conn.commit()
print("Wipe complete!")
