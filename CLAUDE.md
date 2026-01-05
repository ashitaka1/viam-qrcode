# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Viam module that implements a QR code scanner as a custom Vision service using Pyzbar and OpenCV. The module can be deployed to the Viam Registry and used on Viam robots, or run locally for development and testing.

**Module ID**: `joyce:pyzbar`
**Model**: `joyce:vision:pyzbar`
**API**: `rdk:service:vision`

## Development Commands

### Setup
```bash
# Install system dependencies (Linux/macOS)
./setup.sh

# Or manually:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running Locally
```bash
# Run the module in development mode
./run.sh

# Run local test script with camera feed
python script.py

# Run process script (uses vision service instead of direct detection)
python process.py

# Run regression tests
python test_pyzbar_vision.py
```

### Building for Distribution
```bash
# Build PyInstaller binary for deployment
./build.sh

# Creates: dist/main (executable) and dist/archive.tar.gz (for Viam Registry)
```

### Testing Local Changes
```bash
# CRITICAL: To test local module changes, use viam module reload-local
# This rebuilds and reloads the module into the running Viam instance
viam module reload-local --cloud-config /opt/homebrew/etc/viam.json

# NEVER manually copy files to ~/.viam/packages-local/
# ALWAYS use the reload-local command to ensure proper module lifecycle
```

### Manual Deployment
```bash
# Bundle module for upload
make bundle

# Upload to Viam Registry (requires viam CLI)
make upload version=<version> platform=<platform>

# Clean build artifacts
make clean
```

## Architecture

### Module Structure

The codebase has two distinct execution modes:

1. **Viam Module Mode** (`src/` directory)
   - Entry point: `src/__main__.py`
   - Vision service implementation: `src/pyzbar.py`
   - Runs as a Viam modular resource
   - Deployed via PyInstaller binary to Viam Registry

2. **Standalone Scripts** (root directory)
   - `script.py`: Direct camera feed with QR detection using Viam SDK
   - `process.py`: Uses deployed Viam vision service for QR detection
   - `decode.py`: Utility for decoding QR codes from static images
   - For local development/testing only

### Viam Module Implementation

The module implements the Viam Vision service API (`src/pyzbar.py`):

**Key Class**: `pyzbar(Vision, Reconfigurable)`
- **Model**: `joyce:vision:pyzbar`
- **Dependencies**: Requires a camera component specified via `camera_name` attribute
- **Supported Operations**:
  - `get_detections()`: QR code detection from PIL images
  - `get_detections_from_camera()`: QR code detection from Viam camera
  - `capture_all_from_camera()`: Combined image capture and detection
  - `get_properties()`: Reports capabilities (detections_supported=True)

**QR Detection Pipeline** (`detect_qr_code` method):
1. Convert ViamImage → PIL → OpenCV format
2. Preprocess image (grayscale → histogram equalization → threshold → resize 1.5x)
3. Use pyzbar to decode QR codes
4. Return Detection objects with bounding boxes and QR data as `class_name`

**Camera Dependency Handling**:
- Camera specified in config attributes as `camera_name`
- `validate()` returns camera as required dependency
- `reconfigure()` stores dependencies in `self.DEPS`
- Camera looked up by name from dependencies dictionary at runtime

### Build System

**PyInstaller Configuration** (`main.spec`, `build.sh`):
- Bundles Python module into standalone executable
- Critical `--collect-all` flags for: pyzbar, cv2, google.protobuf, grpclib, viam
- Hidden imports for pyzbar.pyzbar and pyzbar.wrapper required
- Output: `dist/main` executable and `dist/archive.tar.gz` for deployment

**Deployment** (`.github/workflows/deploy.yml`):
- GitHub Actions workflow using `viamrobotics/build-action@v1`
- Triggers on release publish or manual workflow dispatch
- Builds for: linux/amd64, linux/arm64, darwin/amd64, darwin/arm64
- Requires `VIAM_KEY_ID` and `VIAM_KEY_VALUE` secrets

### Configuration

**Module Configuration** (`meta.json`):
- Defines module metadata for Viam Registry
- Build process: `setup.sh` → `build.sh` → `dist/archive.tar.gz`
- Entrypoint: `"main"` (NOT `"dist/main"`)
  - IMPORTANT: When the archive is extracted to Viam's local module directory, the executable is placed at the root level, not in a `dist/` subdirectory
  - The entrypoint path is relative to the extracted archive contents

**Environment Variables** (for standalone scripts):
- `ROBOT_API_KEY`: Viam robot API key
- `ROBOT_API_KEY_ID`: Viam robot API key ID
- `ROBOT_ADDRESS`: Viam robot address
- `CAMERA_NAME`: Camera component name (default: "camera-1")
- `VISION_NAME`: Vision service name (for process.py)

## Dependencies

**Python Version**: Python 3.11+ required (per Viam module development requirements)

**Core Libraries**:
- `viam-sdk==0.31.0`: Viam Python SDK
- `pyzbar==0.1.9`: QR code decoding
- `opencv-python-headless==4.10.0.84`: Image processing (headless for PyInstaller compatibility)
- `pillow==10.4.0`: Image format conversion
- `grpclib==0.4.7`: gRPC for Viam communication

**Note on opencv-python-headless**: The module uses opencv-python-headless instead of opencv-python to avoid OpenSSL library conflicts when packaging with PyInstaller. This provides all required image processing functions without GUI dependencies.

**System Dependencies**:
- Linux: `libzbar0` (installed via `setup.sh`)
- macOS: `zbar` via Homebrew (installed via `setup.sh`)

## Testing

Run regression tests with: `python test_pyzbar_vision.py`

The test validates that `get_detections()` correctly handles PIL images without crashing, using `image.jpg` as test data.

## Notes

- The module uses modern Viam dependency pattern: dependencies declared in `validate()` and resolved via `reconfigure()`
- QR code data is returned as the `class_name` field in Detection objects
- Image preprocessing significantly improves detection accuracy (1.5x resize, histogram equalization, thresholding)
- The module only supports detections, not classifications or point clouds
