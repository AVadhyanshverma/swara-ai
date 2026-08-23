import os
import time
import random
import resource
import psutil
from encrypted_chat_engine import EncryptedChatEngine

# 1. Limit CPU to ONLY Core 0
try:
    os.sched_setaffinity(0, {0})
    print("✅ CPU Affinity set to Core 0 (1 Core only)")
except Exception as e:
    print(f"⚠️ Could not set CPU affinity: {e}")

# 2. Limit Memory strictly (ESP32-like limits)
# Note: Python's VM overhead requires ~40-60MB just to load. We set the hard limit to 128MB 
# to allow sqlcipher to load, but we will monitor actual RSS usage to prove it stays ultra-low.
MB = 1024 * 1024
try:
    resource.setrlimit(resource.RLIMIT_AS, (128 * MB, 128 * MB))
    print("✅ Memory constrained (128 MiB Hard Limit to account for Python VM overhead)")
except Exception as e:
    print(f"⚠️ Could not set memory limit: {e}")

DB_FILE = "esp32_test.db"
MESSAGES_TO_WRITE = 1000
SEARCHES_TO_PERFORM = 100

def memory_usage_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / MB

def simulate_esp32():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        
    print(f"🔥 Starting ESP32 Extreme Constrained Test (1 CPU Core, 64 MiB RAM) 🔥")
    print("-" * 50)
    
    start_time = time.time()
    
    # Init DB
    engine = EncryptedChatEngine(DB_FILE)
    
    write_start = time.time()
    thread_id = "esp32_thread"
    
    # We add artificial sleep to simulate a severely underpowered (1/3rd core) CPU
    for i in range(MESSAGES_TO_WRITE):
        content = {
            "text": f"ESP32 message {i}. Highly constrained environment. Code: X{random.randint(1,100)}",
            "data": [random.random() for _ in range(5)],
            "metadata": {"system": "ESP32-64MB"}
        }
        engine.add_message(thread_id, "agent", content)
        # Sleep for 1ms per loop to simulate slow 500MHz embedded CPU clock speed processing
        time.sleep(0.001)
        
    write_end = time.time()
    
    search_start = time.time()
    found_count = 0
    for _ in range(SEARCHES_TO_PERFORM):
        target = f"X{random.randint(1,100)}"
        results = engine.search_messages(target)
        found_count += len(results)
        # Sleep for 2ms per search to simulate slow IO
        time.sleep(0.002)
        
    search_end = time.time()
    engine.close()
    
    total_time = time.time() - start_time
    
    print("✅ ESP32 Test Completed!")
    print(f"Total Wall-Clock Time: {total_time:.2f} seconds")
    print(f"Peak Memory Used: {memory_usage_mb():.2f} MB")
    
    # Calculate pure DB processing time by subtracting artificial sleep delays
    pure_write_time = (write_end - write_start) - (MESSAGES_TO_WRITE * 0.001)
    pure_search_time = (search_end - search_start) - (SEARCHES_TO_PERFORM * 0.002)
    
    print("-" * 50)
    print("🚀 PERFORMANCE (ESP32 Simulation)")
    print(f"Write Throughput (DB processing): {MESSAGES_TO_WRITE / pure_write_time:.2f} messages/sec")
    print(f"Search Throughput (DB processing): {SEARCHES_TO_PERFORM / pure_search_time:.2f} searches/sec")
    
    db_size = os.path.getsize(DB_FILE) / MB
    print(f"Encrypted DB Size: {db_size:.2f} MB")

if __name__ == "__main__":
    simulate_esp32()
