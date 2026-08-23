import os
import time
from memory_engine import MemoryEngine

def main():
    file_path = "/home/adhyansh/Projects/SWARA/bulck.txt"
    
    # Check if file exists, if not create a massive dummy bulk file
    if not os.path.exists(file_path):
        print(f"File {file_path} not found. Generating a 50,000 word dummy file...")
        with open(file_path, "w") as f:
            for _ in range(5000):
                f.write("The quick brown fox jumps over the lazy dog. ")
    
    print("========================================")
    print("  INITIALIZING DYNAMIC MEMORY ENGINE    ")
    print("========================================")
    try:
        # Dynamically scale resources to fit inside: 512MB RAM & 30% total CPU usage
        engine = MemoryEngine(max_memory_mb=512, max_cpu_percent=0.30)
        
        print(f"\nStarting chunked stream processing for {file_path}...")
        start = time.time()
        
        # We no longer hardcode batch_size. The engine calculates the optimal batch 
        # dynamically based on the 512MB constraint!
        engine.add_file(file_path, chunk_size=200, overlap=50)
        
        end = time.time()
        print(f"Finished completely in {end - start:.2f} seconds.")
        
    except MemoryError:
        print("\n[CRITICAL ERROR] Python ran out of memory!")
    except Exception as e:
        print(f"\n[ERROR] Process failed: {e}")

if __name__ == "__main__":
    main()
