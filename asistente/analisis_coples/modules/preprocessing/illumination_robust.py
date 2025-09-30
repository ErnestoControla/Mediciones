#!/usr/bin/env python3
"""
Módulo para robustez ante cambios de iluminación
"""

import cv2
import numpy as np
from typing import Tuple, Optional, Dict, Any
import logging

class RobustezIluminacion:
    """
    Clase para hacer el sistema más robusto ante cambios de iluminación
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Parámetros de normalización
        self.target_mean = 128.0
        self.target_std = 64.0
        
        # Parámetros de CLAHE (Contrast Limited Adaptive Histogram Equalization)
        self.clahe_clip_limit = 2.0
        self.clahe_tile_grid_size = (8, 8)
        
        # Parámetros de gamma correction adaptativo
        self.gamma_range = (0.5, 2.0)
        self.gamma_step = 0.1
        
        # Historial de iluminación para adaptación
        self.illumination_history = []
        self.max_history = 10
        
    def normalizar_imagen_adaptativa(self, imagen: np.ndarray) -> np.ndarray:
        """
        Normaliza la imagen adaptativamente - VERSIÓN SIMPLIFICADA
        
        Args:
            imagen (np.ndarray): Imagen de entrada (BGR)
            
        Returns:
            np.ndarray: Imagen normalizada
        """
        try:
            # Convertir a float32 para cálculos precisos
            img_float = imagen.astype(np.float32)
            
            # Calcular estadísticas globales
            mean_global = np.mean(img_float)
            std_global = np.std(img_float)
            
            # Normalización global simple
            if std_global > 0:
                img_normalized = (img_float - mean_global) / std_global
                img_normalized = img_normalized * self.target_std + self.target_mean
            else:
                img_normalized = img_float
            
            # Asegurar que los valores estén en el rango [0, 255]
            img_normalized = np.clip(img_normalized, 0, 255)
            
            return img_normalized.astype(np.uint8)
            
        except Exception as e:
            self.logger.error(f"Error en normalización adaptativa: {e}")
            return imagen
    
    def aplicar_clahe(self, imagen: np.ndarray) -> np.ndarray:
        """
        Aplica CLAHE (Contrast Limited Adaptive Histogram Equalization)
        
        Args:
            imagen (np.ndarray): Imagen de entrada (BGR)
            
        Returns:
            np.ndarray: Imagen con CLAHE aplicado
        """
        try:
            # Convertir a LAB
            lab = cv2.cvtColor(imagen, cv2.COLOR_BGR2LAB)
            
            # Aplicar CLAHE al canal L
            clahe = cv2.createCLAHE(
                clipLimit=self.clahe_clip_limit,
                tileGridSize=self.clahe_tile_grid_size
            )
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            
            # Convertir de vuelta a BGR
            return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
        except Exception as e:
            self.logger.error(f"Error aplicando CLAHE: {e}")
            return imagen
    
    def gamma_correction_adaptativo(self, imagen: np.ndarray) -> np.ndarray:
        """
        Aplica gamma correction adaptativo basándose en el brillo de la imagen
        
        Args:
            imagen (np.ndarray): Imagen de entrada (BGR)
            
        Returns:
            np.ndarray: Imagen con gamma correction aplicado
        """
        try:
            # Calcular brillo promedio
            brightness = np.mean(imagen)
            
            # Determinar gamma basándose en el brillo
            if brightness < 80:  # Imagen oscura
                gamma = 0.7
            elif brightness > 180:  # Imagen muy brillante
                gamma = 1.3
            else:  # Imagen normal
                gamma = 1.0
            
            # Aplicar gamma correction
            gamma_corrected = np.power(imagen / 255.0, gamma) * 255.0
            return np.clip(gamma_corrected, 0, 255).astype(np.uint8)
            
        except Exception as e:
            self.logger.error(f"Error en gamma correction: {e}")
            return imagen
    
    def mejorar_contraste_adaptativo(self, imagen: np.ndarray) -> np.ndarray:
        """
        Mejora el contraste de manera adaptativa
        
        Args:
            imagen (np.ndarray): Imagen de entrada (BGR)
            
        Returns:
            np.ndarray: Imagen con contraste mejorado
        """
        try:
            # Calcular histograma
            hist = cv2.calcHist([imagen], [0], None, [256], [0, 256])
            
            # Encontrar percentiles
            total_pixels = imagen.shape[0] * imagen.shape[1]
            p1 = np.percentile(hist, 1)
            p99 = np.percentile(hist, 99)
            
            # Aplicar estiramiento de histograma
            if p99 > p1:
                img_stretched = np.clip(
                    (imagen - p1) * 255.0 / (p99 - p1), 0, 255
                ).astype(np.uint8)
            else:
                img_stretched = imagen
            
            return img_stretched
            
        except Exception as e:
            self.logger.error(f"Error mejorando contraste: {e}")
            return imagen
    
    def preprocesar_imagen_robusta(self, imagen: np.ndarray, 
                                 aplicar_clahe: bool = True,
                                 aplicar_gamma: bool = True,
                                 aplicar_contraste: bool = True) -> np.ndarray:
        """
        Aplica múltiples técnicas de preprocesamiento para robustez
        
        Args:
            imagen (np.ndarray): Imagen de entrada (BGR)
            aplicar_clahe (bool): Si aplicar CLAHE
            aplicar_gamma (bool): Si aplicar gamma correction
            aplicar_contraste (bool): Si aplicar mejora de contraste
            
        Returns:
            np.ndarray: Imagen preprocesada
        """
        try:
            img_processed = imagen.copy()
            
            # 1. Normalización adaptativa
            img_processed = self.normalizar_imagen_adaptativa(img_processed)
            
            # 2. CLAHE para mejorar contraste local
            if aplicar_clahe:
                img_processed = self.aplicar_clahe(img_processed)
            
            # 3. Gamma correction adaptativo
            if aplicar_gamma:
                img_processed = self.gamma_correction_adaptativo(img_processed)
            
            # 4. Mejora de contraste
            if aplicar_contraste:
                img_processed = self.mejorar_contraste_adaptativo(img_processed)
            
            return img_processed
            
        except Exception as e:
            self.logger.error(f"Error en preprocesamiento robusto: {e}")
            return imagen
    
    def analizar_iluminacion(self, imagen: np.ndarray) -> Dict[str, float]:
        """
        Analiza las características de iluminación de la imagen
        
        Args:
            imagen (np.ndarray): Imagen de entrada (BGR)
            
        Returns:
            Dict[str, float]: Métricas de iluminación
        """
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
            
            # Calcular métricas
            brightness = np.mean(gray)
            contrast = np.std(gray)
            
            # Calcular histograma
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            
            # Encontrar percentiles
            total_pixels = gray.shape[0] * gray.shape[1]
            p5 = np.percentile(hist, 5)
            p95 = np.percentile(hist, 95)
            
            # Calcular rango dinámico
            dynamic_range = p95 - p5
            
            # Calcular entropía (medida de información)
            hist_norm = hist / total_pixels
            entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))
            
            metrics = {
                'brightness': float(brightness),
                'contrast': float(contrast),
                'dynamic_range': float(dynamic_range),
                'entropy': float(entropy),
                'p5': float(p5),
                'p95': float(p95)
            }
            
            # Guardar en historial
            self.illumination_history.append(metrics)
            if len(self.illumination_history) > self.max_history:
                self.illumination_history.pop(0)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error analizando iluminación: {e}")
            return {}
    
    def obtener_estadisticas_iluminacion(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del historial de iluminación
        
        Returns:
            Dict[str, Any]: Estadísticas de iluminación
        """
        if not self.illumination_history:
            return {}
        
        try:
            # Extraer métricas
            brightness_values = [m['brightness'] for m in self.illumination_history]
            contrast_values = [m['contrast'] for m in self.illumination_history]
            
            stats = {
                'brightness_mean': np.mean(brightness_values),
                'brightness_std': np.std(brightness_values),
                'contrast_mean': np.mean(contrast_values),
                'contrast_std': np.std(contrast_values),
                'samples': len(self.illumination_history)
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def recomendar_ajustes(self, imagen: np.ndarray) -> Dict[str, Any]:
        """
        Recomienda ajustes basándose en el análisis de iluminación
        
        Args:
            imagen (np.ndarray): Imagen de entrada (BGR)
            
        Returns:
            Dict[str, Any]: Recomendaciones de ajuste
        """
        try:
            metrics = self.analizar_iluminacion(imagen)
            
            if not metrics:
                return {}
            
            recommendations = {
                'aplicar_clahe': False,
                'aplicar_gamma': False,
                'aplicar_contraste': False,
                'gamma_value': 1.0,
                'contrast_factor': 1.0
            }
            
            # Recomendaciones basadas en brillo
            if metrics['brightness'] < 80:
                recommendations['aplicar_gamma'] = True
                recommendations['gamma_value'] = 0.7
                recommendations['aplicar_contraste'] = True
            elif metrics['brightness'] > 180:
                recommendations['aplicar_gamma'] = True
                recommendations['gamma_value'] = 1.3
            
            # Recomendaciones basadas en contraste
            if metrics['contrast'] < 30:
                recommendations['aplicar_clahe'] = True
                recommendations['aplicar_contraste'] = True
                recommendations['contrast_factor'] = 1.5
            
            # Recomendaciones basadas en rango dinámico
            if metrics['dynamic_range'] < 100:
                recommendations['aplicar_clahe'] = True
                recommendations['aplicar_contraste'] = True
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generando recomendaciones: {e}")
            return {}
