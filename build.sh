#!/bin/bash
set -e

# Activate virtual environment
source .venv/bin/activate

# Platform check - only support ARM Mac and Linux
if [ "$(uname -s)" = "Darwin" ] && [ ! -d "/opt/homebrew" ]; then
    echo "ERROR: Intel Mac (x86_64) is not supported. Only Apple Silicon (ARM64) is supported."
    echo "This build requires /opt/homebrew which is only available on ARM Macs."
    exit 1
fi

# Clean previous builds
rm -rf dist build

# Build with PyInstaller (using directory mode for better library management)
# Using --collect-all for packages that need their full package structure
pyinstaller --onedir \
    --hidden-import=pyzbar.pyzbar \
    --hidden-import=pyzbar.wrapper \
    --collect-all=pyzbar \
    --collect-all=cv2 \
    --collect-all=google.protobuf \
    --collect-all=grpclib \
    --collect-all=viam \
    --name=main \
    src/__main__.py

# Remove OpenCV's bundled SSL/crypto libraries to avoid compatibility issues
# OpenCV bundles SSL libraries that may be incompatible with Python's _ssl module
if [ -d "dist/main/_internal/cv2/.dylibs" ]; then
    echo "Removing OpenCV's bundled SSL libraries..."
    rm -f dist/main/_internal/cv2/.dylibs/libssl*.dylib
    rm -f dist/main/_internal/cv2/.dylibs/libcrypto*.dylib

    # Dynamically find the correct SSL libraries that Python's _ssl module uses
    if [ "$(uname -s)" = "Darwin" ]; then
        # Find Python's _ssl.so and determine which OpenSSL it links to
        PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        SSL_SO=$(python -c "import _ssl; import os; print(os.path.dirname(_ssl.__file__))")/_ssl.cpython-*-darwin.so

        if [ -f $SSL_SO ]; then
            echo "Found _ssl.so at: $SSL_SO"
            # Use otool to find which OpenSSL libraries _ssl.so links to
            SSL_LIB=$(otool -L $SSL_SO | grep libssl | awk '{print $1}')
            CRYPTO_LIB=$(otool -L $SSL_SO | grep libcrypto | awk '{print $1}')

            if [ -f "$SSL_LIB" ] && [ -f "$CRYPTO_LIB" ]; then
                cp "$SSL_LIB" dist/main/_internal/cv2/.dylibs/
                cp "$CRYPTO_LIB" dist/main/_internal/cv2/.dylibs/
                echo "✓ Copied Python's OpenSSL libraries:"
                echo "  - $SSL_LIB"
                echo "  - $CRYPTO_LIB"
            else
                echo "ERROR: Could not find OpenSSL libraries at:"
                echo "  SSL: $SSL_LIB"
                echo "  Crypto: $CRYPTO_LIB"
                exit 1
            fi
        else
            echo "ERROR: Could not find _ssl.so for Python $PYTHON_VERSION"
            exit 1
        fi
    elif [ "$(uname -s)" = "Linux" ]; then
        # On Linux, use ldd to find SSL libraries
        SSL_SO=$(python -c "import _ssl; print(_ssl.__file__)")
        SSL_LIB=$(ldd "$SSL_SO" | grep libssl.so | awk '{print $3}')
        CRYPTO_LIB=$(ldd "$SSL_SO" | grep libcrypto.so | awk '{print $3}')

        if [ -f "$SSL_LIB" ] && [ -f "$CRYPTO_LIB" ]; then
            cp "$SSL_LIB" dist/main/_internal/cv2/.dylibs/
            cp "$CRYPTO_LIB" dist/main/_internal/cv2/.dylibs/
            echo "✓ Copied system SSL libraries for Linux"
        else
            echo "ERROR: Could not find SSL libraries"
            exit 1
        fi
    fi
fi

# Copy meta.json for packaging
cp meta.json dist/

# Create the archive with dist/main structure to match entrypoint
tar -czf dist/archive.tar.gz -C . dist/main meta.json

echo "Build complete! Archive created at dist/archive.tar.gz"
