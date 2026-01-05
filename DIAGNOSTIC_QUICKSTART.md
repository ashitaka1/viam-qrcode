# OpenSSL Diagnostic Quick Start

## What's the Issue?

The viam-qrcode module builds but fails to run on some MacBooks due to an OpenSSL library conflict between opencv-python-headless and Python's SSL module.

## Quick Diagnostic (5 minutes)

### On Your Current (Failing) Machine

```bash
# 1. Go to the project directory
cd /path/to/viam-qrcode

# 2. Run all diagnostics
./run_all_diagnostics.sh
```

This creates a report file like `diagnostic_report_20260105_123456.txt`.

### On Your Office (Working) Machine

```bash
# 1. Pull latest code
cd /path/to/viam-qrcode
git pull

# 2. Run all diagnostics
./run_all_diagnostics.sh
```

This creates another report file.

## Compare the Reports

Look for differences in:

| Item | What to Check |
|------|---------------|
| **macOS Version** | Are they different OS versions? |
| **Architecture** | Intel (x86_64) vs Apple Silicon (arm64)? |
| **Python Path** | Different installation methods? |
| **OpenSSL Location** | `/opt/homebrew` vs `/usr/local`? |
| **PyInstaller Version** | Different versions? |
| **Runtime Test** | Does OpenSSL load on one but not the other? |

## Individual Scripts

If you want to run tests separately:

```bash
# Just environment info
./collect_env_info.sh

# Just inspect the built binary
./inspect_binary.sh

# Just test runtime extraction
./test_extraction.sh
```

## For Claude on the Office Machine

Send Claude these files:
1. `DEBUG_OPENSSL_ISSUE.md` - Full debugging guide with context
2. `diagnostic_report_XXXXXX.txt` - The diagnostic report from this machine
3. `diagnostic_report_YYYYYY.txt` - The diagnostic report from the failing machine

Then ask:
> "I have two machines where this PyInstaller build succeeds on one but fails on the other. Here are diagnostic reports from both. Can you identify what's different and why the OpenSSL import fails on one machine?"

## What the Fix Does

The current `main.spec` file:
1. **Filters out** opencv's incompatible OpenSSL from `cv2/.dylibs/`
2. **Adds in** the system's OpenSSL that Python's `_ssl` module expects
3. Does this dynamically using `otool -L` on macOS (or `ldd` on Linux)

The build log should show:
```
Filtering opencv OpenSSL and adding system OpenSSL:
  Removed opencv OpenSSL: 2 binaries, 0 datas
  Added system OpenSSL: /path/to/libssl.3.dylib as libssl.3.dylib
  Added system OpenSSL: /path/to/libcrypto.3.dylib as libcrypto.3.dylib
OpenSSL libraries in final binaries list: 2
```

## Expected Test Results

### On Working Machine
```
=== ATTEMPTING SSL IMPORT ===
✓ SUCCESS: ssl module imported
  OpenSSL version: OpenSSL 3.x.x
```

### On Failing Machine
```
=== ATTEMPTING SSL IMPORT ===
✗ FAILED: Library not loaded: @rpath/libssl.3.dylib
```

## Files Changed

The fix involves:
- **main.spec** - PyInstaller specification with OpenSSL handling
- **build.sh** - Now uses the spec file instead of command-line args
- **hook-ssl.py** - Custom PyInstaller hook (backup approach)

## Need Help?

If you're stuck, the diagnostic reports should reveal:
- Whether OpenSSL libraries are in the bundle
- Whether they're being extracted at runtime
- What the specific error is
- Environment differences between machines

Share the reports with Claude for detailed analysis.
