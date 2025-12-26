#!/bin/bash
set -e

UNAME=$(uname -s)

if [ "$UNAME" = "Linux" ]
then
    echo "Installing dependencies for Linux"
    sudo apt-get install -y libzbar0
fi

if [ "$UNAME" = "Darwin" ]
then
    echo "Installing dependencies for macOS"
    brew install zbar
fi

# Setup Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip3 install --upgrade pip
pip3 install -r requirements.txt
pip3 install pyinstaller
