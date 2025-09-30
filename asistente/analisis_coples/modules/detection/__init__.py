"""
Módulo de Detección para Análisis de Coples
Implementa detección de objetos usando modelos ONNX
"""

from .detection_engine import DetectorCoplesONNX, DetectorPiezasCoples
from .bbox_processor import ProcesadorBoundingBoxes, ProcesadorPiezasCoples
from .detection_defectos_engine import DetectorDefectosCoples
from .defectos_processor import ProcesadorDefectos

__all__ = [
    'DetectorCoplesONNX',
    'DetectorPiezasCoples', 
    'ProcesadorBoundingBoxes',
    'ProcesadorPiezasCoples',
    'DetectorDefectosCoples',
    'ProcesadorDefectos'
]
