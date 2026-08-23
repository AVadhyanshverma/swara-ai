#!/bin/bash
set -e

echo "🔧 Building self-extracting Playwright MCP..."
rm -rf build dist
mkdir -p dist

# 1. Clone
git clone --depth 1 https://github.com/microsoft/playwright-mcp.git build
cd build
npm install
cd ..

# 2. Create portable folder — copy ONLY what's needed
mkdir -p dist/playwright-mcp
cp build/package.json dist/playwright-mcp/
cp build/cli.js dist/playwright-mcp/
cp build/index.js dist/playwright-mcp/
cp -r build/src dist/playwright-mcp/
cp -r build/node_modules dist/playwright-mcp/

# 3. Download portable Node binary (no install, just extract)
echo "📥 Downloading portable Node 20..."
wget -q -O dist/node.tar.xz https://nodejs.org/dist/v20.11.1/node-v20.11.1-linux-x64.tar.xz
tar -xf dist/node.tar.xz -C dist/
mv dist/node-v20.11.1-linux-x64/bin/node dist/playwright-mcp/node
rm -rf dist/node.tar.xz dist/node-v20.11.1-linux-x64

# 4. Build self-extracting script
echo "📦 Packing into single file..."
cat > dist/playwright-mcp.run << 'SCRIPT'
#!/bin/bash
set -e
TMPDIR=$(mktemp -d /tmp/playwright-mcp-XXXXXX)
START=$(awk '/^__ARCHIVE_BELOW__/ {print NR + 1; exit 0;}' "$0")
tail -n +$START "$0" | tar -xJ -C "$TMPDIR"
"$TMPDIR/playwright-mcp/node" "$TMPDIR/playwright-mcp/cli.js" "$@"
rm -rf "$TMPDIR"
exit 0
__ARCHIVE_BELOW__
SCRIPT

tar -cJf - -C dist playwright-mcp >> dist/playwright-mcp.run
chmod +x dist/playwright-mcp.run

# 5. Done
echo ""
echo "=========================================="
echo "  ✅ BUILD COMPLETE!"
echo "=========================================="
ls -lh dist/playwright-mcp.run
echo ""
echo "🚀 Test it now:"
echo "   ./dist/playwright-mcp.run --help"
echo ""
echo "📦 Distribute this ONE file. It runs on any Linux with zero dependencies."