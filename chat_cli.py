import sys
import os
import uuid

# Add current dir to path to import agent_dir
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from agent_dir.agent import stream_agent_response

def main():
    print("========================================")
    print("       SWARA Terminal Chat CLI        ")
    print("========================================")
    print("Type 'exit' or 'quit' to stop.")
    
    # Generate a new thread ID for this session
    thread_id = str(uuid.uuid4())
    print(f"[Session Thread ID: {thread_id}]\n")
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
            if not user_input.strip():
                continue
                
            print("\nAgent: ", end="", flush=True)
            # Stream the response directly to the terminal
            for chunk in stream_agent_response(user_input, thread_id):
                print(chunk, end="", flush=True)
            print("\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()
