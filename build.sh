#!/bin/bash
set -e

# Activate virtual environment
source .venv/bin/activate

# Clean previous builds
rm -rf dist build

# Build with PyInstaller using the custom spec file
# The spec file handles OpenSSL compatibility issues and package collection
pyinstaller main.spec

# Create the archive
cd dist
tar -czf archive.tar.gz main
cd ..

echo "Build complete! Archive created at dist/archive.tar.gz"
