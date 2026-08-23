import json
from calculator import PerfectCalculator
from step_calculator import PerfectStepCalculator

# Initialize shared instances
fast_calc = PerfectCalculator(precision=50)
step_calc = PerfectStepCalculator(precision=50)

def solve_math_fast(expression: str) -> str:
    """Evaluates a math expression and returns just the final numerical answer. Fast and exact."""
    try:
        return str(fast_calc.evaluate(expression))
    except Exception as e:
        return f"Error: {str(e)}"

def solve_math_steps(expression: str) -> str:
    """Evaluates a math expression and returns the step-by-step working and final answer as a JSON payload."""
    try:
        result = step_calc.evaluate(expression)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

def grade_student_math(expression: str, student_steps: list) -> str:
    """Grades a student's step-by-step math working against the correct sequence. Returns a grading report JSON."""
    try:
        result = step_calc.mark_student(expression, student_steps)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


# ==========================================
# UNIVERSAL AI TOOL SCHEMAS (OpenAI Format)
# ==========================================
MATH_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "solve_math_fast",
            "description": "Evaluates a mathematical expression safely with high precision. Returns the exact final result. Use this when you need calculations fast.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression. Example: 'max(10, 20) * sin(pi / 2)'"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "solve_math_steps",
            "description": "Evaluates a mathematical expression and returns the step-by-step chronological operations in JSON format. Excellent for generating 'show your working' text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The expression to evaluate step-by-step."
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "grade_student_math",
            "description": "Grades a student's multi-step mathematical working. Identifies exact locations where errors were made.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The original question the student is trying to solve."
                    },
                    "student_steps": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "An array of equations showing the student's steps. Example: ['45000 + 72000 = 117000', '117000 * 15 = 1755000']"
                    }
                },
                "required": ["expression", "student_steps"]
            }
        }
    }
]

# LangChain wrappers
try:
    from langchain.tools import tool
    
    @tool
    def langchain_solve_math_fast(expression: str) -> str:
        """Evaluates a mathematical expression and returns the exact numerical answer."""
        return solve_math_fast(expression)
        
    @tool
    def langchain_solve_math_steps(expression: str) -> str:
        """Evaluates a mathematical expression and returns the chronological step-by-step working as JSON."""
        return solve_math_steps(expression)
        
    @tool
    def langchain_grade_student_math(expression: str, student_steps: list) -> str:
        """Grades a student's step-by-step mathematical working."""
        return grade_student_math(expression, student_steps)
        
except ImportError:
    pass
