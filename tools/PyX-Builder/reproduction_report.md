# PyX: Portable Python Executor - Reproduction Report

## Workspace Reset
As requested, all old experimental directories (`env_for_python_tool` and `python_interpretor_tool`) have been deleted. 
A brand new, clean directory named **`PyX-Builder`** has been created with a fresh, empty virtual environment (`.venv`).

---

## 1. Project Structure
The `PyX-Builder` directory contains the core framework to build the single-file executable for both Linux and Windows.

```text
PyX-Builder/
├── .venv/                   # The clean, empty virtual environment
├── Cargo.toml               # Rust package manager config
├── src/
│   └── main.rs              # The Rust launcher stub that handles CLI execution
└── scripts/
    ├── build_linux.sh       # Automates downloading Python & building for Linux
    └── build_windows.sh     # Automates cross-compiling for Windows
```

---

## 2. Building for Linux (On this machine)
To build the true single executable for Linux, we compile the Rust launcher, download a portable Python runtime, and combine them into one file.

**Run the script:**
```bash
cd /home/adhyansh/Projects/Reverie/PyX-Builder
./scripts/build_linux.sh
```

**What the script does to reproduce the build:**
1. Installs the Rust compiler locally (if missing).
2. Compiles the `pyx` launcher binary using `cargo build --release`.
3. Downloads the `python-build-standalone` tarball for Linux.
4. Appends the tarball to the compiled binary to create `pyx_linux`.

---

## 3. Cross-Compiling for Windows (From this Linux machine)
Rust allows you to compile Windows `.exe` files directly from Linux using the `mingw-w64` toolchain. 

Because `mingw-w64` modifies system libraries, it requires `sudo` (administrator) privileges to install. I cannot run `sudo` automatically without a password, so you must install the prerequisite first.

**Step 1: Install the Windows Compiler (Run this in your terminal)**
```bash
sudo apt update
sudo apt install -y mingw-w64
```

**Step 2: Run the Build Script**
```bash
cd /home/adhyansh/Projects/Reverie/PyX-Builder
./scripts/build_windows.sh
```

**What the script does to reproduce the Windows build:**
1. Verifies `mingw-w64` is installed.
2. Instructs Rust to download the Windows compiler targets (`rustup target add x86_64-pc-windows-gnu`).
3. Cross-compiles the Rust code into a Windows executable (`pyx.exe`).
4. Downloads the `python-build-standalone` zip for Windows.
5. Appends the Windows Python runtime to the `.exe` to create `pyx_windows.exe`.

---

## 4. How to Inject the "10 Packages"
Once you build the base executables above, they are empty (just the standard library).
To create a version with specific pip packages baked in:

1. **Run the executable and install your packages:**
   ```bash
   ./pyx_linux -m pip install numpy pandas requests flask bs4 ...
   ```
2. **Re-bundle (The `-c` logic):**
   *Note: Full file-IO re-bundling logic must be added to the Rust `src/main.rs` file to scan the cache directory and output a new file, but the architecture to support it is fully scaffolding in this repo.*
