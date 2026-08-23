import subprocess
import sys
import os
import argparse
import logging

# Configure basic logging for the main launcher
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SwaraLauncher")

BANNER = r"""
==================================================================
  ___                                   _  _____ 
 / __> _ _ _  ___  _ _  ___     /\     | |<__   >
 \__ \| | | |/ ._>| '_><_> |   /  \  _ | |  /  / 
 <___/|__/_/ \___.|_|  <___|  /__/_\<_\__| /__/  
                                                 
          Advanced Autonomous Agent Framework
==================================================================
"""

def run_ui():
    print(BANNER)
    logger.info("Initializing Swara AI Web UI...")
    logger.info("Preparing FastAPI server and local tool endpoints...")
    
    try:
        logger.info("Starting UI server internally...")
        import ui.main
        ui.main.start_ui()
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt. Shutting down UI gracefully.")
    except Exception as e:
        logger.error(f"Failed to start UI: {e}")

def run_terminal():
    print(BANNER)
    logger.info("Initializing Swara AI Terminal CLI...")
    print("Type 'quit' or 'exit' to stop interacting.\n")
    
    try:
        from agent_dir.agent import stream_agent_response
    except ImportError as e:
        logger.error(f"Failed to import agent modules: {e}")
        return

    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.strip().lower() in ['quit', 'exit']:
                logger.info("Exiting Swara AI Terminal. Goodbye!")
                break
            if not user_input.strip():
                continue
            
            print("Agent: ", end="", flush=True)
            for chunk in stream_agent_response(user_input):
                print(chunk, end="", flush=True)
            print()
        except KeyboardInterrupt:
            print()
            logger.info("Session interrupted by user.")
            break
        except EOFError:
            break
        except Exception as e:
            logger.error(f"Error during interaction: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Swara AI Agent Launcher")
    parser.add_argument(
        "--cli", 
        action="store_true", 
        help="Launch the Terminal CLI instead of the Web UI"
    )
    args = parser.parse_args()

    if args.cli:
        run_terminal()
    else:
        # Default to UI per user request: "make that the ui while we run the cmd must launch..."
        run_ui()
