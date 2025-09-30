"""
Módulo de Segmentación para Análisis de Coples
"""

from .segmentation_defectos_engine import SegmentadorDefectosCoples
from .defectos_segmentation_processor import ProcesadorSegmentacionDefectos

__all__ = [
    "SegmentadorDefectosCoples",
    "ProcesadorSegmentacionDefectos"
]
