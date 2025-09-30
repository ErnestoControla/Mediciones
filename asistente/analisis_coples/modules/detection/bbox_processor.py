"""
Procesador de Bounding Boxes para Detección
Maneja la visualización y análisis de detecciones
"""

import numpy as np
import cv2
from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime
import os
import sys

# Agregar path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from modules.metadata_standard import MetadataStandard


class ProcesadorBoundingBoxes:
    """
    Procesa y visualiza bounding boxes de detecciones
    """
    
    def __init__(self):
        """Inicializa el procesador de bounding boxes"""
        # Colores para diferentes clases (BGR)
        self.colores_clases = {
            "Pieza_Cople": (0, 255, 0),      # Verde
            "default": (255, 0, 0)            # Azul por defecto
        }
        
        # Configuración de visualización
        self.grosor_linea = 2
        self.tamano_fuente = 0.6
        self.espesor_fuente = 1
        self.margen_texto = 5
    
    def dibujar_detecciones(self, imagen: np.ndarray, detecciones: List[Dict]) -> np.ndarray:
        """
        Dibuja las detecciones sobre la imagen
        
        Args:
            imagen: Imagen original RGB
            detecciones: Lista de detecciones
            
        Returns:
            Imagen con bounding boxes dibujados
        """
        imagen_anotada = imagen.copy()
        
        print(f"🎨 Dibujando {len(detecciones)} detecciones...")
        
        for i, deteccion in enumerate(detecciones):
            # Obtener información de la detección
            bbox = deteccion["bbox"]
            clase = deteccion["clase"]
            confianza = deteccion["confianza"]
            centroide = deteccion["centroide"]
            
            # Validar bounding box
            x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
            
            # Verificar que las coordenadas sean válidas
            if x1 >= x2 or y1 >= y2:
                print(f"⚠️ Bounding box inválido para detección {i}: ({x1},{y1}) a ({x2},{y2})")
                continue
            
            # Verificar que esté dentro de la imagen
            if x1 < 0 or y1 < 0 or x2 > imagen.shape[1] or y2 > imagen.shape[0]:
                print(f"⚠️ Bounding box fuera de imagen para detección {i}: ({x1},{y1}) a ({x2},{y2})")
                continue
            
            print(f"🎨 Dibujando detección {i+1}: {clase} en ({x1},{y1}) a ({x2},{y2})")
            
            # Obtener color para la clase
            color = self.colores_clases.get(clase, self.colores_clases["default"])
            
            # Dibujar bounding box
            cv2.rectangle(imagen_anotada, (x1, y1), (x2, y2), color, self.grosor_linea)
            
            # Dibujar centroide (asegurar que sean enteros)
            cx, cy = int(centroide["x"]), int(centroide["y"])
            cv2.circle(imagen_anotada, (cx, cy), 3, color, -1)
            
            # Preparar texto de etiqueta (mostrar confianza como porcentaje)
            confianza_porcentaje = min(confianza, 1.0) * 100  # Limitar a 100%
            texto_etiqueta = f"{clase}: {confianza_porcentaje:.1f}%"
            
            # Calcular posición del texto
            (texto_ancho, texto_alto), _ = cv2.getTextSize(
                texto_etiqueta, cv2.FONT_HERSHEY_SIMPLEX, 
                self.tamano_fuente, self.espesor_fuente
            )
            
            # Posición del texto (arriba del bounding box)
            texto_x = x1
            texto_y = y1 - self.margen_texto
            
            # Si el texto se sale por arriba, ponerlo abajo
            if texto_y < texto_alto + self.margen_texto:
                texto_y = y2 + texto_alto + self.margen_texto
            
            # Dibujar fondo del texto
            cv2.rectangle(
                imagen_anotada,
                (texto_x, texto_y - texto_alto - self.margen_texto),
                (texto_x + texto_ancho + self.margen_texto, texto_y + self.margen_texto),
                color, -1
            )
            
            # Dibujar texto
            cv2.putText(
                imagen_anotada, texto_etiqueta,
                (texto_x + self.margen_texto, texto_y),
                cv2.FONT_HERSHEY_SIMPLEX, self.tamano_fuente,
                (255, 255, 255), self.espesor_fuente
            )
            
            # Agregar número de detección
            texto_numero = f"#{i+1}"
            cv2.putText(
                imagen_anotada, texto_numero,
                (x2 - 20, y1 + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                color, self.espesor_fuente
            )
        
        return imagen_anotada
    
    def agregar_informacion_tiempo(self, imagen: np.ndarray, tiempos: Dict) -> np.ndarray:
        """
        Agrega información de tiempos sobre la imagen
        
        Args:
            imagen: Imagen a anotar
            tiempos: Diccionario con tiempos de procesamiento
            
        Returns:
            Imagen con información de tiempos
        """
        imagen_anotada = imagen.copy()
        
        # Información de tiempos
        info_tiempos = [
            f"Captura: {tiempos.get('captura_ms', 0):.2f} ms",
            f"Detección: {tiempos.get('deteccion_ms', 0):.2f} ms",
            f"Total: {tiempos.get('total_ms', 0):.2f} ms"
        ]
        
        # Posición inicial (esquina superior derecha)
        pos_x = imagen.shape[1] - 200
        pos_y = 30
        
        for i, info in enumerate(info_tiempos):
            # Fondo del texto
            cv2.rectangle(
                imagen_anotada,
                (pos_x - 5, pos_y + i * 20 - 15),
                (pos_x + 190, pos_y + i * 20 + 5),
                (0, 0, 0), -1
            )
            
            # Texto
            cv2.putText(
                imagen_anotada, info,
                (pos_x, pos_y + i * 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (255, 255, 255), 1
            )
        
        return imagen_anotada
    
    def crear_metadatos_deteccion(self, detecciones: List[Dict], tiempos: Dict, 
                                 nombre_archivo: str, modelo: str, tipo_deteccion: str = "piezas") -> Dict:
        """
        Crea metadatos JSON para las detecciones usando estructura estándar
        
        Args:
            detecciones: Lista de detecciones
            tiempos: Diccionario con tiempos
            nombre_archivo: Nombre del archivo de imagen
            modelo: Nombre del modelo usado
            tipo_deteccion: Tipo de detección (piezas o defectos)
            
        Returns:
            Diccionario con metadatos
        """
        # Usar estructura estándar de metadatos
        metadatos = MetadataStandard.crear_metadatos_completos(
            tipo_analisis=f"deteccion_{tipo_deteccion}",
            archivo_imagen=nombre_archivo,
            resultados=detecciones,
            tiempos=tiempos
        )
        
        return metadatos
    
    def guardar_resultado_deteccion(self, imagen: np.ndarray, detecciones: List[Dict], 
                                   tiempos: Dict, directorio_salida: str, 
                                   prefijo: str = "cople_deteccion", 
                                   timestamp_captura: str = None) -> Tuple[str, str]:
        """
        Guarda la imagen anotada y los metadatos JSON
        
        Args:
            imagen: Imagen con bounding boxes dibujados
            detecciones: Lista de detecciones
            tiempos: Diccionario con tiempos
            directorio_salida: Directorio donde guardar
            prefijo: Prefijo para el nombre del archivo
            timestamp_captura: Timestamp único de la captura
            
        Returns:
            Tupla con (ruta_imagen, ruta_json)
        """
        # Usar timestamp de captura si está disponible, sino crear uno nuevo
        if timestamp_captura:
            timestamp = timestamp_captura
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Nombre del archivo
        nombre_base = f"{prefijo}_{timestamp}"
        nombre_imagen = f"{nombre_base}.jpg"
        nombre_json = f"{nombre_base}.json"
        
        # Rutas completas
        ruta_imagen = os.path.join(directorio_salida, nombre_imagen)
        ruta_json = os.path.join(directorio_salida, nombre_json)
        
        # Guardar imagen
        cv2.imwrite(ruta_imagen, imagen)
        
        # Crear y guardar metadatos
        metadatos = self.crear_metadatos_deteccion(
            detecciones, tiempos, nombre_imagen, "CopleDetPz1C1V.onnx"
        )
        
        with open(ruta_json, 'w', encoding='utf-8') as f:
            json.dump(metadatos, f, indent=2, ensure_ascii=False)
        
        return ruta_imagen, ruta_json
    
    def analizar_detecciones(self, detecciones: List[Dict]) -> Dict:
        """
        Analiza las detecciones y genera estadísticas
        
        Args:
            detecciones: Lista de detecciones
            
        Returns:
            Diccionario con estadísticas
        """
        if not detecciones:
            return {
                "total_piezas": 0,
                "confianza_promedio": 0,
                "confianza_maxima": 0,
                "confianza_minima": 0,
                "areas": [],
                "distribucion_clases": {}
            }
        
        # Estadísticas básicas
        confianzas = [d["confianza"] for d in detecciones]
        areas = [d["area"] for d in detecciones]
        clases = [d["clase"] for d in detecciones]
        
        # Distribución de clases
        distribucion_clases = {}
        for clase in clases:
            distribucion_clases[clase] = clases.count(clase)
        
        estadisticas = {
            "total_piezas": len(detecciones),
            "confianza_promedio": np.mean(confianzas),
            "confianza_maxima": max(confianzas),
            "confianza_minima": min(confianzas),
            "confianza_std": np.std(confianzas),
            "area_promedio": np.mean(areas),
            "area_maxima": max(areas),
            "area_minima": min(areas),
            "areas": areas,
            "distribucion_clases": distribucion_clases
        }
        
        return estadisticas


class ProcesadorPiezasCoples(ProcesadorBoundingBoxes):
    """
    Procesador específico para piezas de coples
    """
    
    def __init__(self):
        """Inicializa procesador de piezas de coples"""
        super().__init__()
        
        # Colores específicos para piezas de coples
        self.colores_clases.update({
            "Pieza_Cople": (0, 255, 0),      # Verde
            "Cople_Completo": (255, 0, 0),   # Azul
            "Cople_Parcial": (0, 0, 255)     # Rojo
        })
    
    def procesar_deteccion_piezas(self, imagen: np.ndarray, detecciones: List[Dict], 
                                  tiempos: Dict, directorio_salida: str, 
                                  timestamp_captura: str = None) -> Tuple[str, str]:
        """
        Procesa y guarda detección de piezas de coples
        
        Args:
            imagen: Imagen original
            detecciones: Lista de detecciones
            tiempos: Diccionario con tiempos
            directorio_salida: Directorio de salida
            timestamp_captura: Timestamp único de la captura
            
        Returns:
            Tupla con (ruta_imagen, ruta_json)
        """
        # Dibujar detecciones
        imagen_anotada = self.dibujar_detecciones(imagen, detecciones)
        
        # Agregar información de tiempo
        imagen_anotada = self.agregar_informacion_tiempo(imagen_anotada, tiempos)
        
        # Guardar resultado
        return self.guardar_resultado_deteccion(
            imagen_anotada, detecciones, tiempos, 
            directorio_salida, "cople_deteccion_piezas", timestamp_captura
        )
