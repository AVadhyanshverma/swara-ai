import os
import secrets
import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

# For LangGraph integration
from langgraph.checkpoint.sqlite import SqliteSaver
from sqlcipher3 import dbapi2 as sqlite

import platform
import multiprocessing
import hashlib

class SecureKeyManager:
    """Manages a device-specific encryption key automatically using hardware characteristics."""
    
    @staticmethod
    def get_or_create_device_key() -> str:
        """
        Generates a deterministic, device-specific key based on hardware and OS details.
        The key will remain identical on this machine until it is formatted.
        """
        components = []
        
        # OS Name & Architecture
        components.append(platform.system())
        components.append(platform.machine())
        
        # 1. Motherboard UUID / Platform UUID (Most Permanent)
        # We try cross-platform methods to get the deep hardware ID
        try:
            if platform.system() == "Windows":
                import subprocess
                hw_uuid = subprocess.check_output('wmic csproduct get uuid').decode().split('\n')[1].strip()
                components.append(hw_uuid)
            elif platform.system() == "Darwin":
                import subprocess
                hw_uuid = subprocess.check_output(['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice']).decode()
                # Simple extraction, normally we'd parse the plist/xml
                for line in hw_uuid.split('\n'):
                    if 'IOPlatformUUID' in line:
                        components.append(line.split('=')[1].strip().strip('"'))
                        break
            elif platform.system() == "Linux":
                # Try motherboard UUID first (requires root on some distros)
                try:
                    with open("/sys/class/dmi/id/product_uuid", "r") as f:
                        components.append(f.read().strip())
                except PermissionError:
                    # Fallback to the OS installation UUID (Pure Software ID - Temporary)
                    with open("/etc/machine-id", "r") as f:
                        components.append(f.read().strip())
        except Exception:
            pass
            
        # 2. CPU Cores & Model (Additional entropy)
        try:
            components.append(str(multiprocessing.cpu_count()))
            if platform.system() == "Linux":
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "model name" in line:
                            components.append(line.split(":")[1].strip())
                            break
        except Exception:
            pass

        # 3. MAC Address & Hostname (Fallback identifiers)
        components.append(str(uuid.getnode()))
        components.append(platform.node())

        # Combine all components into a single unique string
        raw_string = "|".join(components)
        
        # Hash to get a deterministic 256-bit (64-character hex) key for SQLCipher
        return hashlib.sha256(raw_string.encode('utf-8')).hexdigest()


class EncryptedChatEngine:
    """
    An ultra-fast, encrypted SQLite engine for storing and searching 
    chat histories, with seamless LangGraph support.
    """
    
    def __init__(self, db_path: Optional[str] = None, key: Optional[str] = None):
        """
        Initializes the database. If key is not provided, automatically
        gets or creates a device-specific key.
        """
        if db_path is None:
            try:
                import sys
                import os
                # Add root to sys path if not there
                root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                if root_dir not in sys.path:
                    sys.path.append(root_dir)
                from path_manager import get_chats_dir
                chats_dir = get_chats_dir()
                os.makedirs(chats_dir, exist_ok=True)
                db_path = str(chats_dir / "SWARA_chats.db")
            except ImportError:
                import os
                db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "SWARA_chats.db"))
        self.db_path = db_path
        self.key = key or SecureKeyManager.get_or_create_device_key()
        
        # Connect to DB and enable encryption (timeout=20s for heavy concurrency)
        self.conn = sqlite.connect(self.db_path, check_same_thread=False, timeout=20.0)
        self.cursor = self.conn.cursor()
        
        # Apply the encryption key immediately
        self.cursor.execute(f"PRAGMA key = '{self.key}';")
        
        # Optimize SQLite for speed and concurrency
        self.cursor.execute("PRAGMA journal_mode = WAL;")
        self.cursor.execute("PRAGMA synchronous = NORMAL;")
        self.cursor.execute("PRAGMA cache_size = -64000;") # ~64MB cache per connection
        
        self._init_schema()

    def _init_schema(self):
        """Initializes tables and indexes for ultra-fast JSON searching."""
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY,
                thread_id TEXT,
                role TEXT,
                content JSON,
                metadata JSON,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Index for fast thread fetching
            CREATE INDEX IF NOT EXISTS idx_thread ON chat_messages(thread_id, timestamp);
            
            -- Expression index for ultra-fast text search within JSON content
            CREATE INDEX IF NOT EXISTS idx_content_text ON chat_messages(json_extract(content, '$.text'));
        """)
        self.conn.commit()

    def add_message(self, thread_id: str, role: str, content: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Stores a full JSON message securely. 
        Compatible with complex structures like file attachments.
        """
        msg_id = str(uuid.uuid4())
        meta = metadata or {}
        
        self.cursor.execute("""
            INSERT INTO chat_messages (id, thread_id, role, content, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (msg_id, thread_id, role, json.dumps(content), json.dumps(meta)))
        self.conn.commit()
        return msg_id

    def get_messages(self, thread_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Fast retrieval of messages for a specific thread."""
        self.cursor.execute("""
            SELECT id, thread_id, role, content, metadata, timestamp 
            FROM chat_messages 
            WHERE thread_id = ? 
            ORDER BY timestamp ASC
            LIMIT ?
        """, (thread_id, limit))
        
        results = []
        for row in self.cursor.fetchall():
            results.append({
                "id": row[0],
                "thread_id": row[1],
                "role": row[2],
                "content": json.loads(row[3]),
                "metadata": json.loads(row[4]),
                "timestamp": row[5]
            })
        return results

    def search_messages(self, search_text: str, thread_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Ultra-fast search inside JSON message contents.
        Uses SQLite JSON expression indexes.
        """
        query = """
            SELECT id, thread_id, role, content, metadata, timestamp 
            FROM chat_messages 
            WHERE (json_extract(content, '$.text') LIKE ? OR json_extract(content, '$.content') LIKE ?)
        """
        params = [f"%{search_text}%", f"%{search_text}%"]
        
        if thread_id:
            query += " AND thread_id = ?"
            params.append(thread_id)
            
        query += " ORDER BY timestamp DESC LIMIT 50"
        
        self.cursor.execute(query, params)
        
        results = []
        for row in self.cursor.fetchall():
            results.append({
                "id": row[0],
                "thread_id": row[1],
                "role": row[2],
                "content": json.loads(row[3]),
                "metadata": json.loads(row[4]),
                "timestamp": row[5]
            })
        return results
        
    def get_langgraph_checkpointer(self) -> SqliteSaver:
        """
        Returns a LangGraph SqliteSaver using the SAME encrypted connection.
        This allows LangGraph's multi-agent system to securely store its state
        alongside your custom chat messages.
        """
        return SqliteSaver(self.conn)

    def close(self):
        self.conn.close()
