#!/bin/bash
set -e
echo "1. Installing Rust if missing..."
if ! command -v cargo &> /dev/null; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
fi

echo "2. Building Linux binary..."
cargo build --release

echo "3. Downloading Python standalone (Linux)..."
wget -qO python-embedded-linux.tar.gz https://github.com/astral-sh/python-build-standalone/releases/download/20240107/cpython-3.12.1+20240107-x86_64-unknown-linux-gnu-install_only.tar.gz

echo "4. Bundling..."
cat target/release/pyx python-embedded-linux.tar.gz > pyx_linux
chmod +x pyx_linux
echo "Done! Run: ./pyx_linux"
