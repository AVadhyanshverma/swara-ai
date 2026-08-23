#!/usr/bin/env python3
"""
Developer Utility: Clean Agent Memory
-------------------------------------
Run this script to completely wipe all chat history, vector database memory, 
and workspaces. Perfect for getting a fresh slate during development!
"""

import shutil
from path_manager import get_base_dir, DEV

def clean_memory():
    # Extra safety check if someone accidentally runs this in PROD
    if not DEV:
        confirm = input("WARNING: You are in PROD mode. This will wipe user data in ~/.SWARA_hackathon. Are you sure? (y/N): ")
        if confirm.lower() != 'y':
            print("Aborted.")
            return

    base_dir = get_base_dir()
    
    dirs_to_remove = [
        base_dir / "agent_workplace",
        base_dir / "chats",
        base_dir / "brain"
    ]
    
    print(f"\n🗑️  Cleaning agent memory in: {base_dir}")
    
    for d in dirs_to_remove:
        if d.exists() and d.is_dir():
            try:
                shutil.rmtree(d)
                print(f"  [✓] Deleted {d.name}/")
            except Exception as e:
                print(f"  [X] Failed to delete {d.name}/: {e}")
        else:
            print(f"  [-] Skipped {d.name}/ (does not exist)")
            
    print("\n✨ All agent memory has been completely wiped! You can start fresh.")

if __name__ == "__main__":
    print("========================================")
    print("      SWARA DEV: MEMORY WIPE TOOL       ")
    print("========================================")
    print("This will PERMANENTLY delete all:")
    print(" - Chat history & SQLite Databases")
    print(" - Vector Databases (Brain)")
    print(" - Agent Workspaces & Mindmaps")
    print("========================================")
    
    confirm = input("Type 'YES' to confirm and wipe everything: ")
    if confirm == "YES":
        clean_memory()
    else:
        print("Aborted. No data was deleted.")
