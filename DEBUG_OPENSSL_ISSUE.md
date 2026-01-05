# PyInstaller OpenSSL Issue - Cross-Machine Debugging Guide

## Problem Summary

The viam-qrcode module builds successfully but fails at runtime with an OpenSSL import error:

```
ImportError: dlopen(.../_ssl.cpython-311-darwin.so): Library not loaded: @rpath/libssl.3.dylib
```

**Key Facts:**
- The module works on one MacBook (at office)
- The module fails on another MacBook (current machine)
- Both are building from the same codebase
- The error is in Python's `_ssl` module trying to load OpenSSL libraries
- This happens because opencv-python-headless bundles incompatible OpenSSL

## Root Cause

opencv-python-headless includes its own OpenSSL libraries in `cv2/.dylibs/`, but these are **incompatible** with Python's `_ssl` module. The spec file now:
1. Filters out opencv's OpenSSL
2. Adds the system's OpenSSL that Python expects

But on the failing machine, the OpenSSL libraries aren't being found at runtime even though they're in the bundle.

## Diagnostic Steps

### Step 1: Environment Information

Run this script to collect environment info:

```bash
#!/bin/bash
# save as: collect_env_info.sh

echo "=== SYSTEM INFO ==="
sw_vers
echo ""
echo "Architecture: $(uname -m)"
echo ""

echo "=== PYTHON INFO ==="
which python3
python3 --version
echo ""

echo "=== HOMEBREW INFO ==="
which brew
brew --version
echo ""

echo "=== OPENSSL INFO ==="
ls -la /opt/homebrew/opt/openssl@3/lib/ | grep -E "(libssl|libcrypto)" || echo "Homebrew OpenSSL not found"
echo ""
ls -la /usr/local/opt/openssl@3/lib/ | grep -E "(libssl|libcrypto)" || echo "Local OpenSSL not found"
echo ""

echo "=== PYTHON OPENSSL LINKAGE ==="
if [ -f /opt/homebrew/Cellar/python@3.11/*/Frameworks/Python.framework/Versions/3.11/lib/python3.11/lib-dynload/_ssl.cpython-311-darwin.so ]; then
    SSL_FILE=$(ls /opt/homebrew/Cellar/python@3.11/*/Frameworks/Python.framework/Versions/3.11/lib/python3.11/lib-dynload/_ssl.cpython-311-darwin.so | head -1)
    echo "Found _ssl.so at: $SSL_FILE"
    otool -L "$SSL_FILE" | grep -E "(libssl|libcrypto)"
else
    echo "_ssl.so not found in expected location"
fi
echo ""

echo "=== VENV INFO ==="
if [ -d ".venv" ]; then
    echo "Virtual environment exists"
    source .venv/bin/activate
    python --version
    pip list | grep -E "(opencv|pyzbar|viam)"
    deactivate
else
    echo "No .venv found"
fi
echo ""

echo "=== OPENCV OPENSSL ==="
if [ -d ".venv/lib/python3.11/site-packages/cv2/.dylibs" ]; then
    ls -la .venv/lib/python3.11/site-packages/cv2/.dylibs/ | grep -E "(libssl|libcrypto)"
else
    echo "opencv .dylibs directory not found"
fi
```

**ACTION:** Run this on BOTH machines and compare the output.

### Step 2: Test Current Build

On each machine:

```bash
cd /path/to/viam-qrcode
source .venv/bin/activate

# Rebuild
./build.sh

# Try to run
./dist/main --help 2>&1 | head -30
```

**Questions to answer:**
- Does it fail immediately or succeed?
- If it fails, what's the exact error message?
- If it succeeds, continue to Step 3

### Step 3: Inspect the Built Binary

```bash
#!/bin/bash
# save as: inspect_binary.sh

echo "=== BINARY SIZE ==="
ls -lh dist/main
echo ""

echo "=== STRINGS CHECK - OpenSSL References ==="
strings dist/main | grep -i "libssl" | head -10
strings dist/main | grep -i "libcrypto" | head -10
echo ""

echo "=== ARCHIVE CONTENTS ==="
cd dist
tar -tzf archive.tar.gz | head -20
echo "..."
tar -tzf archive.tar.gz | grep -E "(libssl|libcrypto)"
cd ..
echo ""

echo "=== OTOOL CHECK - Binary Dependencies ==="
otool -L dist/main | head -20
```

**ACTION:** Compare the outputs between machines. Look for:
- Are the OpenSSL libraries in the archive?
- What dependencies does the binary have?

### Step 4: Runtime Extraction Test

