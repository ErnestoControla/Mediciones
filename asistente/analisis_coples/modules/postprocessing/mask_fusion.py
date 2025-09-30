#!/usr/bin/env python3
"""
Sistema de fusión de máscaras para objetos pegados
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging

class FusionadorMascaras:
    """
    Clase para fusionar máscaras de objetos que están muy cerca o pegados
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Parámetros de fusión
        self.distancia_maxima = 50  # píxeles - distancia máxima para considerar objetos "pegados"
        self.overlap_minimo = 0.1   # 10% de overlap mínimo para fusionar
        self.area_minima_fusion = 100  # área mínima para considerar fusión
        
        # Parámetros de análisis de conectividad
        self.kernel_conectividad = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        
    def analizar_conectividad_mascaras(self, mascaras: List[np.ndarray]) -> List[Dict]:
        """
        Analiza la conectividad entre máscaras para detectar objetos pegados
        
        Args:
            mascaras: Lista de máscaras (arrays numpy)
            
        Returns:
            Lista de diccionarios con información de conectividad
        """
        try:
            resultados = []
            
            for i, mascara in enumerate(mascaras):
                # Encontrar contornos
                contornos, _ = cv2.findContours(
                    mascara.astype(np.uint8), 
                    cv2.RETR_EXTERNAL, 
                    cv2.CHAIN_APPROX_SIMPLE
                )
                
                if len(contornos) == 0:
                    continue
                
                # Obtener el contorno más grande
                contorno_principal = max(contornos, key=cv2.contourArea)
                
                # Calcular propiedades del contorno
                area = cv2.contourArea(contorno_principal)
                perimetro = cv2.arcLength(contorno_principal, True)
                
                # Calcular bounding box
                x, y, w, h = cv2.boundingRect(contorno_principal)
                
                # Calcular centroide
                M = cv2.moments(contorno_principal)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                else:
                    cx, cy = x + w//2, y + h//2
                
                # Calcular compacidad (forma circular)
                compacidad = (4 * np.pi * area) / (perimetro * perimetro) if perimetro > 0 else 0
                
                resultados.append({
                    'indice': i,
                    'mascara': mascara,
                    'contorno': contorno_principal,
                    'area': area,
                    'perimetro': perimetro,
                    'bbox': (x, y, w, h),
                    'centroide': (cx, cy),
                    'compacidad': compacidad,
                    'es_circular': compacidad > 0.7  # Objetos circulares son menos propensos a estar pegados
                })
            
            return resultados
            
        except Exception as e:
            self.logger.error(f"Error analizando conectividad: {e}")
            return []
    
    def calcular_distancia_entre_mascaras(self, mascara1_info: Dict, mascara2_info: Dict) -> float:
        """
        Calcula la distancia mínima entre dos máscaras
        
        Args:
            mascara1_info: Información de la primera máscara
            mascara2_info: Información de la segunda máscara
            
        Returns:
            Distancia mínima en píxeles
        """
        try:
            # Calcular distancia entre centroides
            centroide1 = mascara1_info['centroide']
            centroide2 = mascara2_info['centroide']
            distancia_centroides = np.sqrt(
                (centroide1[0] - centroide2[0])**2 + 
                (centroide1[1] - centroide2[1])**2
            )
            
            # Calcular distancia entre bounding boxes
            bbox1 = mascara1_info['bbox']
            bbox2 = mascara2_info['bbox']
            
            # Calcular distancia entre rectángulos
            x1, y1, w1, h1 = bbox1
            x2, y2, w2, h2 = bbox2
            
            # Calcular distancia mínima entre rectángulos
            dx = max(0, max(x1, x2) - min(x1 + w1, x2 + w2))
            dy = max(0, max(y1, y2) - min(y1 + h1, y2 + h2))
            distancia_bbox = np.sqrt(dx*dx + dy*dy)
            
            # Usar la menor de las dos distancias
            return min(distancia_centroides, distancia_bbox)
            
        except Exception as e:
            self.logger.error(f"Error calculando distancia: {e}")
            return float('inf')
    
    def calcular_overlap_mascaras(self, mascara1: np.ndarray, mascara2: np.ndarray) -> float:
        """
        Calcula el porcentaje de overlap entre dos máscaras
        
        Args:
            mascara1: Primera máscara
            mascara2: Segunda máscara
            
        Returns:
            Porcentaje de overlap (0.0 a 1.0)
        """
        try:
            # Calcular intersección
            interseccion = np.logical_and(mascara1 > 0.5, mascara2 > 0.5)
            area_interseccion = np.sum(interseccion)
            
            # Calcular unión
            union = np.logical_or(mascara1 > 0.5, mascara2 > 0.5)
            area_union = np.sum(union)
            
            # Calcular overlap como intersección / unión
            if area_union > 0:
                return area_interseccion / area_union
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Error calculando overlap: {e}")
            return 0.0
    
    def fusionar_mascaras(self, mascara1: np.ndarray, mascara2: np.ndarray) -> np.ndarray:
        """
        Fusiona dos máscaras en una sola
        
        Args:
            mascara1: Primera máscara
            mascara2: Segunda máscara
            
        Returns:
            Máscara fusionada
        """
        try:
            # Combinar máscaras usando OR lógico
            mascara_fusionada = np.logical_or(mascara1 > 0.5, mascara2 > 0.5).astype(np.float32)
            
            # Aplicar operaciones morfológicas para suavizar
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            mascara_fusionada = cv2.morphologyEx(mascara_fusionada, cv2.MORPH_CLOSE, kernel, iterations=1)
            
            return mascara_fusionada
            
        except Exception as e:
            self.logger.error(f"Error fusionando máscaras: {e}")
            return mascara1  # Retornar la primera máscara como fallback
    
    def detectar_objetos_pegados(self, mascaras_info: List[Dict]) -> List[List[int]]:
        """
        Detecta grupos de máscaras que representan objetos pegados
        
        Args:
            mascaras_info: Lista de información de máscaras
            
        Returns:
            Lista de grupos de índices de máscaras que deben fusionarse
        """
        try:
            grupos_fusion = []
            mascaras_procesadas = set()
            
            for i, mascara1_info in enumerate(mascaras_info):
                if i in mascaras_procesadas:
                    continue
                
                grupo_actual = [i]
                mascaras_procesadas.add(i)
                
                # Buscar máscaras cercanas
                for j, mascara2_info in enumerate(mascaras_info):
                    if j <= i or j in mascaras_procesadas:
                        continue
                    
                    # Calcular distancia
                    distancia = self.calcular_distancia_entre_mascaras(mascara1_info, mascara2_info)
                    
                    # Calcular overlap
                    overlap = self.calcular_overlap_mascaras(
                        mascara1_info['mascara'], 
                        mascara2_info['mascara']
                    )
                    
                    # Criterios para considerar objetos pegados
                    objetos_pegados = (
                        distancia < self.distancia_maxima and
                        overlap > self.overlap_minimo and
                        mascara1_info['area'] > self.area_minima_fusion and
                        mascara2_info['area'] > self.area_minima_fusion
                    )
                    
                    if objetos_pegados:
                        grupo_actual.append(j)
                        mascaras_procesadas.add(j)
                        print(f"   🔗 Objetos pegados detectados: {i} y {j}")
                        print(f"      Distancia: {distancia:.1f}px, Overlap: {overlap:.2%}")
                
                # Si el grupo tiene más de una máscara, agregarlo a la lista
                if len(grupo_actual) > 1:
                    grupos_fusion.append(grupo_actual)
            
            return grupos_fusion
            
        except Exception as e:
            self.logger.error(f"Error detectando objetos pegados: {e}")
            return []
    
    def procesar_segmentaciones(self, segmentaciones: List[Dict]) -> List[Dict]:
        """
        Procesa una lista de segmentaciones para fusionar objetos pegados
        
        Args:
            segmentaciones: Lista de diccionarios con segmentaciones
            
        Returns:
            Lista de segmentaciones procesadas con objetos fusionados
        """
        try:
            if len(segmentaciones) <= 1:
                return segmentaciones
            
            print(f"🔍 Analizando {len(segmentaciones)} segmentaciones para objetos pegados...")
            
            # Extraer máscaras
            mascaras = [seg.get('mascara') for seg in segmentaciones if seg.get('mascara') is not None]
            
            if len(mascaras) == 0:
                return segmentaciones
            
            # Analizar conectividad
            mascaras_info = self.analizar_conectividad_mascaras(mascaras)
            
            if len(mascaras_info) == 0:
                return segmentaciones
            
            # Detectar objetos pegados
            grupos_fusion = self.detectar_objetos_pegados(mascaras_info)
            
            if len(grupos_fusion) == 0:
                print("   ✅ No se detectaron objetos pegados")
                return segmentaciones
            
            print(f"   🔗 Se detectaron {len(grupos_fusion)} grupos de objetos pegados")
            
            # Crear lista de segmentaciones procesadas
            segmentaciones_procesadas = []
            indices_fusionados = set()
            
            # Procesar cada grupo de fusión
            for grupo in grupos_fusion:
                print(f"   🔧 Fusionando grupo: {grupo}")
                
                # Fusionar máscaras del grupo
                mascara_fusionada = mascaras_info[grupo[0]]['mascara']
                for idx in grupo[1:]:
                    mascara_fusionada = self.fusionar_mascaras(
                        mascara_fusionada, 
                        mascaras_info[idx]['mascara']
                    )
                
                # Crear nueva segmentación fusionada
                segmentacion_fusionada = self._crear_segmentacion_fusionada(
                    segmentaciones, grupo, mascara_fusionada
                )
                
                segmentaciones_procesadas.append(segmentacion_fusionada)
                indices_fusionados.update(grupo)
            
            # Agregar segmentaciones no fusionadas
            for i, seg in enumerate(segmentaciones):
                if i not in indices_fusionados:
                    segmentaciones_procesadas.append(seg)
            
            print(f"   ✅ Procesamiento completado: {len(segmentaciones)} → {len(segmentaciones_procesadas)} segmentaciones")
            
            return segmentaciones_procesadas
            
        except Exception as e:
            self.logger.error(f"Error procesando segmentaciones: {e}")
            return segmentaciones
    
    def _crear_segmentacion_fusionada(self, segmentaciones: List[Dict], 
                                    grupo: List[int], mascara_fusionada: np.ndarray) -> Dict:
        """
        Crea una nueva segmentación fusionada a partir de un grupo de segmentaciones
        
        Args:
            segmentaciones: Lista original de segmentaciones
            grupo: Índices de las segmentaciones a fusionar
            mascara_fusionada: Máscara fusionada
            
        Returns:
            Nueva segmentación fusionada
        """
        try:
            # Usar la primera segmentación como base
            base = segmentaciones[grupo[0]].copy()
            
            # Calcular nuevas propiedades de la máscara fusionada
            area_fusionada = int(np.sum(mascara_fusionada > 0.5))
            
            # Encontrar contornos de la máscara fusionada
            contornos, _ = cv2.findContours(
                mascara_fusionada.astype(np.uint8), 
                cv2.RETR_EXTERNAL, 
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            if len(contornos) > 0:
                contorno_principal = max(contornos, key=cv2.contourArea)
                
                # Calcular nuevo bounding box
                x, y, w, h = cv2.boundingRect(contorno_principal)
                
                # Calcular nuevo centroide
                M = cv2.moments(contorno_principal)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                else:
                    cx, cy = x + w//2, y + h//2
                
                # Actualizar propiedades
                base['mascara'] = mascara_fusionada
                base['area_mascara'] = area_fusionada
                base['bbox'] = {'x1': x, 'y1': y, 'x2': x + w, 'y2': y + h}
                base['centroide'] = {'x': cx, 'y': cy}
                base['ancho_mascara'] = w
                base['alto_mascara'] = h
                
                # Calcular confianza promedio del grupo
                confianzas = [segmentaciones[i].get('confianza', 0) for i in grupo]
                base['confianza'] = np.mean(confianzas)
                
                # Marcar como fusionada
                base['fusionada'] = True
                base['objetos_fusionados'] = len(grupo)
            
            return base
            
        except Exception as e:
            self.logger.error(f"Error creando segmentación fusionada: {e}")
            return segmentaciones[grupo[0]]  # Fallback a la primera segmentación
    
    def configurar_parametros(self, distancia_maxima: int = None, 
                            overlap_minimo: float = None,
                            area_minima_fusion: int = None):
        """
        Configura los parámetros de fusión
        
        Args:
            distancia_maxima: Distancia máxima en píxeles para considerar objetos pegados
            overlap_minimo: Overlap mínimo para fusionar (0.0 a 1.0)
            area_minima_fusion: Área mínima para considerar fusión
        """
        if distancia_maxima is not None:
            self.distancia_maxima = distancia_maxima
            print(f"✅ Distancia máxima configurada: {distancia_maxima}px")
        
        if overlap_minimo is not None:
            self.overlap_minimo = overlap_minimo
            print(f"✅ Overlap mínimo configurado: {overlap_minimo:.2%}")
        
        if area_minima_fusion is not None:
            self.area_minima_fusion = area_minima_fusion
            print(f"✅ Área mínima de fusión configurada: {area_minima_fusion}px")
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene estadísticas del fusionador
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'distancia_maxima': self.distancia_maxima,
            'overlap_minimo': self.overlap_minimo,
            'area_minima_fusion': self.area_minima_fusion
        }
