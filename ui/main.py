import sys
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


import threading
import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
import time
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Benchmark start time
start_time = time.time()

app = FastAPI()

# Serve UI assets (CSS, JS, images) from the static/ directory
_static_dir = os.path.join(BASE_DIR, "static")
os.makedirs(_static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=_static_dir), name="static")

_ui_story_static = os.path.join(os.path.dirname(BASE_DIR), "ui_story", "static")
if os.path.exists(_ui_story_static):
    app.mount("/ui_story_static", StaticFiles(directory=_ui_story_static), name="ui_story_static")



import sys
sys.path.insert(0, os.path.abspath(os.path.join(BASE_DIR, "..")))

from pydantic import BaseModel
from typing import Optional
from agent_dir.agent import stream_agent_response, chat_engine, agent_app
import uuid
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

class ChatRequest(BaseModel):
    text: str
    thread_id: Optional[str] = "main_thread"

def generate_title_background(text: str, thread_id: str):
    try:
        cursor = chat_engine.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threads_metadata (
                thread_id TEXT PRIMARY KEY,
                title TEXT
            )
        """)
        chat_engine.conn.commit()
        
        cursor.execute("SELECT title FROM threads_metadata WHERE thread_id = ?", (thread_id,))
        row = cursor.fetchone()
        if not row or not row[0]:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage
            
            summary_llm = ChatOpenAI(
                base_url="https://adhyanshverma-data-gen.hf.space/v1",
                api_key=HF_TOKEN,
                model="deepseek-ai/DeepSeek-V4-Flash-0731"
            )
            prompt = f"Generate a short (2-5 words) chat title for the following message. Just return the title, no quotes or extra text.\n\nMessage: {text[:1000]}"
            res = summary_llm.invoke([HumanMessage(content=prompt)])
            title = res.content.strip()
            # Remove <think>...</think> blocks if present
            import re
            title = re.sub(r'<think>.*?</think>', '', title, flags=re.DOTALL).strip()
            title = title.strip('"').strip("'").strip()
            
            cursor.execute("""
                INSERT INTO threads_metadata (thread_id, title)
                VALUES (?, ?)
                ON CONFLICT(thread_id) DO UPDATE SET title=excluded.title
            """, (thread_id, title))
            chat_engine.conn.commit()
    except Exception as e:
        print("Title generation failed:", e)

import asyncio

active_streams = {}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest, request: Request):
    threading.Thread(target=generate_title_background, args=(req.text, req.thread_id), daemon=True).start()
    
    stream_data = {
        "chunks": [],
        "done": False,
        "event": asyncio.Event(),
        "prompt": req.text
    }
    active_streams[req.thread_id] = stream_data
    loop = asyncio.get_running_loop()
    
    def run_agent():
        try:
            for chunk in stream_agent_response(req.text, req.thread_id):
                stream_data["chunks"].append(chunk)
                loop.call_soon_threadsafe(stream_data["event"].set)
        except Exception as e:
            stream_data["chunks"].append(f"\n\n*[System Error: {e}]*\n\n")
            loop.call_soon_threadsafe(stream_data["event"].set)
        finally:
            stream_data["done"] = True
            loop.call_soon_threadsafe(stream_data["event"].set)
            
    threading.Thread(target=run_agent, daemon=True).start()
    
    async def event_generator():
        idx = 0
        while True:
            if await request.is_disconnected():
                break
            if idx < len(stream_data["chunks"]):
                chunk = stream_data["chunks"][idx]
                idx += 1
                yield chunk
            elif stream_data["done"]:
                break
            else:
                stream_data["event"].clear()
                try:
                    await asyncio.wait_for(stream_data["event"].wait(), timeout=1.0)
                except asyncio.TimeoutError:
                    pass
                    
        # Cleanup only if completely finished and client didn't disconnect midway
        if stream_data["done"] and not await request.is_disconnected():
            active_streams.pop(req.thread_id, None)

    return StreamingResponse(event_generator(), media_type="text/plain")

@app.get("/api/chat/{thread_id}/stream")
async def attach_chat_stream(thread_id: str, request: Request):
    stream_data = active_streams.get(thread_id)
    if not stream_data:
        return Response(status_code=204)
        
    async def event_generator():
        # Start from the beginning to replay what they missed
        idx = 0
        while True:
            if await request.is_disconnected():
                break
            if idx < len(stream_data["chunks"]):
                chunk = stream_data["chunks"][idx]
                idx += 1
                yield chunk
            elif stream_data["done"]:
                break
            else:
                stream_data["event"].clear()
                try:
                    await asyncio.wait_for(stream_data["event"].wait(), timeout=1.0)
                except asyncio.TimeoutError:
                    pass
                    
        if stream_data["done"]:
            active_streams.pop(thread_id, None)

    return StreamingResponse(event_generator(), media_type="text/plain")

@app.get("/api/threads")
def get_threads():
    try:
        cursor = chat_engine.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threads_metadata (
                thread_id TEXT PRIMARY KEY,
                title TEXT
            )
        """)
        chat_engine.conn.commit()
        
        cursor.execute("""
            SELECT t.thread_id, MAX(c.checkpoint_id), m.title 
            FROM (
                SELECT thread_id FROM checkpoints
                UNION
                SELECT thread_id FROM threads_metadata
            ) t
            LEFT JOIN checkpoints c ON t.thread_id = c.thread_id
            LEFT JOIN threads_metadata m ON t.thread_id = m.thread_id
            GROUP BY t.thread_id
        """)
        rows = cursor.fetchall()
        
        import uuid
        import time
        result = []
        for r in rows:
            thread_id, checkpoint_id, title = r[0], r[1], r[2]
            ts = time.time()
            try:
                if checkpoint_id:
                    u = uuid.UUID(checkpoint_id)
                    ts = (u.time - 0x01b21dd213814000) / 1e7
            except Exception:
                pass
            result.append({
                "thread_id": thread_id,
                "updated_at": ts,
                "title": title
            })
            
        result.sort(key=lambda x: x["updated_at"], reverse=True)
        return result
    except Exception as e:
        return []

