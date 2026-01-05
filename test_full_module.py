"""
Comprehensive test that exercises all module imports and functionality.
This test is designed to expose import errors and runtime issues.
"""

import asyncio
from PIL import Image
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.components.camera import Camera, ViamImage
from viam.services.vision import Vision
from viam.resource.registry import Registry
from typing import Mapping

# Import the module's __init__ to trigger registration
import src
from src.pyzbar import pyzbar


class MockCamera(Camera):
    """Mock camera for testing"""

    def __init__(self, name: str):
        self.name = name

    async def get_image(self, mime_type: str = "", *, extra=None, timeout=None) -> ViamImage:
        """Return a test image as ViamImage"""
        # Create a simple test image
        img = Image.new('RGB', (640, 480), color='white')

        # Convert to ViamImage format
        import cv2
        import numpy as np
        image_cv = np.array(img)
        image_cv = cv2.cvtColor(image_cv, cv2.COLOR_RGB2BGR)
        _, encoded = cv2.imencode('.jpg', image_cv)

        return ViamImage(data=encoded.tobytes(), mime_type="image/jpeg")

    async def get_images(self, *, timeout=None):
        return []

    async def get_point_cloud(self, *, extra=None, timeout=None):
        return []

    async def get_properties(self, *, timeout=None):
        return {}


async def test_full_module_initialization():
    """Test complete module initialization and all methods"""

    print("=" * 60)
    print("COMPREHENSIVE MODULE TEST")
    print("=" * 60)

    # Test 1: Check registry registration
    print("\n[1] Testing registry registration...")
    try:
        # The import of src/__init__.py should have registered the model
        print(f"✓ Module imported successfully")
        print(f"✓ Model: {pyzbar.MODEL}")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise

    # Test 2: Create vision service with configuration
    print("\n[2] Creating vision service with configuration...")
    try:
        config = ComponentConfig(name="test_vision")
        config.attributes.fields["camera_name"].string_value = "test_camera"

        # Validate configuration
        deps = pyzbar.validate(config)
        print(f"✓ Validation returned dependencies: {deps}")

    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise

    # Test 3: Create service instance with dependencies
    print("\n[3] Creating service instance with camera dependency...")
    try:
        # Create mock camera
        mock_camera = MockCamera("test_camera")

        # Create resource name for the camera
        camera_resource_name = ResourceName(
            namespace="rdk",
            type="component",
            subtype="camera",
            name="test_camera"
        )

        # Build dependencies mapping
        dependencies: Mapping[ResourceName, Camera] = {
            camera_resource_name: mock_camera
        }

        # Create the vision service using the new() factory method
        vision_service = pyzbar.new(config, dependencies)
        print(f"✓ Service created: {vision_service}")

    except Exception as e:
        print(f"✗ FAILED during service creation: {e}")
        raise

    # Test 4: Test get_properties
    print("\n[4] Testing get_properties()...")
    try:
        props = await vision_service.get_properties()
        print(f"✓ Properties: detections={props.detections_supported}, "
              f"classifications={props.classifications_supported}")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise

    # Test 5: Test get_detections with PIL image
    print("\n[5] Testing get_detections() with PIL image...")
    try:
        test_image = Image.new('RGB', (640, 480), color='white')
        detections = await vision_service.get_detections(test_image)
        print(f"✓ get_detections() returned {len(detections)} detections")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise

    # Test 6: Test get_detections_from_camera
    print("\n[6] Testing get_detections_from_camera()...")
    try:
        detections = await vision_service.get_detections_from_camera("test_camera")
        print(f"✓ get_detections_from_camera() returned {len(detections)} detections")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise

    # Test 7: Test capture_all_from_camera
    print("\n[7] Testing capture_all_from_camera()...")
    try:
        result = await vision_service.capture_all_from_camera(
            "test_camera",
            return_image=True,
            return_detections=True
        )
        print(f"✓ capture_all_from_camera() succeeded")
        print(f"  - Image returned: {result.image is not None}")
        print(f"  - Detections: {len(result.detections)}")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise

    # Test 8: Test get_classifications (should return empty)
    print("\n[8] Testing get_classifications()...")
    try:
        test_image = Image.new('RGB', (640, 480), color='white')
        classifications = await vision_service.get_classifications(test_image, count=10)
        print(f"✓ get_classifications() returned {len(classifications)} classifications (expected 0)")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise

    # Test 9: Test do_command
    print("\n[9] Testing do_command()...")
    try:
        result = await vision_service.do_command({"test": "command"})
        print(f"✓ do_command() returned: {result}")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        raise

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    print("Starting comprehensive module test...")
    print("This test exercises all imports and functionality.\n")

    try:
        asyncio.run(test_full_module_initialization())
        print("\n✓ SUCCESS: All tests passed!")
    except Exception as e:
        print(f"\n✗ FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
