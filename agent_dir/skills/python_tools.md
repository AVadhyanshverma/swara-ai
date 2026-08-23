# Python Execution Skill

## Tools
- `execute_python_with_pyx(code: str)`

## Usage Instructions
This tool allows you to safely execute arbitrary Python code using a portable PyX binary. It returns both STDOUT and STDERR.

1. **`execute_python_with_pyx`**:
   - `code`: The raw Python code to execute.
   
**Example Uses:**
- Running calculations or data processing scripts.
- Testing small Python snippets.
- Formatting or transforming data that is too complex for an LLM to do accurately by itself.

*Note: The code runs with a 15-second timeout.*
