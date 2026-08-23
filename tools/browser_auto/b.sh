#!/bin/bash
set -e

echo "🔧 Building Windows portable Playwright MCP..."

rm -rf build win-dist
mkdir -p win-dist

# 1. Clone (reuse existing build folder if you want)
git clone --depth 1 https://github.com/microsoft/playwright-mcp.git build
cd build
npm install
cd ..

# 2. Create Windows portable folder
mkdir -p win-dist/playwright-mcp
cp build/package.json win-dist/playwright-mcp/
cp build/cli.js win-dist/playwright-mcp/
cp build/index.js win-dist/playwright-mcp/
cp -r build/src win-dist/playwright-mcp/
cp -r build/node_modules win-dist/playwright-mcp/

# 3. Download WINDOWS Node binary
echo "📥 Downloading Windows Node 20..."
wget -q -O win-dist/node.zip https://nodejs.org/dist/v20.11.1/node-v20.11.1-win-x64.zip
unzip -q win-dist/node.zip -d win-dist/
mv win-dist/node-v20.11.1-win-x64/node.exe win-dist/playwright-mcp/node.exe
rm -rf win-dist/node.zip win-dist/node-v20.11.1-win-x64

# 4. Create Windows batch file
cat > win-dist/playwright-mcp/run.bat << 'EOF'
@echo off
set DIR=%~dp0
"%DIR%node.exe" "%DIR%cli.js" %*
EOF

# 5. Zip it
cd win-dist
zip -r ../playwright-mcp-windows.zip playwright-mcp/
cd ..

echo ""
echo "=========================================="
echo "  ✅ WINDOWS BUILD COMPLETE!"
echo "=========================================="
ls -lh playwright-mcp-windows.zip
echo ""
echo "📦 Distribute: playwright-mcp-windows.zip"
echo ""
echo "🪟 Windows user instructions:"
echo "   1. Unzip playwright-mcp-windows.zip"
echo "   2. Open CMD in the unzipped folder"
echo "   3. Run: run.bat --headless --browser chromium"