#!/bin/bash
# Diagnostic script to collect environment information for OpenSSL debugging

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
echo "Homebrew OpenSSL (Apple Silicon):"
ls -la /opt/homebrew/opt/openssl@3/lib/ 2>/dev/null | grep -E "(libssl|libcrypto)" || echo "  Not found"
echo ""
echo "Homebrew OpenSSL (Intel):"
ls -la /usr/local/opt/openssl@3/lib/ 2>/dev/null | grep -E "(libssl|libcrypto)" || echo "  Not found"
echo ""

echo "=== PYTHON OPENSSL LINKAGE ==="
# Try to find _ssl.so in multiple locations
SSL_FILE=""
for path in /opt/homebrew/Cellar/python@3.11/*/Frameworks/Python.framework/Versions/3.11/lib/python3.11/lib-dynload/_ssl.cpython-311-darwin.so /usr/local/Cellar/python@3.11/*/Frameworks/Python.framework/Versions/3.11/lib/python3.11/lib-dynload/_ssl.cpython-311-darwin.so; do
    if [ -f "$path" ]; then
        SSL_FILE="$path"
        break
    fi
done

if [ -n "$SSL_FILE" ]; then
    echo "Found _ssl.so at: $SSL_FILE"
    echo "OpenSSL dependencies:"
    otool -L "$SSL_FILE" | grep -E "(libssl|libcrypto)" || echo "  None found"
else
    echo "_ssl.so not found in expected locations"
    echo "Searching for _ssl.so..."
    find /opt/homebrew/Cellar/python@3.11 /usr/local/Cellar/python@3.11 -name "_ssl.cpython-311-darwin.so" 2>/dev/null | head -1
fi
echo ""

echo "=== VENV INFO ==="
if [ -d ".venv" ]; then
    echo "Virtual environment exists"
    source .venv/bin/activate
    echo "Python in venv: $(which python)"
    python --version
    echo ""
    echo "Key packages:"
    pip list | grep -E "(opencv|pyzbar|viam|PyInstaller)"
    deactivate
else
    echo "No .venv found in current directory"
fi
echo ""

echo "=== OPENCV OPENSSL ==="
if [ -d ".venv/lib/python3.11/site-packages/cv2/.dylibs" ]; then
    echo "opencv-python-headless OpenSSL libraries:"
    ls -la .venv/lib/python3.11/site-packages/cv2/.dylibs/ | grep -E "(libssl|libcrypto)"
else
    echo "opencv .dylibs directory not found"
fi
echo ""

echo "=== PYINSTALLER VERSION ==="
if [ -d ".venv" ]; then
    source .venv/bin/activate
    pip show pyinstaller | grep Version
    deactivate
fi
