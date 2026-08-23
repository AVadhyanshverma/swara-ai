#!/bin/bash
set -e
echo "1. Installing Rust if missing..."
if ! command -v cargo &> /dev/null; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
fi

echo "2. Ensuring mingw-w64 is installed (requires sudo)..."
if ! command -v x86_64-w64-mingw32-gcc &> /dev/null; then
    echo "Please run: sudo apt install -y mingw-w64"
    exit 1
fi

echo "3. Adding Windows target for Rust..."
rustup target add x86_64-pc-windows-gnu

echo "4. Building Windows binary..."
cargo build --release --target x86_64-pc-windows-gnu

echo "5. Downloading Python standalone (Windows)..."
wget -qO python-embedded-windows.tar.gz https://github.com/astral-sh/python-build-standalone/releases/download/20240107/cpython-3.12.1+20240107-x86_64-pc-windows-msvc-shared-install_only.tar.gz

echo "6. Bundling..."
cat target/x86_64-pc-windows-gnu/release/pyx.exe python-embedded-windows.tar.gz > pyx_windows.exe
echo "Done! Windows executable: pyx_windows.exe"
