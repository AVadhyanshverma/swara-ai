import os
import time
import random
import resource
import psutil
from concurrent.futures import ProcessPoolExecutor
from encrypted_chat_engine import EncryptedChatEngine

# Set memory limit to ~1GB (1024 * 1024 * 1024 bytes) for this process
# Note: In a multiprocessing environment, this applies per process. 
# We'll rely on the DB engine being memory-efficient natively.
DB_FILE = "battle_test.db"
NUM_WORKERS = 20
MESSAGES_PER_WORKER = 500  # Total 10,000 messages
SEARCHES_PER_WORKER = 50   # Total 1,000 searches

def memory_usage_mb():
    """Returns memory usage of current process in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def worker_task(worker_id):
    """Simulates an agent spamming messages and searching"""
    engine = EncryptedChatEngine(DB_FILE)
    
    # 1. Heavy Write Phase
    write_start = time.time()
    thread_id = f"stress_thread_{worker_id}"
    
    for i in range(MESSAGES_PER_WORKER):
        # Generate some payload
        content = {
            "text": f"Agent {worker_id} says hello {i}! The secret word is BATTLE{random.randint(1, 100)}.",
            "data": [random.random() for _ in range(50)],
            "metadata": {"iteration": i, "status": "testing"}
        }
        engine.add_message(thread_id, "agent", content)
        
    write_end = time.time()
    
    # 2. Heavy Read/Search Phase (utilizing the JSON index)
    search_start = time.time()
    found_count = 0
    for _ in range(SEARCHES_PER_WORKER):
        target = f"BATTLE{random.randint(1, 100)}"
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

def run_battle_test():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        
    print(f"🔥 Starting Battle Test on {DB_FILE} 🔥")
    print(f"Cores: {NUM_WORKERS} (2000% CPU capacity simulation)")
    print(f"Target: {NUM_WORKERS * MESSAGES_PER_WORKER} total encrypted JSON insertions")
    print(f"Target: {NUM_WORKERS * SEARCHES_PER_WORKER} total JSON text searches")
    print("-" * 50)
    
    start_time = time.time()
    
    # Pre-initialize DB to create tables to avoid race conditions on schema creation
    engine = EncryptedChatEngine(DB_FILE)
    engine.close()
    
    results = []
    # Utilize 20 CPU cores
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = [executor.submit(worker_task, i) for i in range(NUM_WORKERS)]
        for future in futures:
            results.append(future.result())
            
    total_time = time.time() - start_time
    
    # Analyze results
    total_write_time = sum(r["write_time"] for r in results)
    total_search_time = sum(r["search_time"] for r in results)
    avg_mem = sum(r["mem_mb"] for r in results) / len(results)
    total_found = sum(r["found"] for r in results)
    
    print("✅ Battle Test Completed!")
    print(f"Total Wall-Clock Time: {total_time:.2f} seconds")
    print(f"Total CPU Time utilized across workers (Approx): {total_write_time + total_search_time:.2f} seconds")
    print(f"Average Memory per Worker: {avg_mem:.2f} MB")
    print(f"Total Overall Memory (Approx): {avg_mem * NUM_WORKERS:.2f} MB")
    
    print("-" * 50)
    print("🚀 PERFORMANCE METRICS")
    print(f"Write Throughput: {(NUM_WORKERS * MESSAGES_PER_WORKER) / total_time:.2f} messages/sec (encrypted JSON)")
    print(f"Search Throughput: {(NUM_WORKERS * SEARCHES_PER_WORKER) / total_time:.2f} searches/sec (full DB JSON expression scan)")
    print(f"Total matching messages found during search phase: {total_found}")
    
    db_size_mb = os.path.getsize(DB_FILE) / (1024 * 1024)
    print(f"Encrypted Database Size: {db_size_mb:.2f} MB")
    
if __name__ == "__main__":
    run_battle_test()
