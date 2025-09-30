"""
Módulo de clasificación de coples
"""

from .inference_engine import ClasificadorCoplesONNX
from .image_processor import ProcesadorImagenClasificacion

__all__ = ['ClasificadorCoplesONNX', 'ProcesadorImagenClasificacion']
