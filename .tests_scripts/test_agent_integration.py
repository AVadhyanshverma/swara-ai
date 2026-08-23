import sys
import os
import uuid

# Setup paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
from agent_dir.agent import stream_agent_response, chat_engine, agent_app
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

def run_test():
    print("=== TEST 1: Sending math prompt ===")
    thread_id = str(uuid.uuid4())
    print(f"Created Thread ID: {thread_id}")
    
    prompt = r"Find all positive integers n such that n divides 2^n - 1."
    print("User Prompt:", prompt)
    print("\n--- Agent Response Stream ---")
    for chunk in stream_agent_response(prompt, thread_id):
        print(chunk, end="", flush=True)
    print("\n-----------------------------")

    print("\n=== TEST 2: Checking Message History ===")
    state = agent_app.get_state({"configurable": {"thread_id": thread_id}})
    messages = state.values.get("messages", [])
    for m in messages:
        role = "User" if isinstance(m, HumanMessage) else "Assistant" if isinstance(m, AIMessage) else "Tool"
        print(f"[{role}]: {m.content[:50]}...")
        
    print("\n=== TEST 3: Checking Checkpoints in DB ===")
    cursor = chat_engine.conn.cursor()
    cursor.execute("SELECT thread_id, MAX(checkpoint_id) FROM checkpoints GROUP BY thread_id")
    rows = cursor.fetchall()
    print("Threads in DB:")
    for r in rows:
        print(f" - {r[0]} (Last updated: {r[1]})")
        
    print("\n=== TEST 4: Cleaning up thread ===")
    cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
    cursor.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
    chat_engine.conn.commit()
    print("Deleted thread successfully.")

if __name__ == "__main__":
    run_test()
