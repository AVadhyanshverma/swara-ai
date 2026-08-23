import os
from datetime import datetime
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import ToolNode
import sys

# Add chat_his directory to import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.chat_his.encrypted_chat_engine import EncryptedChatEngine

try:
    from path_manager import get_chats_dir
    chats_dir = get_chats_dir()
    os.makedirs(chats_dir, exist_ok=True)
    db_path = os.path.join(chats_dir, "SWARA_chats.db")
except ImportError:
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools", "chat_his", "SWARA_chats.db"))

chat_engine = EncryptedChatEngine(db_path=db_path)

from .tools_system import available_tools

# Load system prompt template
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.txt")

class State(TypedDict):
    messages: Annotated[list, add_messages]

def build_agent():
    from .model_router import MODEL_REGISTRY, route_message
    
    # Use the dynamically loaded tools with proper schemas
    tools = available_tools
    
    # Instantiate all our specialized models
    models = {}
    for task_type, model_id in set([(k, v) for k, v in MODEL_REGISTRY.items() if k != "router"]):
        llm = ChatOpenAI(
            base_url="https://adhyanshverma-data-gen.hf.space/v1",
            api_key="ge",
            model=model_id,
            streaming=True
        )
        models[task_type] = llm.bind_tools(tools) if tools else llm
        
    # We also need to map the keys so `models[task_type]` works safely
    # (e.g. if 'chat' and 'math' share the same model, we just point to the same instance)
    llm_map = {}
    for task_type, model_id in MODEL_REGISTRY.items():
        if task_type != "router":
            llm_map[task_type] = models[task_type]
    
    def estimate_tokens(text: str) -> int:
        """Rough token estimate: ~4 chars per token for English text."""
        return len(text) // 4 if text else 0

    def truncate_tool_messages(messages: list, max_tool_chars: int = 100000) -> list:
        """Truncate ToolMessage content that is too large before sending to LLM."""
        from langchain_core.messages import ToolMessage as TM
        truncated = []
        for msg in messages:
            if isinstance(msg, TM) and msg.content and len(str(msg.content)) > max_tool_chars:
                content_str = str(msg.content)[:max_tool_chars] + "\n\n...[TRUNCATED to fit 32K token budget. Please optimize your tool query to return less data.]"
                new_msg = TM(content=content_str, tool_call_id=msg.tool_call_id, name=msg.name)
                truncated.append(new_msg)
            else:
                truncated.append(msg)
        return truncated

    def chatbot(state: State, config):
        task_type = "chat"
        last_msg = state["messages"][-1]
        
        if isinstance(last_msg, HumanMessage):
            task_type = route_message(str(last_msg.content))
        else:
            # Tool loop: retrieve the task type assigned to the previous AIMessage
            for m in reversed(state["messages"]):
                if hasattr(m, "response_metadata") and m.response_metadata and "model_task_type" in m.response_metadata:
                    task_type = m.response_metadata["model_task_type"]
                    break
        selected_llm = llm_map.get(task_type, llm_map["chat"])
        
        # Load specific prompt based on task type
        prompt_file = f"{task_type}_prompt.txt"
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", prompt_file)
        if not os.path.exists(prompt_path):
            prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.txt")
            
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
        
        # Auto replace current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sys_prompt_content = prompt_template.replace("{current_time}", current_time)
        
        try:
            cursor = chat_engine.conn.cursor()
            cursor.execute("SELECT name, dob, ai_persona FROM user_profile LIMIT 1")
            row = cursor.fetchone()
            if row:
                name, dob, persona = row
                sys_prompt_content += f"\n\n[USER PROFILE]\nUser Name: {name}\nUser DOB: {dob}\nRequested AI Persona/Vibe: {persona}\nPlease strictly adhere to the requested AI persona in your interactions."
        except Exception:
            pass
        
        # Build message list
        conversation_messages = list(state["messages"])
        
        # Step 1: Truncate any oversized tool result messages
        conversation_messages = truncate_tool_messages(conversation_messages, max_tool_chars=100000)
        
        # Step 2: Prepend system message
        memory_sys_msg = None
        if isinstance(last_msg, HumanMessage):
            from agent_dir.tools.memory_tools import memory_search
            import json
            try:
                search_res_str = memory_search.invoke({"query": str(last_msg.content)})
                search_res = json.loads(search_res_str)
                if search_res.get("status") == "success":
                    context_strs = []
                    for r in search_res.get("results", []):
                        if r.get("score", 0) > 0.7:
                            context_strs.append(f"Memory (Score: {r['score']}): {r['text']}")
                    if context_strs:
                        mem_context = "\n".join(context_strs)
                        memory_sys_msg = SystemMessage(content=f"[LONG-TERM MEMORY CONTEXT]\n{mem_context}")
            except Exception:
                pass

        messages = [SystemMessage(content=sys_prompt_content)]
        if memory_sys_msg:
            messages.append(memory_sys_msg)
        messages.extend(conversation_messages)
        
        # Step 3: Estimate total token count and aggressively trim if over budget
        # We limit the input to 24,000 tokens so that the combination of input (24K) + output response (e.g. 8K)
        # safely fits within a 32K strict context window limit.
        MAX_INPUT_TOKENS = 24000
        total_tokens = sum(estimate_tokens(str(m.content)) for m in messages)
        
        while total_tokens > MAX_INPUT_TOKENS and len(messages) > 3:
            removed = messages.pop(1)
            total_tokens -= estimate_tokens(str(removed.content))
        
        if total_tokens > MAX_INPUT_TOKENS:
            for i in range(1, len(messages)):
                content = str(messages[i].content)
                if len(content) > 100000:
                    messages[i].content = content[:100000] + "\n\n...[HARD TRUNCATED]"
            
        # Add a custom tag so UI knows which model is handling it (can be intercepted by streamer)
        response = selected_llm.invoke(messages, config=config)
        # We append the model name to the response's response_metadata so the streamer can access it
        if not response.response_metadata:
            response.response_metadata = {}
        response.response_metadata["model_task_type"] = task_type
        response.response_metadata["model_name"] = MODEL_REGISTRY.get(task_type)
        return {"messages": [response]}
        
    def should_continue(state: State):
        last_message = state["messages"][-1]
        # If the LLM makes a tool call, route to the "tools" node
        if last_message.tool_calls:
            return "tools"
        # Otherwise, we are done
        return END

    graph_builder = StateGraph(State)
    graph_builder.add_node("chatbot", chatbot)
    
    # Add a tool node that executes the requested tool if tools exist
    if tools:
        tool_node = ToolNode(tools=tools)
        graph_builder.add_node("tools", tool_node)
        
        graph_builder.add_edge(START, "chatbot")
        graph_builder.add_conditional_edges("chatbot", should_continue)
        graph_builder.add_edge("tools", "chatbot")
    else:
        graph_builder.add_edge(START, "chatbot")
        graph_builder.add_edge("chatbot", END)
        
    memory = chat_engine.get_langgraph_checkpointer()
    return graph_builder.compile(checkpointer=memory)

