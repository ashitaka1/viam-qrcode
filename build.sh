#!/bin/bash
set -e

# Activate virtual environment
source .venv/bin/activate

# Clean previous builds
rm -rf dist build

# Build with PyInstaller
# Using --collect-all for packages that need their full package structure
pyinstaller --onefile \
    --hidden-import=pyzbar.pyzbar \
    --hidden-import=pyzbar.wrapper \
    --collect-all=pyzbar \
    --collect-all=cv2 \
    --collect-all=google.protobuf \
    --collect-all=grpclib \
    --collect-all=viam \
    --name=main \
    src/__main__.py

# Create the archive
cd dist
tar -czf archive.tar.gz main
cd ..

echo "Build complete! Archive created at dist/archive.tar.gz"
