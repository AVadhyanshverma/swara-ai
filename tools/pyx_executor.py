#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os

PYX_BIN = "/home/adhyansh/Projects/SWARA/PyX-Builder/pyx_linux"

def execute_with_pyx(filepath=None, code=None, script_args=[]):
    if not os.path.exists(PYX_BIN):
        print(f"Error: {PYX_BIN} not found.")
        sys.exit(1)
        
    cmd = [PYX_BIN]
    
    if filepath:
        cmd.append(filepath)
    elif code:
        cmd.extend(["-c", code])
    
    if script_args:
        cmd.extend(script_args)
    
    print(f"Executing: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("--- OUTPUT ---")
        print(result.stdout)
        if result.stderr:
            print("--- STDERR ---")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Execution failed with exit code {e.returncode}")
        print("--- OUTPUT ---")
        print(e.stdout)
        print("--- STDERR ---")
        print(e.stderr)
        sys.exit(e.returncode)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent Tool to execute Python code via PyX portable executable.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-f", "--file", help="Path to Python file to execute")
    group.add_argument("-c", "--code", help="Inline Python code to execute")
    parser.add_argument("script_args", nargs=argparse.REMAINDER, help="Arguments to pass to the script")
    
    args = parser.parse_args()
    execute_with_pyx(args.file, args.code, args.script_args)
