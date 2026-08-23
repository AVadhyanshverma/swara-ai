import os
import glob

# files to fix:
files_to_fix = [
    "/home/adhyansh/Projects/Reverie/agent_dir/agent.py",
    "/home/adhyansh/Projects/Reverie/agent_dir/model_router.py",
    "/home/adhyansh/Projects/Reverie/agent_dir/tools/document_tools.py",
    "/home/adhyansh/Projects/Reverie/agent_dir/tools/firecrawl_tools.py",
    "/home/adhyansh/Projects/Reverie/ui/main.py",
]

def get_token_code():
    return """
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
"""

for fpath in files_to_fix:
    if not os.path.exists(fpath): continue
    with open(fpath, "r") as f:
        content = f.read()
    
    # 1. Fix api_key="dummy_key_replaced_by_proxy" and api_key="dummy" to api_key=HF_TOKEN
    content = content.replace('api_key="dummy_key_replaced_by_proxy"', 'api_key=HF_TOKEN')
    content = content.replace('api_key="dummy"', 'api_key=HF_TOKEN')
    
    # 2. Fix httpx.post(..., timeout=...) to include headers
    if "httpx.post" in content:
        content = content.replace(
            'httpx.post("https://adhyanshverma-data-gen.hf.space/analyze", data=data, files=files, timeout=120.0)',
            'httpx.post("https://adhyanshverma-data-gen.hf.space/analyze", data=data, files=files, timeout=120.0, headers={"Authorization": f"Bearer {HF_TOKEN}"})'
        )
        content = content.replace(
            'httpx.post("https://adhyanshverma-data-gen.hf.space/analyze", data={"text": combined}, timeout=120.0)',
            'httpx.post("https://adhyanshverma-data-gen.hf.space/analyze", data={"text": combined}, timeout=120.0, headers={"Authorization": f"Bearer {HF_TOKEN}"})'
        )
        
    # Inject token reading at the top (after imports)
    if "HF_TOKEN =" not in content:
        lines = content.split('\n')
        # find last import
        last_import = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                last_import = i
        lines.insert(last_import + 1, get_token_code())
        content = '\n'.join(lines)
        
    with open(fpath, "w") as f:
        f.write(content)
print("Done fixing files!")
