#!/usr/bin/env python3
"""
Helper script to create annotation files for real-world test images.

Usage:
    python create_annotation.py <image_path> [output_json]

This script will:
1. Detect QR codes in the image
2. Print the detected bounding boxes
3. Generate a JSON annotation file you can edit if needed
"""

import sys
import json
from pathlib import Path
from PIL import Image
import numpy as np
from pyzbar.pyzbar import decode


def create_annotation_from_image(image_path: Path, output_path: Path = None, description: str = None):
    """
    Detect QR codes in an image and create an annotation file.

    Args:
        image_path: Path to the image file
        output_path: Path for output JSON (defaults to image_path.with_suffix('.json'))
        description: Optional description for the test case
    """
    # Load image
    print(f"Loading image: {image_path}")
    img = Image.open(image_path)
    print(f"Image size: {img.size}")

    # Detect QR codes
    print("\nDetecting QR codes...")
    results = decode(np.array(img))
    print(f"Found {len(results)} QR code(s)")

    if len(results) == 0:
        print("No QR codes detected. Cannot create annotation.")
        return False

    # Build annotation
    expected_detections = []
    for i, result in enumerate(results):
        data = result.data.decode('utf-8')
        x, y, w, h = result.rect

        print(f"\nQR Code {i+1}:")
        print(f"  Data: {data}")
        print(f"  Position: ({x}, {y})")
        print(f"  Size: {w}x{h}")

        expected_detections.append({
            "data": data,
            "bbox": {
                "x_min": x,
                "y_min": y,
                "x_max": x + w,
                "y_max": y + h
            }
        })

    # Create annotation object
    annotation = {
        "description": description or f"Test case for {image_path.name}",
        "image": image_path.name,
        "expected_detections": expected_detections,
        "min_iou": 0.5
    }

    # Determine output path
    if output_path is None:
        output_path = image_path.with_suffix('.json')

    # Write JSON
    print(f"\nWriting annotation to: {output_path}")
    with open(output_path, 'w') as f:
        json.dump(annotation, f, indent=2)

    print("\n✓ Annotation created successfully!")
    print(f"\nTo use in tests:")
    print(f"1. Copy both {image_path.name} and {output_path.name} to test_images/")
    print(f"2. Run: python test_bounding_boxes.py")

    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python create_annotation.py <image_path> [output_json]")
        print("\nExample:")
        print("  python create_annotation.py my_test_image.jpg")
        print("  python create_annotation.py my_test_image.jpg custom_name.json")
        sys.exit(1)

    image_path = Path(sys.argv[1])

    if not image_path.exists():
        print(f"Error: Image file not found: {image_path}")
        sys.exit(1)

    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    try:
        success = create_annotation_from_image(image_path, output_path)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
