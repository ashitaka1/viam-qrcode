# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs, collect_data_files, collect_submodules, get_module_file_attribute

datas = []
binaries = []
hiddenimports = ['pyzbar.pyzbar', 'pyzbar.wrapper']

# Collect pyzbar
tmp_ret = collect_all('pyzbar')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Collect cv2 - but exclude its bundled OpenSSL (incompatible with Python's _ssl)
cv2_datas = collect_data_files('cv2')
cv2_bins = collect_dynamic_libs('cv2')
cv2_imports = collect_submodules('cv2')
# Filter out opencv's bundled OpenSSL from BOTH data files and binaries
cv2_datas_filtered = [(src, dest) for src, dest in cv2_datas
                       if not ('libssl' in src or 'libcrypto' in src)]
cv2_bins_filtered = [(src, dest) for src, dest in cv2_bins
                      if not ('libssl' in src or 'libcrypto' in src)]
datas += cv2_datas_filtered
binaries += cv2_bins_filtered
hiddenimports += cv2_imports

# Collect other packages normally
tmp_ret = collect_all('google.protobuf')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('grpclib')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('viam')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['src/__main__.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['.'],  # Use custom hook-ssl.py to include Python's OpenSSL
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# CRITICAL: Remove ONLY opencv's OpenSSL and add Python's OpenSSL
print(f"\nFiltering opencv OpenSSL and adding system OpenSSL:")
original_bins = len(a.binaries)
original_datas = len(a.datas)

# Filter binaries - only remove ones from cv2/.dylibs
a.binaries = [x for x in a.binaries
               if not ('cv2/.dylibs' in x[0] and ('libssl' in x[0] or 'libcrypto' in x[0]))]
# Filter datas - only remove ones from cv2/.dylibs
a.datas = [x for x in a.datas
            if not ('cv2/.dylibs' in x[0] and ('libssl' in x[0] or 'libcrypto' in x[0]))]

print(f"  Removed opencv OpenSSL: {original_bins - len(a.binaries)} binaries, {original_datas - len(a.datas)} datas")

# Add Python's OpenSSL libraries dynamically
import sys
import os
import subprocess
from PyInstaller.building.datastruct import TOC

if sys.platform == 'darwin':
    try:
        # Find where _ssl gets its OpenSSL from
        ssl_file = get_module_file_attribute('_ssl')
        ssl_libs_to_add = []
        if ssl_file and os.path.exists(ssl_file):
            result = subprocess.run(['otool', '-L', ssl_file],
                                  capture_output=True, text=True, check=True)
            for line in result.stdout.split('\n'):
                if 'libssl' in line or 'libcrypto' in line:
                    lib_path = line.strip().split()[0]
                    if os.path.exists(lib_path):
                        lib_name = os.path.basename(lib_path)
                        # PyInstaller TOC format: (dest_name, source_path, typecode)
                        ssl_libs_to_add.append((lib_name, lib_path, 'BINARY'))
                        print(f"  Added system OpenSSL: {lib_path} as {lib_name}")

        if ssl_libs_to_add:
            # Extend a.binaries with new TOC
            a.binaries.extend(TOC(ssl_libs_to_add))
    except Exception as e:
        print(f"  WARNING: Could not add system OpenSSL: {e}")

# Debug: Check if OpenSSL libraries are in final binaries list
ssl_in_binaries = [x for x in a.binaries if 'libssl' in x[0] or 'libcrypto' in x[0]]
print(f"OpenSSL libraries in final binaries list: {len(ssl_in_binaries)}")
for entry in ssl_in_binaries:
    print(f"  - {entry[0]} -> {entry[1]}")
print()

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
