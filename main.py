import subprocess
import sys
import os

def run_ui():
    print("Starting LangGraph UI Agent...")
    ui_path = os.path.join(os.path.dirname(__file__), "ui", "main.py")
    
    try:
        subprocess.run([sys.executable, ui_path])
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Failed to start UI: {e}")

def run_terminal():
    print("Starting LangGraph Terminal Agent... (Type 'quit' or 'exit' to stop)")
    try:
        from agent_dir.agent import stream_agent_response
    except ImportError as e:
        print(f"Failed to import agent: {e}")
        return

    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.strip().lower() in ['quit', 'exit']:
                break
            if not user_input.strip():
                continue
            
            print("Agent: ", end="", flush=True)
            for chunk in stream_agent_response(user_input):
                print(chunk, end="", flush=True)
            print()
        except KeyboardInterrupt:
            break
        except EOFError:
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    # Temporarily disconnected the UI server
    # run_ui()
    run_terminal()
