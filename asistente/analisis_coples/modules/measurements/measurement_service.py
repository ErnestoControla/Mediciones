"""
Servicio de cálculo de mediciones geométricas.

Extrae características dimensionales de máscaras de segmentación:
- Dimensiones de bounding box (ancho, alto)
- Propiedades de máscara (área, perímetro)
- Propiedades geométricas (excentricidad, orientación)
- Conversión de píxeles a milímetros
"""

import cv2
import numpy as np
import math
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MeasurementService:
    """
    Servicio para cálculo de mediciones geométricas de máscaras.
    
    Calcula todas las propiedades dimensionales necesarias para análisis
    de piezas y defectos a partir de máscaras de segmentación.
    """
    
    def __init__(self):
        """Inicializa el servicio de mediciones"""
        self.factor_conversion_px_mm: Optional[float] = None
    
    def set_conversion_factor(self, factor: float) -> None:
        """
        Establece el factor de conversión de píxeles a milímetros.
        
        Args:
            factor: Factor de conversión (mm/píxel)
        """
        self.factor_conversion_px_mm = factor
        logger.info(f"Factor de conversión establecido: {factor} mm/px")
    
    def calcular_mediciones_completas(
        self,
        mascara: np.ndarray,
        convertir_a_mm: bool = False
    ) -> Dict[str, float]:
        """
        Calcula todas las mediciones de una máscara de segmentación.
        
        Args:
            mascara: Máscara binaria (numpy array 2D con valores 0 o 255)
            convertir_a_mm: Si True, también calcula mediciones en mm
            
        Returns:
            Dict con todas las mediciones:
                - ancho_bbox_px, alto_bbox_px
                - area_mascara_px, perimetro_mascara_px
                - excentricidad, orientacion_grados
                - ancho_bbox_mm, alto_bbox_mm, etc. (si convertir_a_mm=True)
        """
        try:
            # Validar máscara
            if mascara is None or mascara.size == 0:
                logger.warning("Máscara vacía o None")
                return self._mediciones_vacias()
            
            # Asegurar que sea binaria
            if mascara.dtype != np.uint8:
                mascara = mascara.astype(np.uint8)
            
            # Binarizar si no lo está
            if mascara.max() > 1:
                _, mascara = cv2.threshold(mascara, 127, 255, cv2.THRESH_BINARY)
            
            # Calcular mediciones en píxeles
            mediciones_px = self._calcular_mediciones_pixeles(mascara)
            
            # Si se solicita conversión a mm y hay factor disponible
            if convertir_a_mm and self.factor_conversion_px_mm:
                mediciones_mm = self._convertir_a_milimetros(mediciones_px)
                mediciones_px.update(mediciones_mm)
            
            return mediciones_px
            
        except Exception as e:
            logger.error(f"Error calculando mediciones: {e}")
            return self._mediciones_vacias()
    
    def _calcular_mediciones_pixeles(self, mascara: np.ndarray) -> Dict[str, float]:
        """
        Calcula todas las mediciones en píxeles.
        
        Args:
            mascara: Máscara binaria
            
        Returns:
            Dict con mediciones en píxeles
        """
        mediciones = {}
        
        # 1. Calcular bounding box
        bbox = self._calcular_bounding_box(mascara)
        mediciones['ancho_bbox_px'] = bbox['ancho']
        mediciones['alto_bbox_px'] = bbox['alto']
        
        # 2. Calcular propiedades de máscara
        props = self._calcular_propiedades_mascara(mascara)
        mediciones['area_mascara_px'] = props['area']
        mediciones['perimetro_mascara_px'] = props['perimetro']
        
        # 3. Calcular propiedades geométricas avanzadas
        geo = self._calcular_geometria_avanzada(mascara)
        mediciones['excentricidad'] = geo['excentricidad']
        mediciones['orientacion_grados'] = geo['orientacion_grados']
        
        return mediciones
    
    def _calcular_bounding_box(self, mascara: np.ndarray) -> Dict[str, float]:
        """
        Calcula las dimensiones del bounding box de la máscara.
        
        Args:
            mascara: Máscara binaria
            
        Returns:
            Dict con ancho y alto del bounding box
        """
        try:
            # Encontrar contornos
            contours, _ = cv2.findContours(
                mascara,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            if not contours:
                return {'ancho': 0.0, 'alto': 0.0}
            
            # Obtener el contorno más grande
            contorno_principal = max(contours, key=cv2.contourArea)
            
            # Calcular bounding box
            x, y, w, h = cv2.boundingRect(contorno_principal)
            
            return {
                'ancho': float(w),
                'alto': float(h),
                'x': float(x),
                'y': float(y)
            }
            
        except Exception as e:
            logger.error(f"Error calculando bounding box: {e}")
            return {'ancho': 0.0, 'alto': 0.0}
    
    def _calcular_propiedades_mascara(self, mascara: np.ndarray) -> Dict[str, float]:
        """
        Calcula área y perímetro de la máscara.
        
        Args:
            mascara: Máscara binaria
            
        Returns:
            Dict con área y perímetro
        """
        try:
            # Encontrar contornos
            contours, _ = cv2.findContours(
                mascara,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            if not contours:
                return {'area': 0.0, 'perimetro': 0.0}
            
            # Obtener el contorno más grande
            contorno_principal = max(contours, key=cv2.contourArea)
            
            # Calcular área y perímetro
            area = cv2.contourArea(contorno_principal)
            perimetro = cv2.arcLength(contorno_principal, closed=True)
            
            return {
                'area': float(area),
                'perimetro': float(perimetro)
            }
            
        except Exception as e:
            logger.error(f"Error calculando propiedades de máscara: {e}")
            return {'area': 0.0, 'perimetro': 0.0}
    
    def _calcular_geometria_avanzada(self, mascara: np.ndarray) -> Dict[str, float]:
        """
        Calcula propiedades geométricas avanzadas usando momentos de imagen.
        
        Args:
            mascara: Máscara binaria
            
        Returns:
            Dict con excentricidad y orientación
        """
        try:
            # Encontrar contornos
            contours, _ = cv2.findContours(
                mascara,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            if not contours:
                return {'excentricidad': 0.0, 'orientacion_grados': 0.0}
            
            # Obtener el contorno más grande
            contorno_principal = max(contours, key=cv2.contourArea)
            
            # Calcular momentos
            momentos = cv2.moments(contorno_principal)
            
            if momentos['m00'] == 0:  # Evitar división por cero
                return {'excentricidad': 0.0, 'orientacion_grados': 0.0}
            
            # Calcular momentos centrales normalizados
            mu20 = momentos['mu20'] / momentos['m00']
            mu02 = momentos['mu02'] / momentos['m00']
            mu11 = momentos['mu11'] / momentos['m00']
            
            # Calcular excentricidad
            # Basado en los eigenvalues de la matriz de covarianza
            lambda_sum = mu20 + mu02
            lambda_diff = math.sqrt(4 * mu11 * mu11 + (mu20 - mu02) * (mu20 - mu02))
            
            lambda1 = (lambda_sum + lambda_diff) / 2
            lambda2 = (lambda_sum - lambda_diff) / 2
            
            # Excentricidad: sqrt(1 - (lambda2/lambda1))
            # Rango [0, 1]: 0 = círculo perfecto, 1 = línea
            if lambda1 > 0:
                excentricidad = math.sqrt(1 - (lambda2 / lambda1)) if lambda2 < lambda1 else 0.0
            else:
                excentricidad = 0.0
            
            # Calcular orientación en grados
            # Ángulo del eje principal
            if mu20 != mu02:
                theta = 0.5 * math.atan2(2 * mu11, mu20 - mu02)
                orientacion_grados = math.degrees(theta)
            else:
                orientacion_grados = 0.0
            
            # Normalizar ángulo a rango [-90, 90]
            while orientacion_grados > 90:
                orientacion_grados -= 180
            while orientacion_grados < -90:
                orientacion_grados += 180
            
            return {
                'excentricidad': float(excentricidad),
                'orientacion_grados': float(orientacion_grados)
            }
            
        except Exception as e:
            logger.error(f"Error calculando geometría avanzada: {e}")
            return {'excentricidad': 0.0, 'orientacion_grados': 0.0}
    
    def _convertir_a_milimetros(self, mediciones_px: Dict[str, float]) -> Dict[str, float]:
        """
        Convierte mediciones de píxeles a milímetros.
        
        Args:
            mediciones_px: Dict con mediciones en píxeles
            
        Returns:
            Dict con mediciones en mm (campos terminados en _mm)
        """
        if not self.factor_conversion_px_mm:
            logger.warning("Factor de conversión no establecido")
            return {}
        
        factor = self.factor_conversion_px_mm
        
        return {
            # Dimensiones lineales: multiplicar por factor
            'ancho_bbox_mm': mediciones_px.get('ancho_bbox_px', 0) * factor,
            'alto_bbox_mm': mediciones_px.get('alto_bbox_px', 0) * factor,
            'perimetro_mascara_mm': mediciones_px.get('perimetro_mascara_px', 0) * factor,
            
            # Área: multiplicar por factor al cuadrado (mm²)
            'area_mascara_mm': mediciones_px.get('area_mascara_px', 0) * (factor ** 2),
            
            # Propiedades geométricas adimensionales: no necesitan conversión
            # (excentricidad y orientación son iguales en px y mm)
        }
    
    def _mediciones_vacias(self) -> Dict[str, float]:
        """
        Retorna un diccionario con mediciones en 0.
        
        Returns:
            Dict con todas las mediciones en 0
        """
        return {
            'ancho_bbox_px': 0.0,
            'alto_bbox_px': 0.0,
            'area_mascara_px': 0.0,
            'perimetro_mascara_px': 0.0,
            'excentricidad': 0.0,
            'orientacion_grados': 0.0,
        }
    
    def calcular_ancho_mascara(self, mascara: np.ndarray) -> float:
        """
        Calcula el ancho de la máscara (bounding box).
        
        Args:
            mascara: Máscara binaria
            
        Returns:
            Ancho en píxeles
        """
        bbox = self._calcular_bounding_box(mascara)
        return bbox['ancho']
    
    def calcular_alto_mascara(self, mascara: np.ndarray) -> float:
        """
        Calcula el alto de la máscara (bounding box).
        
        Args:
            mascara: Máscara binaria
            
        Returns:
            Alto en píxeles
        """
        bbox = self._calcular_bounding_box(mascara)
        return bbox['alto']
    
    def calcular_area_mascara(self, mascara: np.ndarray) -> float:
        """
        Calcula el área de la máscara.
        
        Args:
            mascara: Máscara binaria
            
        Returns:
            Área en píxeles cuadrados
        """
        props = self._calcular_propiedades_mascara(mascara)
        return props['area']
    
    def calcular_perimetro_mascara(self, mascara: np.ndarray) -> float:
        """
        Calcula el perímetro de la máscara.
        
        Args:
            mascara: Máscara binaria
            
        Returns:
            Perímetro en píxeles
        """
        props = self._calcular_propiedades_mascara(mascara)
        return props['perimetro']


# Instancia singleton del servicio
_measurement_service_instance = None

def get_measurement_service() -> MeasurementService:
    """
    Obtiene la instancia singleton del servicio de mediciones.
    
    Returns:
        MeasurementService: Instancia del servicio
    """
    global _measurement_service_instance
    
    if _measurement_service_instance is None:
        _measurement_service_instance = MeasurementService()
        logger.info("✅ Servicio de mediciones inicializado")
    
    return _measurement_service_instance

