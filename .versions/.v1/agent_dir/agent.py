import os
from datetime import datetime
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import ToolNode

from .tools_system import available_tools

# Load system prompt template
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.txt")

class State(TypedDict):
    messages: Annotated[list, add_messages]

def build_agent():
    llm = ChatOpenAI(
        base_url="http://localhost:8000/v1",
        api_key="dummy_key_replaced_by_proxy",
        model="deepseek-ai/DeepSeek-V4-Flash-0731",
        streaming=True
    )
    
    # Use the dynamically loaded tools with proper schemas
    tools = available_tools
    llm_with_tools = llm.bind_tools(tools) if tools else llm
    
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
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            prompt_template = f.read()
        
        # Auto replace current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sys_prompt_content = prompt_template.replace("{current_time}", current_time)
        
        # Build message list
        conversation_messages = list(state["messages"])
        
        # Step 1: Truncate any oversized tool result messages
        conversation_messages = truncate_tool_messages(conversation_messages, max_tool_chars=100000)
        
        # Step 2: Prepend system message
        messages = [SystemMessage(content=sys_prompt_content)] + conversation_messages
        
        # Step 3: Estimate total token count and aggressively trim if over budget
        # Budget: 32K total - 4K reserved for output = 28K input max
        MAX_INPUT_TOKENS = 26000
        
        total_tokens = sum(estimate_tokens(str(m.content)) for m in messages)
        
        # If over budget, keep system prompt + trim from oldest (keep last N)
        while total_tokens > MAX_INPUT_TOKENS and len(messages) > 3:
            # Remove the second message (oldest after system prompt)
            removed = messages.pop(1)
            total_tokens -= estimate_tokens(str(removed.content))
        
        # Final safety: if still over, hard-truncate the largest message contents
        if total_tokens > MAX_INPUT_TOKENS:
            for i in range(1, len(messages)):
                content = str(messages[i].content)
                if len(content) > 100000:
                    messages[i].content = content[:100000] + "\n\n...[HARD TRUNCATED - token budget exceeded]"
            
        response = llm_with_tools.invoke(messages, config=config)
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
        
    from langgraph.checkpoint.memory import MemorySaver
    memory = MemorySaver()
    return graph_builder.compile(checkpointer=memory)

# Global instance for the FastAPI app to use
agent_app = build_agent()

from langchain_core.messages import AIMessageChunk, AIMessage, ToolMessage, HumanMessage, SystemMessage

def stream_agent_response(user_input: str):
    config = {"configurable": {"thread_id": "main_thread"}}
    try:
        for msg, metadata in agent_app.stream(
            {"messages": [HumanMessage(content=user_input)]},
            stream_mode="messages",
            config=config
        ):
            # Yield LLM text generation
            if msg.content and isinstance(msg.content, str) and not isinstance(msg, ToolMessage) and not isinstance(msg, HumanMessage):
                yield msg.content
                
            # Detect when the LLM starts a tool call
            if hasattr(msg, "tool_call_chunks") and msg.tool_call_chunks:
                for chunk in msg.tool_call_chunks:
                    if chunk.get("name"):
                        yield f"\n<think>\n⏳ Preparing tool: {chunk['name']}...\n</think>\n"
                        
            # Yield completed tool calls (before execution)
            if hasattr(msg, "tool_calls") and msg.tool_calls and not isinstance(msg, AIMessageChunk):
                for tc in msg.tool_calls:
                    yield f"\n<think>\n🚀 Executing Tool: {tc['name']}\nArguments: {tc.get('args', {})}\n</think>\n"
                    
            # Yield tool results after execution
            if isinstance(msg, ToolMessage):
                content_str = str(msg.content)
                yield f"\n<think>\n✅ Tool Completed: {msg.name}\nResult:\n{content_str}\n</think>\n"
                
        # After streaming completes, check if we need to summarize
        state = agent_app.get_state(config)
        all_msgs = state.values.get("messages", [])
        human_msgs = [m for m in all_msgs if isinstance(m, HumanMessage)]
        
        if len(human_msgs) % 5 == 0 and len(human_msgs) > 0:
            yield "\n<think>\n🧠 5 messages reached. Summarizing and smartly chunking recent context to Vector DB...\n</think>\n"
            
            # Grab recent context
            recent_msgs = all_msgs[-15:]
            text_to_summarize = "\n".join([f"{type(m).__name__}: {str(m.content)[:1000]}" for m in recent_msgs])
            
            summary_llm = ChatOpenAI(
                base_url="http://localhost:8000/v1",
                api_key="dummy",
                model="deepseek-ai/DeepSeek-V4-Flash-0731"
            )
            prompt = f"Summarize the following recent conversation into a dense, highly informative summary. Do NOT exceed 500 words. Focus strictly on facts, user preferences, and decisions made that would be useful for long-term memory retrieval:\n\n{text_to_summarize}"
            
            summary_response = summary_llm.invoke([HumanMessage(content=prompt)])
            
            # Store in Vector DB
            from .tools_system import memory_store
            import json
            metadata = json.dumps({"source": "auto_summarization", "msg_count": len(human_msgs)})
            memory_store.invoke({"text": summary_response.content, "metadata_json": metadata})
            
            yield "\n<think>\n✅ Summarized context successfully stored in Vector DB!\n</think>\n"
            
    except Exception as e:
        yield f"\n\n*[System Error: Agent execution stopped due to: {str(e)}]*\n\n"
