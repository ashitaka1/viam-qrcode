#!/bin/bash
# Script to inspect the built binary for OpenSSL libraries

if [ ! -f "dist/main" ]; then
    echo "Error: dist/main not found. Run ./build.sh first."
    exit 1
fi

echo "=== BINARY SIZE ==="
ls -lh dist/main
echo ""

echo "=== BINARY INFO ==="
file dist/main
echo ""

echo "=== CODE SIGNATURE ==="
codesign -dv dist/main 2>&1 || echo "Not code signed"
echo ""

echo "=== RPATHS ==="
otool -l dist/main | grep -A5 LC_RPATH || echo "No RPATHs found"
echo ""

echo "=== EXTENDED ATTRIBUTES (quarantine, etc) ==="
xattr dist/main 2>/dev/null || echo "No extended attributes"
echo ""

echo "=== STRINGS CHECK - OpenSSL References ==="
echo "libssl references:"
strings dist/main | grep -i "libssl" | head -10
echo ""
echo "libcrypto references:"
strings dist/main | grep -i "libcrypto" | head -10
echo ""

echo "=== ARCHIVE CONTENTS ==="
if [ -f "dist/archive.tar.gz" ]; then
    echo "First 20 files:"
    tar -tzf dist/archive.tar.gz | head -20
    echo "..."
    echo ""
    echo "OpenSSL libraries in archive:"
    tar -tzf dist/archive.tar.gz | grep -E "(libssl|libcrypto)" || echo "  None found"
else
    echo "archive.tar.gz not found"
fi
echo ""

echo "=== OTOOL CHECK - Binary Dependencies ==="
otool -L dist/main | head -20
