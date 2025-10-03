"""
Servicios del sistema de análisis de coples.
"""

from .camera_service import CameraService, get_camera_service
from .segmentation_analysis_service import SegmentationAnalysisService, get_segmentation_analysis_service
from .rutina_inspeccion_service import RutinaInspeccionService, get_rutina_inspeccion_service

__all__ = [
    'CameraService',
    'get_camera_service',
    'SegmentationAnalysisService',
    'get_segmentation_analysis_service',
    'RutinaInspeccionService',
    'get_rutina_inspeccion_service',
]

