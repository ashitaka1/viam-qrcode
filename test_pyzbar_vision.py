"""
Regression tests for pyzbar vision service.
"""

import asyncio
from PIL import Image
from src.pyzbar import pyzbar
from viam.proto.app.robot import ComponentConfig


async def test_get_detections_with_pil_image():
    """
    Test that get_detections() works with a PIL Image containing a QR code.
    If there's a bug with ViamImage construction, this will fail.
    """

    # Load existing test image (image.jpg should contain a QR code)
    test_image = Image.open("image.jpg")

    print(f"Created test QR code image: {test_image.size}")

    # Create a minimal vision service instance
    config = ComponentConfig(name="test_qr")
    vision_service = pyzbar(config.name)

    # Call get_detections with the PIL image (should not crash)
    detections = await vision_service.get_detections(test_image)

    print(f"Detections found: {len(detections)}")
    print(f"✓ PASS: get_detections() works with PIL Image (no crash)")

    if len(detections) > 0:
        print(f"  Detected QR codes: {[d.class_name for d in detections]}")


if __name__ == "__main__":
    asyncio.run(test_get_detections_with_pil_image())
    print("\nTest passed!")
