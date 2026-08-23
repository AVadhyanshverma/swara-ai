from sqlcipher3 import dbapi2 as sqlite
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

def my_node(state: State):
    return {"messages": [{"role": "assistant", "content": "hello from assistant!"}]}

key = "testkey123"
conn = sqlite.connect("test_langgraph.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute(f"PRAGMA key = '{key}';")

saver = SqliteSaver(conn)

# Build graph
builder = StateGraph(State)
builder.add_node("my_node", my_node)
builder.add_edge(START, "my_node")
builder.add_edge("my_node", END)
graph = builder.compile(checkpointer=saver)

config = {"configurable": {"thread_id": "1"}}
print(graph.invoke({"messages": [{"role": "user", "content": "hi"}]}, config))

# Verify it was saved
print(saver.get_tuple(config))
conn.close()
