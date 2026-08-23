from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

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


MODEL_REGISTRY = {
    "router": "deepseek-ai/DeepSeek-V4-Flash-0731",
    "chat": "deepseek-ai/DeepSeek-V4-Flash-0731",
    "research": "moonshotai/Kimi-K2.6",
    "code": "zai-org/GLM-5.2",
    "math": "moonshotai/Kimi-K2.6",
    "browser": "moonshotai/Kimi-K2.6",
}

def route_message(user_input: str) -> str:
    """Classifies the user intent into one of the known categories."""
    try:
        router_llm = ChatOpenAI(
            base_url="https://adhyanshverma-data-gen.hf.space/v1",
            api_key=HF_TOKEN,
            model=MODEL_REGISTRY["router"],
            max_tokens=150
        )
        prompt = (
            "Classify this user message into exactly one category:\n"
            "- 'chat' (casual conversation, greetings, simple questions)\n"
            "- 'research' (web search needed, reading articles, comparing data, real-time info)\n"
            "- 'code' (write code, debug, explain code, refactor)\n"
            "- 'math' (calculations, equations, step-by-step math)\n"
            "- 'browser' (navigate web, fill forms, automate browser tasks)\n\n"
            "Reply with ONLY the category word in lowercase (e.g., chat, research, code, math, browser).\n\n"
            f"User message: {user_input}"
        )
        response = router_llm.invoke([HumanMessage(content=prompt)], config={"callbacks": []})
        content = str(response.content)
        
        # Remove <think> blocks if present (DeepSeek specific)
        import re
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        
        # Extract the last valid category word
        category = "chat"
        words = content.lower().split()
        for word in reversed(words):
            import string
            clean_word = word.translate(str.maketrans('', '', string.punctuation))
            if clean_word in MODEL_REGISTRY:
                category = clean_word
                break
                
        return category
    except Exception:
        return "chat"

def get_model_for_task(task_type: str) -> str:
    return MODEL_REGISTRY.get(task_type, MODEL_REGISTRY["chat"])
