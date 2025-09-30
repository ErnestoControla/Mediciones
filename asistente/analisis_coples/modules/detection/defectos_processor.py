"""
Procesador de Defectos para Detección
Maneja la visualización y análisis de detecciones de defectos
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


class ProcesadorDefectos:
    """
    Procesa y visualiza detecciones de defectos
    """
    
    def __init__(self):
        """Inicializa el procesador de defectos"""
        # Colores para diferentes tipos de defectos (BGR)
        self.colores_defectos = {
            "Defecto_1": (0, 0, 255),      # Rojo
            "Defecto_2": (0, 255, 255),    # Amarillo
            "default": (255, 0, 0)          # Azul por defecto
        }
        
        # Configuración de visualización
        self.grosor_linea = 2
        self.tamano_fuente = 0.6
        self.espesor_fuente = 1
        self.margen_texto = 5
    
    def dibujar_defectos(self, imagen: np.ndarray, defectos: List[Dict]) -> np.ndarray:
        """
        Dibuja las detecciones de defectos sobre la imagen
        
        Args:
            imagen: Imagen original RGB
            defectos: Lista de detecciones de defectos
            
        Returns:
            Imagen con bounding boxes dibujados
        """
        imagen_anotada = imagen.copy()
        
        print(f"🎨 Dibujando {len(defectos)} defectos...")
        
        for i, defecto in enumerate(defectos):
            # Obtener información de la detección
            bbox = defecto["bbox"]
            clase = defecto["clase"]
            confianza = defecto["confianza"]
            centroide = defecto["centroide"]
            
            # Validar bounding box
            x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
            
            # Verificar que las coordenadas sean válidas
            if x1 >= x2 or y1 >= y2:
                print(f"⚠️ Bounding box inválido para defecto {i}: ({x1},{y1}) a ({x2},{y2})")
                continue
            
            # Verificar que esté dentro de la imagen
            if x1 < 0 or y1 < 0 or x2 > imagen.shape[1] or y2 > imagen.shape[0]:
                print(f"⚠️ Bounding box fuera de imagen para defecto {i}: ({x1},{y1}) a ({x2},{y2})")
                continue
            
            print(f"🎨 Dibujando defecto {i+1}: {clase} en ({x1},{y1}) a ({x2},{y2})")
            
            # Obtener color para la clase
            color = self.colores_defectos.get(clase, self.colores_defectos["default"])
            
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
                (texto_x - 2, texto_y - texto_alto - 2),
                (texto_x + texto_ancho + 2, texto_y + 2),
                color, -1
            )
            
            # Dibujar texto
            cv2.putText(
                imagen_anotada, texto_etiqueta,
                (texto_x, texto_y),
                cv2.FONT_HERSHEY_SIMPLEX, self.tamano_fuente,
                (255, 255, 255), self.espesor_fuente
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
    
    def crear_metadatos_defectos(self, defectos: List[Dict], tiempos: Dict, 
                                 nombre_archivo: str, modelo: str) -> Dict:
        """
        Crea metadatos JSON para las detecciones de defectos usando estructura estándar
        
        Args:
            defectos: Lista de detecciones de defectos
            tiempos: Diccionario con tiempos
            nombre_archivo: Nombre del archivo de imagen
            modelo: Nombre del modelo usado
            
        Returns:
            Diccionario con metadatos
        """
        # Usar estructura estándar de metadatos
        metadatos = MetadataStandard.crear_metadatos_completos(
            tipo_analisis="deteccion_defectos",
            archivo_imagen=nombre_archivo,
            resultados=defectos,
            tiempos=tiempos
        )
        
        return metadatos
    
    def guardar_resultado_defectos(self, imagen: np.ndarray, defectos: List[Dict], 
                                   tiempos: Dict, directorio_salida: str, 
                                   prefijo: str = "cople_deteccion_defectos", 
                                   timestamp_captura: str = None) -> Tuple[str, str]:
        """
        Guarda la imagen anotada y los metadatos JSON
        
        Args:
            imagen: Imagen con defectos dibujados
            defectos: Lista de detecciones de defectos
            tiempos: Diccionario con tiempos
            directorio_salida: Directorio donde guardar
            prefijo: Prefijo para nombres de archivo
            timestamp_captura: Timestamp de la captura
            
        Returns:
            Tupla con (ruta_imagen, ruta_json)
        """
        try:
            # Crear nombre de archivo
            if timestamp_captura:
                nombre_base = f"{prefijo}_{timestamp_captura}"
            else:
                nombre_base = f"{prefijo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Guardar imagen
            nombre_imagen = f"{nombre_base}.jpg"
            ruta_imagen = os.path.join(directorio_salida, nombre_imagen)
            cv2.imwrite(ruta_imagen, imagen)
            
            # Crear y guardar metadatos
            metadatos = self.crear_metadatos_defectos(
                defectos, tiempos, nombre_imagen, "CopleDetDef1C2V.onnx"
            )
            
            nombre_json = f"{nombre_base}.json"
            ruta_json = os.path.join(directorio_salida, nombre_json)
            
            with open(ruta_json, 'w', encoding='utf-8') as f:
                json.dump(metadatos, f, indent=2, ensure_ascii=False)
            
            return ruta_imagen, ruta_json
            
        except Exception as e:
            print(f"❌ Error guardando resultado de defectos: {e}")
            return "", ""
    
    def procesar_deteccion_defectos(self, imagen: np.ndarray, defectos: List[Dict], 
                                    tiempos: Dict, directorio_salida: str, 
                                    timestamp_captura: str = None) -> Tuple[str, str]:
        """
        Procesa y guarda detección de defectos de coples
        
        Args:
            imagen: Imagen original
            defectos: Lista de detecciones de defectos
            tiempos: Diccionario con tiempos
            directorio_salida: Directorio de salida
            timestamp_captura: Timestamp único de la captura
            
        Returns:
            Tupla con (ruta_imagen, ruta_json)
        """
        # Dibujar defectos
        imagen_anotada = self.dibujar_defectos(imagen, defectos)
        
        # Agregar información de tiempo
        imagen_anotada = self.agregar_informacion_tiempo(imagen_anotada, tiempos)
        
        # Guardar resultado
        return self.guardar_resultado_defectos(
            imagen_anotada, defectos, tiempos, 
            directorio_salida, "cople_deteccion_defectos", timestamp_captura
        )
