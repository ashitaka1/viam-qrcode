from typing import ClassVar, Mapping, Optional, Any, List, cast
from typing_extensions import Self

from PIL import Image
from viam.proto.common import PointCloudObject
from viam.proto.service.vision import Classification, Detection
from viam.resource.types import RESOURCE_NAMESPACE_RDK, RESOURCE_TYPE_SERVICE, Subtype
from viam.utils import ValueTypes


from viam.module.types import Reconfigurable
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.types import Model, ModelFamily

from viam.services.vision import Vision, CaptureAllResult
from viam.proto.service.vision import GetPropertiesResponse
from viam.components.camera import Camera, ViamImage
from viam.logging import getLogger
from viam.media.utils.pil import viam_to_pil_image

import numpy as np
import cv2
from pyzbar.pyzbar import decode
# import subprocess
# import urllib.parse
import time

LOGGER = getLogger(__name__)

class pyzbar(Vision, Reconfigurable):
    """
    Custom Vision Service that uses pyzbar to detect QR codes.
    """

    MODEL: ClassVar[Model] = Model(ModelFamily("joyce", "vision"), "pyzbar")
    
    model: None

    last_triggered: dict = {}

    cooldown_period: int = 5

    # Constructor
    @classmethod
    def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> Self:
        my_class = cls(config.name)
        my_class.reconfigure(config, dependencies)
        return my_class

    # Validates JSON Configuration
    @classmethod
    def validate(cls, config: ComponentConfig):
        # Declare camera as a required dependency based on attributes
        camera_name = config.attributes.fields.get("camera_name")
        if camera_name:
            camera_name_str = camera_name.string_value or camera_name.list_value
            if camera_name_str:
                # Return the camera as a required dependency
                return [camera_name_str] if isinstance(camera_name_str, str) else list(camera_name_str)
        return []

    # Handles attribute reconfiguration
    def reconfigure(self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]):
        self.DEPS = dependencies

        # Log available dependencies for debugging
        dep_names = [rn.name for rn in dependencies.keys()]
        LOGGER.info(f"Reconfiguring with dependencies: {dep_names}")

        # Store the camera name from attributes if provided
        camera_name_field = config.attributes.fields.get("camera_name")
        if camera_name_field:
            self.default_camera_name = camera_name_field.string_value
            LOGGER.info(f"Default camera configured: {self.default_camera_name}")
        else:
            self.default_camera_name = None

        return
        
    async def get_cam_image(self, camera_name: str) -> ViamImage:
        # Find the camera in dependencies by iterating and matching name
        actual_cam = None
        for resource_name, resource in self.DEPS.items():
            if resource_name.name == camera_name:
                actual_cam = resource
                break

        if actual_cam is None:
            raise ValueError(f"Camera '{camera_name}' not found in dependencies. Available: {[rn.name for rn in self.DEPS.keys()]}")

        cam = cast(Camera, actual_cam)
        cam_image = await cam.get_image(mime_type="image/jpeg")
        return cam_image

    async def get_detections_from_camera(self, camera_name: str, *, extra: Optional[Mapping[str, Any]] = None, timeout: Optional[float] = None) -> List[Detection]:
        # Get image from the camera
        cam_image = await self.get_cam_image(camera_name)
        return await self.detect_qr_code(cam_image)

    async def get_detections(
        self,
        image: Image.Image,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> List[Detection]:
        # Convert PIL image to ViamImage or OpenCV as needed
        image_cv = np.array(image)
        image_cv = cv2.cvtColor(image_cv, cv2.COLOR_RGB2BGR)
        return self.detect_qr_code(ViamImage(data=image_cv.tobytes(), mime_type="image/jpeg"))

    async def get_classifications(
        self,
        image: Image.Image,
        count: int,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> List[Classification]:
        """
        This method is not implemented for QR code detection.
        """
        # No classifications are done, return an empty list
        return []

    async def detect_qr_code(self, image: ViamImage) -> List[Detection]:
        """
        Detect QR codes in the given image using pyzbar.
        """
        # Convert ViamImage to OpenCV format
        image_pil = viam_to_pil_image(image)
        image_cv = np.array(image_pil)
        image_cv = cv2.cvtColor(image_cv, cv2.COLOR_RGB2BGR)
        
        # Detect QR codes
        processed_image = self.preprocess_image(image_cv)
        qr_codes = decode(processed_image)
        detections = []
        
        for qr_code in qr_codes:
            qr_data = qr_code.data.decode('utf-8')
            LOGGER.info(f"QR Code detected: {qr_data}")

            # Only trigger action if it hasn't been triggered recently
            current_time = time.time()
            if qr_data not in self.last_triggered or (current_time - self.last_triggered[qr_data] > self.cooldown_period):  
                self.trigger_action_on_qr_code(qr_data)
                self.last_triggered[qr_data] = current_time
            
            # Create a Detection object for each QR code detected
            (x, y, w, h) = qr_code.rect
            # Adjust bounding box to align with original image dimensions
            scale_x = image_cv.shape[1] / processed_image.shape[1]
            scale_y = image_cv.shape[0] / processed_image.shape[0]
            x = int(x * scale_x)
            y = int(y * scale_y)
            w = int(w * scale_x)
            h = int(h * scale_y)
            detection = Detection(x_min=x, y_min=y, x_max=x + w, y_max=y + h, class_name=qr_data, confidence=1.0)
            detections.append(detection)
        
        if not qr_codes:
            LOGGER.info("No QR Code detected")
        
        return detections
    
    def preprocess_image(self, image):
        """
        Preprocess the image to improve QR code detection.
        """
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        equalized_image = cv2.equalizeHist(gray_image)
        threshold_image = cv2.threshold(equalized_image, 128, 255, cv2.THRESH_BINARY)[1]
        resized_image = cv2.resize(threshold_image, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)
        return resized_image
    
    def trigger_action_on_qr_code(self, qr_data: str):
        """
        Trigger an action based on the QR code data.
        """
        
        # Can add custom logic here
        LOGGER.info(f"Triggering action based on QR Code: {qr_data}")

    async def get_classifications_from_camera(self, camera_name: str, count: int, *, extra: Optional[Mapping[str, Any]] = None, timeout: Optional[float] = None) -> List[Classification]:
        """
        This method is not implemented for QR code detection.
        """
        return []
    
    async def get_object_point_clouds(self, camera_name: str, *, extra: Optional[Mapping[str, Any]] = None, timeout: Optional[float] = None) -> List[PointCloudObject]:
        return []
    
    async def do_command(self, command: Mapping[str, ValueTypes], *, timeout: Optional[float] = None) -> Mapping[str, ValueTypes]:
        return {}

    async def capture_all_from_camera(self, camera_name: str, return_image: bool = False, return_classifications: bool = False, return_detections: bool = False, return_object_point_clouds: bool = False, *, extra: Optional[Mapping[str, Any]] = None, timeout: Optional[float] = None) -> CaptureAllResult:
        result = CaptureAllResult()
        result.image = await self.get_cam_image(camera_name)
        result.detections = await self.get_detections_from_camera(camera_name)
        return result

    async def get_properties(self, *, extra: Optional[Mapping[str, Any]] = None, timeout: Optional[float] = None) -> GetPropertiesResponse:
        return GetPropertiesResponse(
            classifications_supported=False,
            detections_supported=True,
            object_point_clouds_supported=False
        )