@app.post("/api/threads/new")
def create_thread():
    thread_id = str(uuid.uuid4())
    try:
        cursor = chat_engine.conn.cursor()
        cursor.execute("INSERT INTO threads_metadata (thread_id, title) VALUES (?, ?)", (thread_id, None))
        chat_engine.conn.commit()
    except Exception as e:
        print("Error creating thread metadata:", e)
    return {"thread_id": thread_id}

@app.get("/api/threads/{thread_id}/messages")
def get_thread_messages(thread_id: str):
    try:
        state = agent_app.get_state({"configurable": {"thread_id": thread_id}})
        messages = state.values.get("messages", [])
        result = []
        
        current_assistant_text = ""
        
        for m in messages:
            if isinstance(m, HumanMessage):
                if current_assistant_text:
                    result.append({"role": "assistant", "content": current_assistant_text.strip()})
                    current_assistant_text = ""
                result.append({"role": "user", "content": m.content})
                
            elif isinstance(m, AIMessage):
                # Extract text whether content is a string or a list of blocks
                content = ""
                if isinstance(m.content, str):
                    content = m.content
                elif isinstance(m.content, list):
                    for block in m.content:
                        if isinstance(block, str):
                            content += block
                        elif isinstance(block, dict) and block.get("type") == "text":
                            content += block.get("text", "")
                
                if content:
                    if m.response_metadata and "model_name" in m.response_metadata:
                        model_name = m.response_metadata["model_name"]
                        model_header = f"**[Model: {model_name}]**\n\n"
                        if model_header not in current_assistant_text:
                            current_assistant_text += model_header
                    current_assistant_text += content + "\n"
                
                if hasattr(m, "tool_calls") and m.tool_calls:
                    for tc in m.tool_calls:
                        tc_name = tc.get('name', 'unknown')
                        tc_id = tc.get('id', 'unknown')
                        tc_args = tc.get('args', {})
                        import json
                        try:
                            tc_args_str = "```json\n" + json.dumps(tc_args, indent=2) + "\n```"
                        except:
                            tc_args_str = "```python\n" + str(tc_args) + "\n```"
                        current_assistant_text += f"\n<think>\n🚀 tool_call name: {tc_name}\nid: {tc_id}\nArguments:\n{tc_args_str}\n</think>\n"
                        
            elif isinstance(m, ToolMessage):
                content_str = str(m.content)
                import json
                try:
                    parsed = json.loads(content_str)
                    content_str = "```json\n" + json.dumps(parsed, indent=2) + "\n```"
                except Exception:
                    pass
                tc_id = m.tool_call_id if hasattr(m, 'tool_call_id') else 'unknown'
                current_assistant_text += f"\n<think>\n✅ tool_call_results id: {tc_id}\nResult:\n{content_str}\n</think>\n"

        if current_assistant_text:
            result.append({"role": "assistant", "content": current_assistant_text.strip()})
            
        return {"messages": result}
    except Exception as e:
        return {"messages": []}

