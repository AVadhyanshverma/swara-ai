import os
import time
import json
import glob
from tools.chat_his.encrypted_chat_engine import EncryptedChatEngine

DATASET_DIR = "/run/media/adhyansh/EFC6-61EA/datasets/code"
DB_PATH = os.path.join(DATASET_DIR, "chat_history.db")

def process_kimi_workflows():
    print(f"Initializing EncryptedChatEngine at: {DB_PATH}")
    engine = EncryptedChatEngine(DB_PATH)
    
    # Find all Kimi_Workflow directories
    search_pattern = os.path.join(DATASET_DIR, "Kimi_Workflow_*")
    directories = glob.glob(search_pattern)
    
    print(f"Found {len(directories)} 'Kimi_Workflow' directories.")
    
    start_time = time.time()
    total_messages = 0
    
    for d in directories:
        workflow_path = os.path.join(d, "workflow.json")
        if not os.path.exists(workflow_path):
            continue
            
        thread_id = os.path.basename(d)
        
        try:
            with open(workflow_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            for item in data:
                # `role` could map to `type` in the workflow item
                role = item.get("type", "unknown")
                engine.add_message(
                    thread_id=thread_id,
                    role=role,
                    content=item,
                    metadata={"source_dir": d}
                )
                total_messages += 1
                
        except Exception as e:
            print(f"Error processing {workflow_path}: {e}")

    end_time = time.time()
    elapsed = end_time - start_time
    
    engine.close()
    
    print("-" * 50)
    print("✅ PROCESSING COMPLETE")
    print(f"Total Workflows Processed: {len(directories)}")
    print(f"Total Chat Messages Stored: {total_messages}")
    print(f"Total Time Taken: {elapsed:.3f} seconds")
    print(f"Throughput: {total_messages / elapsed:.2f} messages/second")
    print("-" * 50)

if __name__ == "__main__":
    process_kimi_workflows()
