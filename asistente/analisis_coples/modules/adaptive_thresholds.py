#!/usr/bin/env python3
"""
Sistema de umbrales adaptativos para robustez ante cambios de iluminación
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from collections import deque

class UmbralesAdaptativos:
    """
    Sistema de umbrales adaptativos que se ajusta automáticamente
    basándose en las condiciones de iluminación
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Umbrales base
        self.confianza_base = 0.5
        self.area_minima_base = 500
        self.cobertura_minima_base = 0.1
        
        # Historial de detecciones exitosas
        self.detection_history = deque(maxlen=50)
        self.illumination_history = deque(maxlen=20)
        
        # Factores de ajuste
        self.confianza_factor = 0.1
        self.area_factor = 0.2
        self.cobertura_factor = 0.15
        
        # Límites de ajuste - MÁS AGRESIVOS para condiciones difíciles
        self.confianza_min = 0.1  # Muy permisivo para condiciones difíciles
        self.confianza_max = 0.8
        self.area_min = 100  # Área mínima más pequeña
        self.area_max = 2000
        self.cobertura_min = 0.02  # Cobertura mínima muy baja
        self.cobertura_max = 0.3
        
    def actualizar_historial_iluminacion(self, brightness: float, contrast: float):
        """
        Actualiza el historial de iluminación
        
        Args:
            brightness (float): Brillo de la imagen
            contrast (float): Contraste de la imagen
        """
        self.illumination_history.append({
            'brightness': brightness,
            'contrast': contrast
        })
    
    def actualizar_historial_detecciones(self, detecciones: List[Dict], 
                                       umbrales_usados: Dict[str, float]):
        """
        Actualiza el historial de detecciones exitosas
        
        Args:
            detecciones (List[Dict]): Lista de detecciones
            umbrales_usados (Dict[str, float]): Umbrales utilizados
        """
        if detecciones:
            self.detection_history.append({
                'count': len(detecciones),
                'confianza_promedio': np.mean([d.get('confianza', 0) for d in detecciones]),
                'area_promedio': np.mean([d.get('area_mascara', 0) for d in detecciones]),
                'umbrales': umbrales_usados.copy()
            })
    
    def calcular_umbrales_adaptativos(self, brightness: float, contrast: float) -> Dict[str, float]:
        """
        Calcula umbrales adaptativos basándose en las condiciones de iluminación
        
        Args:
            brightness (float): Brillo de la imagen
            contrast (float): Contraste de la imagen
            
        Returns:
            Dict[str, float]: Umbrales adaptativos
        """
        try:
            # Actualizar historial
            self.actualizar_historial_iluminacion(brightness, contrast)
            
            # Calcular factores de ajuste basándose en iluminación
            brightness_factor = self._calcular_factor_brillo(brightness)
            contrast_factor = self._calcular_factor_contraste(contrast)
            
            # Calcular umbrales adaptativos
            confianza_adaptativa = self.confianza_base * brightness_factor * contrast_factor
            area_adaptativa = self.area_minima_base * brightness_factor
            cobertura_adaptativa = self.cobertura_minima_base * contrast_factor
            
            # Aplicar límites
            confianza_adaptativa = np.clip(confianza_adaptativa, 
                                         self.confianza_min, self.confianza_max)
            area_adaptativa = np.clip(area_adaptativa, 
                                    self.area_min, self.area_max)
            cobertura_adaptativa = np.clip(cobertura_adaptativa, 
                                         self.cobertura_min, self.cobertura_max)
            
            umbrales = {
                'confianza_min': confianza_adaptativa,
                'area_minima': area_adaptativa,
                'cobertura_minima': cobertura_adaptativa,
                'brightness_factor': brightness_factor,
                'contrast_factor': contrast_factor
            }
            
            return umbrales
            
        except Exception as e:
            self.logger.error(f"Error calculando umbrales adaptativos: {e}")
            return self._obtener_umbrales_base()
    
    def _calcular_factor_brillo(self, brightness: float) -> float:
        """
        Calcula factor de ajuste basándose en el brillo
        
        Args:
            brightness (float): Brillo de la imagen
            
        Returns:
            float: Factor de ajuste
        """
        # Imagen muy oscura: reducir umbrales AGRESIVAMENTE
        if brightness < 80:
            return 0.5  # Más agresivo
        # Imagen muy brillante: aumentar umbrales
        elif brightness > 180:
            return 1.3
        # Imagen normal pero con brillo medio-bajo: reducir umbrales
        elif brightness < 100:
            return 0.6  # Moderadamente agresivo
        # Imagen normal
        else:
            return 1.0
    
    def _calcular_factor_contraste(self, contrast: float) -> float:
        """
        Calcula factor de ajuste basándose en el contraste
        
        Args:
            contrast (float): Contraste de la imagen
            
        Returns:
            float: Factor de ajuste
        """
        # Contraste muy bajo: reducir umbrales AGRESIVAMENTE
        if contrast < 20:
            return 0.5  # Muy agresivo
        # Contraste bajo: reducir umbrales
        elif contrast < 30:
            return 0.7  # Agresivo
        # Contraste alto: aumentar umbrales
        elif contrast > 80:
            return 1.2
        # Contraste normal
        else:
            return 1.0
    
    def _obtener_umbrales_base(self) -> Dict[str, float]:
        """
        Obtiene umbrales base como fallback
        
        Returns:
            Dict[str, float]: Umbrales base
        """
        return {
            'confianza_min': self.confianza_base,
            'area_minima': self.area_minima_base,
            'cobertura_minima': self.cobertura_minima_base,
            'brightness_factor': 1.0,
            'contrast_factor': 1.0
        }
    
    def ajustar_umbrales_por_rendimiento(self, detecciones_actuales: int, 
                                       detecciones_esperadas: int = 1) -> Dict[str, float]:
        """
        Ajusta umbrales basándose en el rendimiento de detección
        
        Args:
            detecciones_actuales (int): Número de detecciones actuales
            detecciones_esperadas (int): Número de detecciones esperadas
            
        Returns:
            Dict[str, float]: Umbrales ajustados
        """
        try:
            if not self.detection_history:
                return self._obtener_umbrales_base()
            
            # Calcular rendimiento promedio
            rendimiento_promedio = np.mean([d['count'] for d in self.detection_history])
            
            # Calcular factor de ajuste
            if detecciones_actuales < detecciones_esperadas:
                # Pocas detecciones: reducir umbrales
                factor_ajuste = 0.9
            elif detecciones_actuales > detecciones_esperadas * 2:
                # Demasiadas detecciones: aumentar umbrales
                factor_ajuste = 1.1
            else:
                # Rendimiento normal
                factor_ajuste = 1.0
            
            # Obtener umbrales base
            umbrales = self._obtener_umbrales_base()
            
            # Aplicar ajuste
            umbrales['confianza_min'] *= factor_ajuste
            umbrales['area_minima'] *= factor_ajuste
            umbrales['cobertura_minima'] *= factor_ajuste
            
            # Aplicar límites
            umbrales['confianza_min'] = np.clip(umbrales['confianza_min'], 
                                              self.confianza_min, self.confianza_max)
            umbrales['area_minima'] = np.clip(umbrales['area_minima'], 
                                            self.area_min, self.area_max)
            umbrales['cobertura_minima'] = np.clip(umbrales['cobertura_minima'], 
                                                 self.cobertura_min, self.cobertura_max)
            
            return umbrales
            
        except Exception as e:
            self.logger.error(f"Error ajustando umbrales por rendimiento: {e}")
            return self._obtener_umbrales_base()
    
    def obtener_umbrales_hibridos(self, brightness: float, contrast: float, 
                                detecciones_actuales: int) -> Dict[str, float]:
        """
        Obtiene umbrales híbridos combinando iluminación y rendimiento
        
        Args:
            brightness (float): Brillo de la imagen
            contrast (float): Contraste de la imagen
            detecciones_actuales (int): Número de detecciones actuales
            
        Returns:
            Dict[str, float]: Umbrales híbridos
        """
        try:
            # Obtener umbrales basados en iluminación
            umbrales_iluminacion = self.calcular_umbrales_adaptativos(brightness, contrast)
            
            # Obtener umbrales basados en rendimiento
            umbrales_rendimiento = self.ajustar_umbrales_por_rendimiento(detecciones_actuales)
            
            # Combinar ambos (promedio ponderado)
            umbrales_hibridos = {
                'confianza_min': (umbrales_iluminacion['confianza_min'] + 
                                umbrales_rendimiento['confianza_min']) / 2,
                'area_minima': (umbrales_iluminacion['area_minima'] + 
                              umbrales_rendimiento['area_minima']) / 2,
                'cobertura_minima': (umbrales_iluminacion['cobertura_minima'] + 
                                   umbrales_rendimiento['cobertura_minima']) / 2,
                'brightness_factor': umbrales_iluminacion['brightness_factor'],
                'contrast_factor': umbrales_iluminacion['contrast_factor']
            }
            
            # Aplicar límites
            umbrales_hibridos['confianza_min'] = np.clip(umbrales_hibridos['confianza_min'], 
                                                       self.confianza_min, self.confianza_max)
            umbrales_hibridos['area_minima'] = np.clip(umbrales_hibridos['area_minima'], 
                                                     self.area_min, self.area_max)
            umbrales_hibridos['cobertura_minima'] = np.clip(umbrales_hibridos['cobertura_minima'], 
                                                          self.cobertura_min, self.cobertura_max)
            
            return umbrales_hibridos
            
        except Exception as e:
            self.logger.error(f"Error obteniendo umbrales híbridos: {e}")
            return self._obtener_umbrales_base()
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del sistema de umbrales adaptativos
        
        Returns:
            Dict[str, Any]: Estadísticas del sistema
        """
        try:
            stats = {
                'detection_history_size': len(self.detection_history),
                'illumination_history_size': len(self.illumination_history),
                'umbrales_base': self._obtener_umbrales_base()
            }
            
            if self.detection_history:
                stats['detection_stats'] = {
                    'count_mean': np.mean([d['count'] for d in self.detection_history]),
                    'count_std': np.std([d['count'] for d in self.detection_history]),
                    'confianza_mean': np.mean([d['confianza_promedio'] for d in self.detection_history]),
                    'area_mean': np.mean([d['area_promedio'] for d in self.detection_history])
                }
            
            if self.illumination_history:
                stats['illumination_stats'] = {
                    'brightness_mean': np.mean([i['brightness'] for i in self.illumination_history]),
                    'brightness_std': np.std([i['brightness'] for i in self.illumination_history]),
                    'contrast_mean': np.mean([i['contrast'] for i in self.illumination_history]),
                    'contrast_std': np.std([i['contrast'] for i in self.illumination_history])
                }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
