"""
PyInstaller hook to include OpenSSL libraries required by Python's _ssl module.
This hook dynamically finds the OpenSSL libraries that _ssl depends on.
"""
from PyInstaller.utils.hooks import get_module_file_attribute
from PyInstaller.compat import is_darwin, is_linux
import subprocess
import os

# Initialize all hook variables at module level (required by PyInstaller)
binaries = []
datas = []
hiddenimports = []

# Find the _ssl module
ssl_file = get_module_file_attribute('_ssl')

if ssl_file and os.path.exists(ssl_file):
    if is_darwin:
        # Use otool on macOS to find OpenSSL dependencies
        try:
            result = subprocess.run(['otool', '-L', ssl_file],
                                  capture_output=True, text=True, check=True)
            for line in result.stdout.split('\n'):
                if 'libssl' in line or 'libcrypto' in line:
                    # Extract the library path (first column after tab)
                    lib_path = line.strip().split()[0]
                    if os.path.exists(lib_path):
                        # Add the library with its basename as destination
                        binaries.append((lib_path, '.'))
                        print(f"hook-ssl: Adding OpenSSL library: {lib_path}")
        except Exception as e:
            print(f"hook-ssl WARNING: Could not determine OpenSSL dependencies: {e}")

    elif is_linux:
        # Use ldd on Linux to find OpenSSL dependencies
        try:
            result = subprocess.run(['ldd', ssl_file],
                                  capture_output=True, text=True, check=True)
            for line in result.stdout.split('\n'):
                if 'libssl' in line or 'libcrypto' in line:
                    # Extract the library path (format: "libssl.so.3 => /path/to/lib (0x...)")
                    parts = line.split('=>')
                    if len(parts) > 1:
                        lib_path = parts[1].strip().split()[0]
                        if os.path.exists(lib_path):
                            binaries.append((lib_path, '.'))
                            print(f"hook-ssl: Adding OpenSSL library: {lib_path}")
        except Exception as e:
            print(f"hook-ssl WARNING: Could not determine OpenSSL dependencies: {e}")

print(f"hook-ssl: Collected {len(binaries)} OpenSSL libraries")
