import time
import os
import resource
import multiprocessing
from calculator import PerfectCalculator

def set_memory_limit(megabytes):
    """Attempt to limit the memory of the current process."""
    try:
        bytes_limit = megabytes * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (bytes_limit, bytes_limit))
        print(f"Memory limit set to {megabytes} MiB")
    except ValueError as e:
        print(f"Warning: Could not set memory limit to {megabytes} MiB. {e}")
        try:
            bytes_limit = 64 * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (bytes_limit, bytes_limit))
            print(f"Fallback: Memory limit set to 64 MiB")
        except Exception:
            pass

def eval_expr_task(expr):
    calc = PerfectCalculator(precision=50)
    return calc.evaluate(expr)

def battle_test():
    print("\n--- BATTLE TEST & CORRECTNESS ---")
    calc = PerfectCalculator(precision=50)
    
    expr1 = "(45000 + 72000) * 15 - (98000 // 4) * 8 + (35 * 12 * 150) - (84000 // 12) + (6500 - 325) * 4"
    print(f"Expr: {expr1} -> {calc.evaluate(expr1)}")
    
    expr2 = "0.1 + 0.2"
    print(f"Expr: {expr2} -> {calc.evaluate(expr2)}")
    
    expr3 = "(1000000 ** 2) / 3"
    print(f"Expr: {expr3} -> {calc.evaluate(expr3)}")
    
    # New functions & Constants Tests
    expr4 = "max(10, 20) * sin(pi / 2)"
    print(f"Expr: {expr4} -> {calc.evaluate(expr4)}")
    
    expr5 = "sqrt(16) + abs(-10) - log10(100)"
    print(f"Expr: {expr5} -> {calc.evaluate(expr5)}")
    
    # Visual Error Traces Test
    print("\n--- VISUAL ERROR TRACES TEST ---")
    bad_expr = "10 + 5 * (4 - ) + 2"
    try:
        calc.evaluate(bad_expr)
    except Exception as e:
        print("Caught correctly:")
        print(e)
        
    bad_expr2 = "(45000 + 72000) * 15 - (98000 // 4) * 8 + (35 * 12 * 150) - (84000 // 12) + (6500 - 325) * * 4"
    try:
        calc.evaluate(bad_expr2)
    except Exception as e:
        print("\nCaught huge line error correctly:")
        print(e)

def run_single_core_benchmark():
    print("\n--- SINGLE CORE BENCHMARK (32MiB LIMIT) ---")
    set_memory_limit(32)
    
    # We use a mix of functions and heavy math now
    base_expr = "max(10, 20) * sqrt(16) + (45000 + 72000) * 15 - (98000 // 4) * 8"
    large_expr = " + ".join([base_expr] * 100)
    
    calc = PerfectCalculator(precision=50)
    
    print("Running 1000 iterations of a large expression (Regex Tokenizer)...")
    start = time.perf_counter()
    for _ in range(1000):
        calc.evaluate(large_expr)
    end = time.perf_counter()
    
    print(f"Single Core Time taken: {end - start:.4f} seconds")

def run_multi_core_benchmark():
    cores = multiprocessing.cpu_count()
    print(f"\n--- MULTI CORE BENCHMARK ({cores} CORES) ---")
    
    base_expr = "max(10, 20) * sqrt(16) + (45000 + 72000) * 15 - (98000 // 4) * 8"
    large_expr = " + ".join([base_expr] * 100)
    
    print(f"Running 10000 iterations distributed across {cores} cores...")
    start = time.perf_counter()
    
    with multiprocessing.Pool(processes=cores) as pool:
        pool.map(eval_expr_task, [large_expr] * 10000)
        
    end = time.perf_counter()
    print(f"Multi Core Time taken: {end - start:.4f} seconds")

if __name__ == "__main__":
    battle_test()
    
    pid = os.fork()
    if pid == 0:
        try:
            run_single_core_benchmark()
        except MemoryError:
            print("Single Core Benchmark failed due to strict Memory Limit!")
        except Exception as e:
            print(f"Error in single core run: {e}")
        os._exit(0)
    else:
        os.waitpid(pid, 0)
        
    run_multi_core_benchmark()