@app.get("/api/files")
def get_file_content(path: str, thread_id: str = ""):
    try:
        project_root = os.path.dirname(BASE_DIR)
        
        # Clean path of any stray markdown artifacts or quotes
        path = path.strip().strip("'").strip('"')
        
        # If the path is relative, try to resolve it
        if not os.path.isabs(path):
            sys.path.append(project_root)
            from path_manager import get_agent_workspace
            
            # Try 1: Resolve against the current thread_id workspace
            target_path = None
            if thread_id:
                base_dir = str(get_agent_workspace(thread_id))
                test_path = os.path.abspath(os.path.join(base_dir, path))
                if os.path.exists(test_path):
                    target_path = test_path
            
            # Try 2: Resolve against the project root
            if not target_path:
                test_path = os.path.abspath(os.path.join(project_root, path))
                if os.path.exists(test_path):
                    target_path = test_path
                    
            # Try 3: Fallback - deeply search the entire agent_workplace for the filename
            if not target_path:
                workplace_root = os.path.join(project_root, "agent_workplace")
                if os.path.exists(workplace_root):
                    search_name = os.path.basename(path)
                    for root, _, files in os.walk(workplace_root):
                        if search_name in files:
                            target_path = os.path.join(root, search_name)
                            break
                            
            path = target_path or path # keep original if not found (will trigger error below)
            
        if not os.path.exists(path):
            return {"error": "File not found in workspace", "path": path}
            
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.endswith('\n\n'):
                content += '\n\n'
        return {"content": content, "path": path}
    except Exception as e:
        return {"error": str(e), "path": path}

@app.delete("/api/threads/{thread_id}")
def delete_thread(thread_id: str):
    try:
        cursor = chat_engine.conn.cursor()
        cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
        cursor.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
        cursor.execute("DELETE FROM threads_metadata WHERE thread_id = ?", (thread_id,))
        chat_engine.conn.commit()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
class RenameRequest(BaseModel):
    title: str