```bash
#!/bin/bash
# save as: test_extraction.sh

echo "=== TESTING RUNTIME EXTRACTION ==="

# Create a test script that pauses before SSL import
cat > test_early_exit.py << 'EOF'
import sys
import os

# This should work - before ssl import
print(f"Python version: {sys.version}")
print(f"Executable: {sys.executable}")

# Check temp directory
import tempfile
temp_base = tempfile.gettempdir()
print(f"Temp directory: {temp_base}")

# List _MEI directories
mei_dirs = [d for d in os.listdir(temp_base) if d.startswith('_MEI')]
print(f"Found {len(mei_dirs)} _MEI directories")

if mei_dirs:
    mei_path = os.path.join(temp_base, mei_dirs[0])
    print(f"Latest _MEI: {mei_path}")

    # Check for libssl/libcrypto
    for root, dirs, files in os.walk(mei_path):
        for f in files:
            if 'libssl' in f or 'libcrypto' in f:
                full_path = os.path.join(root, f)
                print(f"Found OpenSSL lib: {full_path}")

# Now try to import ssl
print("\nAttempting to import ssl...")
try:
    import ssl
    print("SUCCESS: ssl module imported")
    print(f"SSL version: {ssl.OPENSSL_VERSION}")
except ImportError as e:
    print(f"FAILED: {e}")
    sys.exit(1)
EOF

# Temporarily modify src/__main__.py to run our test
cp src/__main__.py src/__main__.py.backup
cp test_early_exit.py src/__main__.py

# Rebuild with test
./build.sh > /dev/null 2>&1

# Run test
echo ""
./dist/main 2>&1

# Restore original
mv src/__main__.py.backup src/__main__.py
rm test_early_exit.py
```

**ACTION:** This will show if OpenSSL libraries are actually being extracted to the temp directory.

### Step 5: PyInstaller Version Check

```bash
source .venv/bin/activate
pip show pyinstaller
pyinstaller --version
```

**ACTION:** Compare PyInstaller versions between machines.

### Step 6: Compare Spec File Execution

```bash
source .venv/bin/activate
./build.sh 2>&1 | tee build_log.txt

# Check these sections in build_log.txt:
grep -A5 "Filtering opencv" build_log.txt
grep -A5 "hook-ssl" build_log.txt
grep "OpenSSL libraries in final binaries" build_log.txt
```

**ACTION:** Compare build logs. The "OpenSSL libraries in final binaries" section should show 2 entries on both machines.

## What to Look For

### On the WORKING machine, you should see:
- OpenSSL libraries successfully extracted to `_MEI` temp directory
- `ssl` module imports successfully
- The binary runs without errors

### On the FAILING machine, you should see:
- OpenSSL libraries might not be in `_MEI` directory
- OR they're there but not being found by dlopen
- OR they have the wrong permissions/signatures

## Potential Differences to Check

1. **macOS Version**: Different OS versions handle code signing differently
2. **Python Installation**: Homebrew vs python.org vs pyenv
3. **OpenSSL Location**: Different Homebrew installations
4. **Security Settings**: Gatekeeper, SIP, code signing policies
5. **File System**: Case sensitivity, APFS vs HFS+
6. **Architecture**: Intel (x86_64) vs Apple Silicon (arm64)

## Quick Comparison Checklist

| Check | Working Machine | Failing Machine |
|-------|----------------|-----------------|
| macOS Version | | |
| Architecture (uname -m) | | |
| Python 3.11 location | | |
| OpenSSL location | | |
| PyInstaller version | | |
| opencv-python-headless version | | |
| Binary size | | |
| OpenSSL in archive? | | |
| `otool -L` on _ssl.so | | |

## Files to Check

The fix involves these files:
- `main.spec` - PyInstaller spec with OpenSSL filtering
- `build.sh` - Build script
- `hook-ssl.py` - Custom PyInstaller hook (may not be needed)

## Expected Behavior

After the fix, the build should:
1. Remove opencv's OpenSSL (from cv2/.dylibs/)
2. Add system OpenSSL (from Homebrew)
3. Print during build:
   ```
   Filtering opencv OpenSSL and adding system OpenSSL:
     Removed opencv OpenSSL: 2 binaries, 0 datas
     Added system OpenSSL: /opt/homebrew/opt/openssl@3/lib/libssl.3.dylib as libssl.3.dylib
     Added system OpenSSL: /opt/homebrew/opt/openssl@3/lib/libcrypto.3.dylib as libcrypto.3.dylib
   OpenSSL libraries in final binaries list: 2
     - libssl.3.dylib -> /opt/homebrew/opt/openssl@3/lib/libssl.3.dylib
     - libcrypto.3.dylib -> /opt/homebrew/opt/openssl@3/lib/libcrypto.3.dylib
   ```

## Questions for Claude on the Working Machine

1. Run all diagnostic scripts and share the output
2. Check if there are any differences in file permissions
3. Try: `codesign -dv ./dist/main` on both machines
4. Check: `otool -l ./dist/main | grep -A5 LC_RPATH`
5. Verify: Are there any security/quarantine extended attributes? `xattr ./dist/main`

## Next Steps

Once you've collected diagnostic info from both machines, the key differences should reveal:
- Why OpenSSL loads on one machine but not the other
- Whether it's a build-time or runtime issue
- If code signing or security policies are involved
- If the OpenSSL libraries are incompatible between machines

Share the comparison results and we can identify the specific fix needed.
