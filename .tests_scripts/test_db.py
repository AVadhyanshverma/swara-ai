import sqlite3
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(BASE_DIR))
from tools.chat_his.encrypted_chat_engine import EncryptedChatEngine

chat_engine = EncryptedChatEngine("SWARA")
cursor = chat_engine.conn.cursor()

try:
    cursor.execute("DELETE FROM checkpoints WHERE thread_id = 'test'")
except Exception as e:
    print("Error checkpoints:", e)

try:
    cursor.execute("DELETE FROM writes WHERE thread_id = 'test'")
except Exception as e:
    print("Error writes:", e)

try:
    cursor.execute("DELETE FROM checkpoint_writes WHERE thread_id = 'test'")
except Exception as e:
    print("Error checkpoint_writes:", e)

try:
    cursor.execute("DELETE FROM checkpoint_blobs WHERE thread_id = 'test'")
except Exception as e:
    print("Error checkpoint_blobs:", e)
