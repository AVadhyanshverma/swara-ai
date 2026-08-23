import time
from step_calculator import PerfectStepCalculator

def battle_test():
    calc = PerfectStepCalculator(precision=50)
    
    expr = "(45000 + 72000) * 15 - (98000 // 4) * 8 + (35 * 12 * 150) - (84000 // 12) + (6500 - 325) * 4"
    print("\n--- 1. AST STEP EVALUATION ---")
    report = calc.evaluate(expr)
    for s in report["steps"]:
        print(f"Step {s['step_num']}: {s['expression']} = {s['result']} (+{s['marks']})")
    print(f"Final Answer: {report['final_answer']}")
    
    print("\n--- 2. AST STUDENT GRADING ---")
    student = [
        "45000 + 72000 = 117000",
        "117000 * 15 = 1755000",
        "98000 // 4 = 25000",      # incorrect, should be 24500
        "35 * 12 = 420",
    ]
    graded = calc.mark_student(expr, student)
    for s in graded["student_marked_steps"]:
        print(f"[{s['status'].upper()}] Step {s['step']}: {s['feedback']}")
    print(f"Score: {graded['earned_marks']}/{graded['total_possible']} ({graded['percentage']}%)")

def run_benchmarks():
    from calculator import PerfectCalculator
    fast_c = PerfectCalculator()
    step_c = PerfectStepCalculator()
    
    # Large mathematical workload
    base_expr = "max(10, 20) * sqrt(16) + (45000 + 72000) * 15 - (98000 // 4) * 8"
    large_expr = " + ".join([base_expr] * 20)
    
    print("\n--- 3. PERFORMANCE BENCHMARK (1,000 iterations) ---")
    
    start = time.perf_counter()
    for _ in range(1000):
        fast_c.evaluate(large_expr)
    end = time.perf_counter()
    print(f"Direct Evaluation Time: {end-start:.4f}s")
    
    start = time.perf_counter()
    for _ in range(1000):
        step_c.evaluate(large_expr)
    end = time.perf_counter()
    print(f"AST Step Generation Time: {end-start:.4f}s")

if __name__ == '__main__':
    battle_test()
    run_benchmarks()