# Global instance for the FastAPI app to use
agent_app = build_agent()

from langchain_core.messages import AIMessageChunk, AIMessage, ToolMessage, HumanMessage, SystemMessage

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


def stream_agent_response(user_input: str, thread_id: str = "main_thread"):
    from .model_router import route_message, MODEL_REGISTRY
    
    config = {"configurable": {"thread_id": thread_id}}
    try:
        # Determine the model proactively so we can inform the user instantly
        task_type = route_message(user_input)
        model_name = MODEL_REGISTRY.get(task_type, MODEL_REGISTRY["chat"])
        yield f"**[Model: {model_name}]**\n\n"
        
        for msg, metadata in agent_app.stream(
            {"messages": [HumanMessage(content=user_input)]},
            stream_mode="messages",
            config=config
        ):
            # Yield LLM text generation
            if not isinstance(msg, ToolMessage) and not isinstance(msg, HumanMessage):
                if isinstance(msg.content, str) and msg.content:
                    yield msg.content
                elif isinstance(msg.content, list):
                    for block in msg.content:
                        if isinstance(block, str):
                            yield block
                        elif isinstance(block, dict) and block.get("type") == "text" and block.get("text"):
                            yield block.get("text")
                
            # Detect when the LLM starts a tool call
            if hasattr(msg, "tool_call_chunks") and msg.tool_call_chunks:
                for chunk in msg.tool_call_chunks:
                    if chunk.get("name"):
                        yield f"\n<think>\n⏳ Preparing tool: {chunk['name']}...\n</think>\n"
                        
            # Yield completed tool calls (before execution)
            if hasattr(msg, "tool_calls") and msg.tool_calls and not isinstance(msg, AIMessageChunk):
                for tc in msg.tool_calls:
                    tc_id = tc.get('id', 'unknown')
                    tc_name = tc.get('name', 'unknown')
                    tc_args = tc.get('args', {})
                    import json
                    try:
                        tc_args_str = "```json\n" + json.dumps(tc_args, indent=2) + "\n```"
                    except:
                        tc_args_str = "```python\n" + str(tc_args) + "\n```"
                    yield f"\n<think>\n🚀 tool_call name: {tc_name}\nid: {tc_id}\nArguments:\n{tc_args_str}\n</think>\n"
                    
            # Yield tool results after execution
            if isinstance(msg, ToolMessage):
                content_str = str(msg.content)
                import json
                try:
                    parsed = json.loads(content_str)
                    content_str = "```json\n" + json.dumps(parsed, indent=2) + "\n```"
                except Exception:
                    # If it's not JSON, we don't necessarily want to wrap it in json, but maybe just a generic code block if it's long.
                    pass
                tc_id = msg.tool_call_id if hasattr(msg, 'tool_call_id') else 'unknown'
                yield f"\n<think>\n✅ tool_call_results id: {tc_id}\nResult:\n{content_str}\n</think>\n"
                
        # After streaming completes, check if we need to summarize
        state = agent_app.get_state(config)
        all_msgs = state.values.get("messages", [])
        human_msgs = [m for m in all_msgs if isinstance(m, HumanMessage)]
        
        if len(human_msgs) % 5 == 0 and len(human_msgs) > 0:
            def background_summarize(all_msgs_copy, human_count, tid):
                try:
                    print(f"\n[BACKGROUND] 🧠 {human_count} messages reached. Summarizing and smartly chunking recent context to Vector DB...")
                    recent_msgs = all_msgs_copy[-15:]
                    text_to_summarize = "\n".join([f"{type(m).__name__}: {str(m.content)[:1000]}" for m in recent_msgs])
                    
                    summary_llm = ChatOpenAI(
                        base_url="https://adhyanshverma-data-gen.hf.space/v1",
                        api_key=HF_TOKEN,
                        model="deepseek-ai/DeepSeek-V4-Flash-0731"
                    )
                    prompt = f"Summarize the following recent conversation into a dense, highly informative summary. Do NOT exceed 500 words. Focus strictly on facts, user preferences, and decisions made that would be useful for long-term memory retrieval:\n\n{text_to_summarize}"
                    summary_response = summary_llm.invoke([HumanMessage(content=prompt)])
                    
                    from agent_dir.tools.memory_tools import memory_store
                    import json
                    metadata = json.dumps({"source": "auto_summarization", "msg_count": human_count, "thread_id": tid})
                    memory_store.invoke({"text": summary_response.content, "metadata_json": metadata})
                    print(f"[BACKGROUND] ✅ Summarized context successfully stored in Vector DB for thread {tid}!")
                except Exception as e:
                    print(f"[BACKGROUND Error] Failed to summarize: {e}")
                    
            import threading
            threading.Thread(target=background_summarize, args=(list(all_msgs), len(human_msgs), thread_id), daemon=True).start()
            
    except Exception as e:
        yield f"\n\n*[System Error: Agent execution stopped due to: {str(e)}]*\n\n"
