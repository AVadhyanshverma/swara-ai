import os
import time
import random
import resource
import psutil
from concurrent.futures import ProcessPoolExecutor
from encrypted_chat_engine import EncryptedChatEngine

# 1. Limit CPU to ONLY Core 0
try:
    os.sched_setaffinity(0, {0})
    print("✅ CPU Affinity set to Core 0 (1 Core only)")
except Exception as e:
    print(f"⚠️ Could not set CPU affinity: {e}")

# 2. Limit Memory strictly to 1 GB
GB = 1024 * 1024 * 1024
try:
    resource.setrlimit(resource.RLIMIT_AS, (GB, GB))
    print("✅ Memory strictly constrained to 1 GB")
except Exception as e:
    print(f"⚠️ Could not set memory limit: {e}")

DB_FILE = "constrained_test.db"
# We will use 4 workers, but they will all be forced to share the single CPU core
NUM_WORKERS = 4
MESSAGES_PER_WORKER = 2500  # Total 10,000 messages
SEARCHES_PER_WORKER = 250   # Total 1,000 searches

def memory_usage_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def worker_task(worker_id):
    # Workers inherit CPU affinity and Memory limits from parent process in Linux
    engine = EncryptedChatEngine(DB_FILE)
    
    write_start = time.time()
    thread_id = f"constrained_thread_{worker_id}"
    
    for i in range(MESSAGES_PER_WORKER):
        content = {
            "text": f"Agent {worker_id} message {i} on a tiny 1-core machine. Code: X{random.randint(1,100)}",
            "data": [random.random() for _ in range(20)],
            "metadata": {"system": "1GB-1Core"}
        }
        engine.add_message(thread_id, "agent", content)
        
    write_end = time.time()
    
    search_start = time.time()
    found_count = 0
    for _ in range(SEARCHES_PER_WORKER):
        target = f"X{random.randint(1,100)}"
        results = engine.search_messages(target)
        found_count += len(results)
        
    search_end = time.time()
    engine.close()
    
    return {
        "worker_id": worker_id,
        "write_time": write_end - write_start,
        "search_time": search_end - search_start,
        "mem_mb": memory_usage_mb(),
        "found": found_count
    }

def run_test():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        
    print(f"🔥 Starting Constrained Test (1 CPU Core, 1 GB RAM) 🔥")
    print("-" * 50)
    
    start_time = time.time()
    
    # Pre-init schema
    engine = EncryptedChatEngine(DB_FILE)
    engine.close()
    
    results = []
    # 4 agents fighting over 1 CPU core
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = [executor.submit(worker_task, i) for i in range(NUM_WORKERS)]
        for future in futures:
            results.append(future.result())
            
    total_time = time.time() - start_time
    
    total_write_time = sum(r["write_time"] for r in results)
    total_search_time = sum(r["search_time"] for r in results)
    avg_mem = sum(r["mem_mb"] for r in results) / len(results)
    
    print("✅ Constrained Test Completed!")
    print(f"Total Wall-Clock Time: {total_time:.2f} seconds")
    print(f"Avg Memory per Worker: {avg_mem:.2f} MB")
    
    print("-" * 50)
    print("🚀 PERFORMANCE (1 CORE)")
    print(f"Write Throughput: {(NUM_WORKERS * MESSAGES_PER_WORKER) / total_time:.2f} messages/sec")
    print(f"Search Throughput: {(NUM_WORKERS * SEARCHES_PER_WORKER) / total_time:.2f} searches/sec")
    
    db_size = os.path.getsize(DB_FILE) / (1024 * 1024)
    print(f"Encrypted DB Size: {db_size:.2f} MB")

if __name__ == "__main__":
    run_test()
