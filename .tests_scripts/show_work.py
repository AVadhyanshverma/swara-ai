import sys
import os
import uuid
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
from agent_dir.agent import agent_app
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

def show_work():
    thread_id = str(uuid.uuid4())
    prompt = r"Find all positive integers n such that n divides 2^n - 1."
    
    print("Running agent...")
    # Run the graph and collect all messages
    agent_app.invoke({"messages": [HumanMessage(content=prompt)]}, config={"configurable": {"thread_id": thread_id}})
    
    state = agent_app.get_state({"configurable": {"thread_id": thread_id}})
    messages = state.values.get("messages", [])
    
    for m in messages:
        if isinstance(m, AIMessage) and m.tool_calls:
            for tc in m.tool_calls:
                print(f"\n--- 🛠️ Agent wrote Python Code ({tc['name']}) ---")
                # The arguments usually contain 'code' or similar
                print(json.dumps(tc['args'], indent=2))
        elif isinstance(m, ToolMessage):
            print(f"\n--- 💻 Output of the Python Code ---")
            print(m.content)

if __name__ == "__main__":
    show_work()
