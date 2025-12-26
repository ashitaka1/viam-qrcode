"""
This file registers the model with the Python SDK.
"""

from viam.services.vision import Vision
from viam.resource.registry import Registry, ResourceCreatorRegistration

from src.pyzbar import pyzbar

Registry.register_resource_creator(Vision.SUBTYPE, pyzbar.MODEL, ResourceCreatorRegistration(pyzbar.new, pyzbar.validate))