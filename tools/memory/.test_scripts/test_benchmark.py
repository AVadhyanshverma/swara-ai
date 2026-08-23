import time
import json
from memory_engine import MemoryEngine

def run_calibration():
    print("Initializing Agent Hardware Calibration...")
    # Initialize without constraints to test raw hardware limits
    engine = MemoryEngine()
    
    base_text = "The quick brown fox jumps over the lazy dog. "
    
    # 1. Warmup Phase (CRITICAL)
    # The ONNX ML model has a heavy "first-run" penalty while it loads weights into RAM.
    # We run a tiny payload first so it doesn't skew our benchmark.
    engine.add_document(base_text * 10, batch_size=2)
    
    # 2. Calibration Phase 
    # 1,000 words is large enough to get a mathematically accurate speed average, 
    # but small enough that even a 1-core machine will finish it in ~30 seconds, 
    # while a fast machine finishes in ~1.5 seconds.
    target_words = 1000
    test_text = base_text * (target_words // 9)
    actual_words = len(test_text.split())
    
    start = time.time()
    engine.add_document(test_text)
    end = time.time()
    
    duration = end - start
    words_per_sec = int(actual_words / duration)
    
    # Output raw JSON so an AI Agent can easily parse it
    result = {
        "hardware_profile": "unknown",
        "words_per_second": words_per_sec,
        "test_duration_seconds": round(duration, 2),
        "total_words_tested": actual_words
    }
    
    print("\n--- AGENT CALIBRATION RESULTS ---")
    print(json.dumps(result, indent=2))
    print("---------------------------------")
    print("Agent Decision Logic Suggestion:")
    print("If words_per_second < 100: Offload to Background Queue / External API")
    print("If words_per_second > 100: Process locally via MemoryEngine")

if __name__ == "__main__":
    run_calibration()
