#!/bin/bash
# Script to test if OpenSSL libraries are extracted at runtime

echo "=== TESTING RUNTIME EXTRACTION ==="
echo "This will temporarily modify src/__main__.py to test extraction"
echo ""

# Backup original
if [ ! -f "src/__main__.py.backup" ]; then
    cp src/__main__.py src/__main__.py.backup
fi

# Create test script
cat > src/__main__.py << 'EOF'
import sys
import os

print("=== RUNTIME DIAGNOSTIC ===")
print(f"Python version: {sys.version}")
print(f"Executable: {sys.executable}")
print("")

# Check temp directory
import tempfile
temp_base = tempfile.gettempdir()
print(f"Temp directory: {temp_base}")

# List _MEI directories
try:
    mei_dirs = [d for d in os.listdir(temp_base) if d.startswith('_MEI')]
    print(f"Found {len(mei_dirs)} _MEI directories")

    if mei_dirs:
        # Sort by modification time to get latest
        mei_paths = [os.path.join(temp_base, d) for d in mei_dirs]
        mei_paths.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        mei_path = mei_paths[0]

        print(f"\nLatest _MEI: {mei_path}")
        print(f"Contents:")

        # Walk and find OpenSSL
        ssl_libs = []
        for root, dirs, files in os.walk(mei_path):
            for f in files:
                if 'libssl' in f or 'libcrypto' in f:
                    full_path = os.path.join(root, f)
                    ssl_libs.append(full_path)
                    rel_path = os.path.relpath(full_path, mei_path)
                    size = os.path.getsize(full_path)
                    print(f"  Found: {rel_path} ({size:,} bytes)")

        if not ssl_libs:
            print("  WARNING: No OpenSSL libraries found in _MEI directory!")
        else:
            print(f"\n  Total OpenSSL libraries: {len(ssl_libs)}")
    else:
        print("WARNING: No _MEI directories found!")
except Exception as e:
    print(f"ERROR scanning temp directory: {e}")

print("\n=== ATTEMPTING SSL IMPORT ===")
try:
    import ssl
    print("✓ SUCCESS: ssl module imported")
    print(f"  OpenSSL version: {ssl.OPENSSL_VERSION}")
    print(f"  OpenSSL version info: {ssl.OPENSSL_VERSION_INFO}")
except ImportError as e:
    print(f"✗ FAILED: {e}")
    print("\nThis indicates the OpenSSL libraries are either:")
    print("  1. Not in the bundle")
    print("  2. In the bundle but not extracted")
    print("  3. Extracted but not found by the dynamic linker")
    sys.exit(1)

print("\n=== TEST COMPLETE ===")
EOF

echo "Building with test script..."
source .venv/bin/activate
./build.sh > /dev/null 2>&1

echo ""
echo "Running test..."
echo "==============================================="
./dist/main 2>&1
EXIT_CODE=$?
echo "==============================================="
echo ""

# Restore original
mv src/__main__.py.backup src/__main__.py

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Test PASSED - OpenSSL is working"
else
    echo "✗ Test FAILED - OpenSSL import failed"
fi

exit $EXIT_CODE
