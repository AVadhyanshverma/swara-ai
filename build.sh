#!/bin/bash

# SwaraAI Build Script

set -e

echo "========================================"
echo "    Starting SwaraAI Build Process      "
echo "========================================"

# Step 1: Check for virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment found."
fi

# Step 2: Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Step 3: Upgrade pip and install requirements
echo "Installing dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 4: Ensure pyinstaller is installed
echo "Checking PyInstaller..."
pip install pyinstaller

# Step 5: Run the PyInstaller build
echo "Running PyInstaller with build.spec..."
pyinstaller build.spec --clean -y

echo "========================================"
echo "    Build completed successfully!       "
echo "    Executable is in the dist/ folder.  "
echo "========================================"
