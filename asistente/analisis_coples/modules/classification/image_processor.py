"""
Procesador de imágenes para clasificación de coples
"""

import cv2
import numpy as np
import time
from typing import Tuple, Optional

# Importar configuración
from analisis_coples.expo_config import VisualizationConfig, FileConfig


class ProcesadorImagenClasificacion:
    """
    Procesador de imágenes para agregar anotaciones de clasificación.
    
    Características:
    - Agrega etiquetas de clase con colores apropiados
    - Muestra información de confianza y tiempo
    - Genera imágenes de salida anotadas
    - Mantiene calidad de imagen original
    """
    
    def __init__(self):
        """Inicializa el procesador de imágenes."""
        self.font = VisualizationConfig.FONT
        self.font_scale = VisualizationConfig.FONT_SCALE
        self.font_thickness = VisualizationConfig.FONT_THICKNESS
        self.text_padding = VisualizationConfig.TEXT_PADDING
        self.text_position = VisualizationConfig.TEXT_POSITION
        
        # Colores
        self.accepted_color = VisualizationConfig.ACCEPTED_COLOR
        self.rejected_color = VisualizationConfig.REJECTED_COLOR
        self.text_color = VisualizationConfig.TEXT_COLOR
        self.background_color = VisualizationConfig.BACKGROUND_COLOR
    
    def agregar_anotaciones_clasificacion(
        self, 
        imagen: np.ndarray, 
        clase_predicha: str, 
        confianza: float,
        tiempo_captura: float = 0,
        tiempo_inferencia: float = 0
    ) -> np.ndarray:
        """
        Agrega anotaciones de clasificación a la imagen.
        
        Args:
            imagen (np.ndarray): Imagen original (BGR)
            clase_predicha (str): Clase predicha por el modelo
            confianza (float): Nivel de confianza (0.0 - 1.0)
            tiempo_captura (float): Tiempo de captura en ms
            tiempo_inferencia (float): Tiempo de inferencia en ms
            
        Returns:
            np.ndarray: Imagen con anotaciones
        """
        try:
            # Crear copia de la imagen
            imagen_anotada = imagen.copy()
            
            # Determinar color según la clase
            color_clase = self._obtener_color_clase(clase_predicha)
            
            # Agregar etiqueta principal de clase
            imagen_anotada = self._agregar_etiqueta_clase(
                imagen_anotada, clase_predicha, confianza, color_clase
            )
            
            # Agregar información de tiempo si se proporciona
            if tiempo_captura > 0 or tiempo_inferencia > 0:
                imagen_anotada = self._agregar_info_tiempo(
                    imagen_anotada, tiempo_captura, tiempo_inferencia
                )
            
            return imagen_anotada
            
        except Exception as e:
            print(f"❌ Error agregando anotaciones: {e}")
            return imagen
    
    def _obtener_color_clase(self, clase_predicha: str) -> Tuple[int, int, int]:
        """
        Obtiene el color apropiado para la clase.
        
        Args:
            clase_predicha (str): Nombre de la clase
            
        Returns:
            tuple: Color en formato BGR
        """
        clase_lower = clase_predicha.lower()
        
        if "aceptado" in clase_lower or "acept" in clase_lower:
            return self.accepted_color
        elif "rechazado" in clase_lower or "rechaz" in clase_lower:
            return self.rejected_color
        else:
            # Color neutral para clases desconocidas
            return (128, 128, 128)  # Gris
    
    def _agregar_etiqueta_clase(
        self, 
        imagen: np.ndarray, 
        clase_predicha: str, 
        confianza: float, 
        color_clase: Tuple[int, int, int]
    ) -> np.ndarray:
        """
        Agrega la etiqueta principal de clase a la imagen.
        
        Args:
            imagen (np.ndarray): Imagen a anotar
            clase_predicha (str): Nombre de la clase
            confianza (float): Nivel de confianza
            color_clase (tuple): Color de la clase
            
        Returns:
            np.ndarray: Imagen con etiqueta agregada
        """
        try:
            # Preparar texto
            texto_clase = f"{clase_predicha}"
            texto_confianza = f"Conf: {confianza:.2%}"
            
            # Calcular posiciones
            x, y = self.text_position
            y_confianza = y + 30
            
            # Obtener dimensiones del texto
            (text_width_clase, text_height_clase), baseline_clase = cv2.getTextSize(
                texto_clase, self.font, self.font_scale, self.font_thickness
            )
            
            (text_width_conf, text_height_conf), baseline_conf = cv2.getTextSize(
                texto_confianza, self.font, self.font_scale * 0.7, self.font_thickness
            )
            
            # Calcular dimensiones del rectángulo de fondo
            rect_width = max(text_width_clase, text_width_conf) + 2 * self.text_padding
            rect_height = text_height_clase + text_height_conf + 3 * self.text_padding
            
            # Dibujar rectángulo de fondo
            cv2.rectangle(
                imagen,
                (x, y - text_height_clase - self.text_padding),
                (x + rect_width, y + rect_height),
                self.background_color,
                -1  # Relleno sólido
            )
            
            # Dibujar borde del rectángulo
            cv2.rectangle(
                imagen,
                (x, y - text_height_clase - self.text_padding),
                (x + rect_width, y + rect_height),
                color_clase,
                2  # Grosor del borde
            )
            
            # Agregar texto de clase
            cv2.putText(
                imagen,
                texto_clase,
                (x + self.text_padding, y),
                self.font,
                self.font_scale,
                color_clase,
                self.font_thickness,
                cv2.LINE_AA
            )
            
            # Agregar texto de confianza
            cv2.putText(
                imagen,
                texto_confianza,
                (x + self.text_padding, y_confianza),
                self.font,
                self.font_scale * 0.7,
                self.text_color,
                self.font_thickness,
                cv2.LINE_AA
            )
            
            return imagen
            
        except Exception as e:
            print(f"❌ Error agregando etiqueta de clase: {e}")
            return imagen
    
    def _agregar_info_tiempo(
        self, 
        imagen: np.ndarray, 
        tiempo_captura: float, 
        tiempo_inferencia: float
    ) -> np.ndarray:
        """
        Agrega información de tiempo a la imagen.
        
        Args:
            imagen (np.ndarray): Imagen a anotar
            tiempo_captura (float): Tiempo de captura en ms
            tiempo_inferencia (float): Tiempo de inferencia en ms
            
        Returns:
            np.ndarray: Imagen con información de tiempo
        """
        try:
            # Calcular posición (esquina inferior derecha)
            height, width = imagen.shape[:2]
            x = width - 200
            y = height - 20
            
            # Preparar texto
            texto_captura = f"Capt: {tiempo_captura:.1f}ms"
            texto_inferencia = f"Inf: {tiempo_inferencia:.1f}ms"
            tiempo_total = tiempo_captura + tiempo_inferencia
            texto_total = f"Total: {tiempo_total:.1f}ms"
            
            # Agregar texto de tiempo
            cv2.putText(
                imagen,
                texto_captura,
                (x, y - 40),
                self.font,
                self.font_scale * 0.6,
                self.text_color,
                self.font_thickness,
                cv2.LINE_AA
            )
            
            cv2.putText(
                imagen,
                texto_inferencia,
                (x, y - 20),
                self.font,
                self.font_scale * 0.6,
                self.text_color,
                self.font_thickness,
                cv2.LINE_AA
            )
            
            cv2.putText(
                imagen,
                texto_total,
                (x, y),
                self.font,
                self.font_scale * 0.6,
                self.text_color,
                self.font_thickness,
                cv2.LINE_AA
            )
            
            return imagen
            
        except Exception as e:
            print(f"❌ Error agregando información de tiempo: {e}")
            return imagen
    
    def crear_imagen_resumen(
        self, 
        imagen_original: np.ndarray, 
        clase_predicha: str, 
        confianza: float,
        tiempo_captura: float = 0,
        tiempo_inferencia: float = 0
    ) -> np.ndarray:
        """
        Crea una imagen de resumen con toda la información.
        
        Args:
            imagen_original (np.ndarray): Imagen original
            clase_predicha (str): Clase predicha
            confianza (float): Nivel de confianza
            tiempo_captura (float): Tiempo de captura
            tiempo_inferencia (float): Tiempo de inferencia
            
        Returns:
            np.ndarray: Imagen de resumen
        """
        try:
            # Agregar anotaciones básicas
            imagen_resumen = self.agregar_anotaciones_clasificacion(
                imagen_original, clase_predicha, confianza, tiempo_captura, tiempo_inferencia
            )
            
            # Agregar información adicional si es necesario
            if GlobalConfig.DEBUG_MODE:
                imagen_resumen = self._agregar_info_debug(imagen_resumen)
            
            return imagen_resumen
            
        except Exception as e:
            print(f"❌ Error creando imagen de resumen: {e}")
            return imagen_original
    
    def _agregar_info_debug(self, imagen: np.ndarray) -> np.ndarray:
        """
        Agrega información de debug a la imagen.
        
        Args:
            imagen (np.ndarray): Imagen a anotar
            
        Returns:
            np.ndarray: Imagen con información de debug
        """
        try:
            # Agregar timestamp
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Posición en esquina superior derecha
            height, width = imagen.shape[:2]
            x = width - 250
            y = 20
            
            # Agregar texto de debug
            cv2.putText(
                imagen,
                f"Debug: {timestamp}",
                (x, y),
                self.font,
                self.font_scale * 0.5,
                (128, 128, 128),  # Gris
                self.font_thickness,
                cv2.LINE_AA
            )
            
            return imagen
            
        except Exception as e:
            print(f"⚠️ Error agregando info de debug: {e}")
            return imagen
    
    def redimensionar_imagen(
        self, 
        imagen: np.ndarray, 
        nuevo_ancho: int, 
        nuevo_alto: int,
        mantener_aspecto: bool = True
    ) -> np.ndarray:
        """
        Redimensiona la imagen manteniendo la calidad.
        
        Args:
            imagen (np.ndarray): Imagen a redimensionar
            nuevo_ancho (int): Nuevo ancho
            nuevo_alto (int): Nuevo alto
            mantener_aspecto (bool): Si mantener la relación de aspecto
            
        Returns:
            np.ndarray: Imagen redimensionada
        """
        try:
            if mantener_aspecto:
                # Calcular relación de aspecto
                h, w = imagen.shape[:2]
                aspect_ratio = w / h
                
                if nuevo_ancho / nuevo_alto > aspect_ratio:
                    # El nuevo ancho es muy ancho
                    nuevo_ancho = int(nuevo_alto * aspect_ratio)
                else:
                    # El nuevo alto es muy alto
                    nuevo_alto = int(nuevo_ancho / aspect_ratio)
            
            # Redimensionar usando INTER_LANCZOS4 para mejor calidad
            imagen_redimensionada = cv2.resize(
                imagen, 
                (nuevo_ancho, nuevo_alto), 
                interpolation=cv2.INTER_LANCZOS4
            )
            
            return imagen_redimensionada
            
        except Exception as e:
            print(f"❌ Error redimensionando imagen: {e}")
            return imagen