@app.patch("/api/threads/{thread_id}")
def rename_thread(thread_id: str, req: RenameRequest):
    try:
        cursor = chat_engine.conn.cursor()
        cursor.execute("""
            INSERT INTO threads_metadata (thread_id, title)
            VALUES (?, ?)
            ON CONFLICT(thread_id) DO UPDATE SET title=excluded.title
        """, (thread_id, req.title))
        chat_engine.conn.commit()
        return {"status": "success", "title": req.title}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def check_user_profile():
    cursor = chat_engine.conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY,
            name TEXT,
            dob TEXT,
            ai_persona TEXT
        )
    """)
    chat_engine.conn.commit()
    cursor.execute("SELECT name, dob, ai_persona FROM user_profile LIMIT 1")
    return cursor.fetchone()

@app.get("/", response_class=HTMLResponse)
@app.get("/chat/{thread_id}", response_class=HTMLResponse)
def read_root(request: Request, thread_id: Optional[str] = None):
    if not check_user_profile():
        url = "/welcome"
        if "q" in request.query_params:
            url += f"?q={request.query_params['q']}"
        return RedirectResponse(url=url)
        
    html_path = os.path.join(BASE_DIR, "index.html")
    with open(html_path, "r") as f:
        return f.read()

@app.get("/welcome", response_class=HTMLResponse)
def read_welcome():
    html_path = os.path.join(os.path.dirname(BASE_DIR), "ui_story", "index.html")
    with open(html_path, "r") as f:
        return f.read()

@app.get("/setup", response_class=HTMLResponse)
def read_setup():
    return """
    <html>
      <head>
        <title>Setup - SWARA</title>
        <style>
          body { background: #0B0B0F; color: #F2F2F5; font-family: 'Inter', sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
          .container { background: #131318; padding: 2.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.06); width: 100%; max-width: 420px; box-shadow: 0 16px 48px rgba(0,0,0,.35); }
          h2 { margin-top: 0; color: #7fff00; font-weight: 800; font-size: 28px; }
          p { color: #A1A1AA; font-size: 0.9rem; margin-bottom: 2rem; }
          label { display: block; margin-top: 1.2rem; font-size: 0.85rem; color: #A1A1AA; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; }
          input, textarea { width: 100%; padding: 12px; margin-top: 8px; background: #1A1A21; border: 1px solid rgba(255,255,255,0.12); color: #fff; border-radius: 8px; box-sizing: border-box; font-family: inherit; font-size: 14px; transition: border-color 0.2s; }
          input:focus, textarea:focus { outline: none; border-color: #7fff00; box-shadow: 0 0 12px rgba(127, 255, 0, 0.15); }
          button { margin-top: 2rem; width: 100%; padding: 14px; background: #7fff00; color: #0B0B0F; border: none; border-radius: 8px; font-weight: 700; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; cursor: pointer; transition: all 0.2s cubic-bezier(.4,0,.2,1); }
          button:hover { background: #66cc00; transform: translateY(-2px); box-shadow: 0 4px 20px rgba(127,255,0,0.25); }
        </style>
      </head>
      <body>
        <div class="container">
          <h2>Welcome to SWARA</h2>
          <p>Let's personalize your local intelligence.</p>
          <form method="POST" action="/api/save_profile">
            <label>Name</label>
            <input type="text" name="name" required placeholder="e.g. Alex">
            
            <label>Date of Birth</label>
            <input type="date" name="dob" required>
            
            <label>AI Persona</label>
            <textarea name="ai_persona" rows="3" placeholder="How would you like AI to feel in talk? e.g. Friendly, professional, humorous..." required></textarea>
            
            <button type="submit">Complete Setup</button>
          </form>
        </div>
      </body>
    </html>
    """

@app.post("/api/save_profile")
def save_profile(name: str = Form(...), dob: str = Form(...), ai_persona: str = Form(...)):
    cursor = chat_engine.conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY,
            name TEXT,
            dob TEXT,
            ai_persona TEXT
        )
    """)
    cursor.execute("DELETE FROM user_profile")
    cursor.execute("INSERT INTO user_profile (name, dob, ai_persona) VALUES (?, ?, ?)", (name, dob, ai_persona))
    chat_engine.conn.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/api/profile")
def get_profile():
    cursor = chat_engine.conn.cursor()
    try:
        cursor.execute("SELECT name, dob, ai_persona FROM user_profile LIMIT 1")
        row = cursor.fetchone()
        if row:
            return {"name": row[0], "dob": row[1], "ai_persona": row[2]}
    except:
        pass
    return {}

@app.delete("/api/chats")
def delete_all_chats():
    cursor = chat_engine.conn.cursor()
    try:
        cursor.execute("DELETE FROM chat_messages")
        cursor.execute("DELETE FROM checkpoints")
        cursor.execute("DELETE FROM writes")
        cursor.execute("DELETE FROM threads_metadata")
        chat_engine.conn.commit()
        return {"status": "success"}
    except Exception as e:
        return {"error": str(e)}

@app.delete("/api/account")
def delete_account():
    cursor = chat_engine.conn.cursor()
    try:
        cursor.execute("DROP TABLE IF EXISTS user_profile")
        cursor.execute("DELETE FROM chat_messages")
        cursor.execute("DELETE FROM checkpoints")
        cursor.execute("DELETE FROM writes")
        cursor.execute("DELETE FROM threads_metadata")
        chat_engine.conn.commit()
        return {"status": "success"}
    except Exception as e:
        return {"error": str(e)}

import json
@app.get("/api/backup")
def backup_chats():
    cursor = chat_engine.conn.cursor()
    cursor.execute("SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id")
    threads = [row[0] for row in cursor.fetchall()]

    def generate_backup():
        yield "[\n"
        first_item = True

        for thread_id in threads:
            try:
                state = agent_app.get_state({"configurable": {"thread_id": thread_id}})
                messages = state.values.get("messages", [])
                chat_messages = []

                for message in messages:
                    if isinstance(message, HumanMessage):
                        role = "user"
                    elif isinstance(message, AIMessage):
                        role = "assistant"
                    elif isinstance(message, ToolMessage):
                        role = "tool"
                    else:
                        continue

                    chat_messages.append({
                        "role": role,
                        "content": str(message.content)
                    })

                if not first_item:
                    yield ",\n"
                yield json.dumps(
                    {"thread_id": thread_id, "messages": chat_messages},
                    indent=2
                )
                first_item = False
            except Exception as e:
                print(f"Skipping thread {thread_id} during backup: {e}")

        yield "\n]"

    return StreamingResponse(
        generate_backup(),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=swara_chats_backup.json"}
    )

import socket

# --- Load HF Token ---
import os
HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    try:
        token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "proxy_server", "hf_token.txt")
        if not os.path.exists(token_path):
            token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proxy_server", "hf_token.txt")
        with open(token_path, "r") as f:
            HF_TOKEN = f.read().strip()
    except:
        HF_TOKEN = "dummy_key_replaced_by_proxy"


def _port_in_use(host: str, port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        return sock.connect_ex((host, port)) == 0
    finally:
        sock.close()

def wait_for_server(host: str, port: int, retries: int = 30, delay: float = 0.3) -> bool:
    for _ in range(retries):
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(delay)
    return False

def run_server():
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=8080,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    server.run()

def start_ui():
    APP_PORT = 8080
    
    if _port_in_use("127.0.0.1", APP_PORT):
        print(f"\nERROR: Port {APP_PORT} is already in use. Stop the process using it and retry.")
        sys.exit(1)

    # Start FastAPI server in a single daemon thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for Uvicorn to actually bind the port
    if not wait_for_server("127.0.0.1", APP_PORT):
        print(f"\nERROR: Server did not start on port {APP_PORT}")
        sys.exit(1)

    import webbrowser
    url = f'http://127.0.0.1:{APP_PORT}/?q=high'
    
    print("=" * 60)
    print("  🟢 SERVER STATUS: ONLINE")
    print(f"  🌐 LOCAL URL:     {url}")
    print("  💡 HINT:          Press CTRL+C to shutdown the server")
    print("=" * 60)
    print("\n🚀 Launching interface in your default web browser...\n")
    
    webbrowser.open(url)

    # Keep the main thread alive so the server doesn't die
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down SWARA...")

if __name__ == '__main__':
    start_ui()
