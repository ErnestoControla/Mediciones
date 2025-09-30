"""
Motor de Detección ONNX para Coples
Implementa detección de objetos usando modelos ONNX
"""

import numpy as np
import onnxruntime as ort
import cv2
from typing import List, Dict, Tuple, Optional
import time
import os
import sys

# Agregar path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from analisis_coples.expo_config import ModelsConfig, GlobalConfig
from .yolov11_decoder import YOLOv11Decoder


class DetectorCoplesONNX:
    """
    Motor de detección ONNX para coples
    Basado en el motor de clasificación pero adaptado para detección
    """
    
    def __init__(self, modelo_path: str, clases_path: str, confianza_min: float = 0.3):
        """
        Inicializa el detector ONNX
        
        Args:
            modelo_path: Ruta al archivo .onnx
            clases_path: Ruta al archivo de clases
            confianza_min: Umbral mínimo de confianza
        """
        self.modelo_path = modelo_path
        self.clases_path = clases_path
        self.confianza_min = confianza_min
        
        # Cargar clases
        self.clases = self._cargar_clases()
        
        # Inicializar motor ONNX
        self.session = None
        self.input_name = None
        self.output_names = []
        self.input_shape = None
        
        # Estadísticas
        self.tiempo_inferencia = 0.0
        self.frames_procesados = 0
        
        # Inicializar
        self._inicializar_modelo()
        
        # Inicializar decodificador YOLOv11
        self.decoder = YOLOv11Decoder(
            confianza_min=self.confianza_min,  # Usar el umbral configurado
            iou_threshold=0.35,  # Más agresivo para eliminar falsos positivos
            max_det=30,          # Reducido para mayor calidad
            class_names=self.clases  # Pasar las clases del detector de piezas
        )
    
    def _cargar_clases(self) -> List[str]:
        """Carga las clases desde el archivo de texto"""
        try:
            with open(self.clases_path, 'r', encoding='utf-8') as f:
                clases = [linea.strip() for linea in f.readlines() if linea.strip()]
            print(f"✅ Clases de detección cargadas: {clases}")
            return clases
        except Exception as e:
            print(f"❌ Error cargando clases: {e}")
            return ["Pieza_Cople"]  # Clase por defecto
    
    def _inicializar_modelo(self):
        """Inicializa el modelo ONNX"""
        try:
            # Verificar que el archivo existe
            if not os.path.exists(self.modelo_path):
                raise FileNotFoundError(f"Modelo no encontrado: {self.modelo_path}")
            
            # Configurar proveedores ONNX
            providers = ModelsConfig.PROVIDERS
            
            # Crear sesión ONNX
            self.session = ort.InferenceSession(
                self.modelo_path,
                providers=providers
            )
            
            # Obtener información del modelo
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [output.name for output in self.session.get_outputs()]
            
            # Obtener forma de entrada
            input_shape = self.session.get_inputs()[0].shape
            self.input_shape = (input_shape[2], input_shape[3])  # (height, width)
            
            print(f"🧠 Motor de detección ONNX inicializado:")
            print(f"   📁 Modelo: {os.path.basename(self.modelo_path)}")
            print(f"   📊 Input: {self.input_name} - Shape: {self.session.get_inputs()[0].shape}")
            print(f"   📊 Outputs: {self.output_names}")
            print(f"   🎯 Clases: {len(self.clases)}")
            print(f"   🔧 Proveedores: {providers}")
            
        except Exception as e:
            print(f"❌ Error inicializando modelo de detección: {e}")
            raise
    
    def preprocesar_imagen(self, imagen: np.ndarray) -> np.ndarray:
        """
        Preprocesa la imagen para el modelo de detección
        
        Args:
            imagen: Imagen RGB de entrada (H, W, C)
            
        Returns:
            Imagen preprocesada lista para inferencia
        """
        try:
            # Redimensionar a la entrada del modelo
            imagen_resized = cv2.resize(imagen, self.input_shape)
            
            # Convertir a float32 y normalizar [0, 1]
            imagen_float = imagen_resized.astype(np.float32) / 255.0
            
            # Transponer de HWC a CHW: (H, W, C) -> (C, H, W)
            imagen_chw = np.transpose(imagen_float, (2, 0, 1))
            
            # Agregar dimensión de batch: (C, H, W) -> (1, C, H, W)
            imagen_batch = np.expand_dims(imagen_chw, axis=0)
            
            return imagen_batch
            
        except Exception as e:
            print(f"❌ Error en preprocesamiento: {e}")
            raise
    
    def detectar_piezas(self, imagen: np.ndarray) -> List[Dict]:
        """
        Detecta piezas en la imagen
        
        Args:
            imagen: Imagen RGB de entrada (H, W, C)
            
        Returns:
            Lista de detecciones con bbox, clase y confianza
        """
        try:
            # Debug: Mostrar tamaño de imagen original
            print(f"🔍 Debug imagen - Original: {imagen.shape}")
            print(f"🔍 Debug imagen - Input shape esperado: {self.input_shape}")
            
            # Preprocesar imagen
            imagen_input = self.preprocesar_imagen(imagen)
            
            # Debug: Mostrar tamaño de imagen procesada
            print(f"🔍 Debug imagen - Procesada: {imagen_input.shape}")
            
            # Ejecutar inferencia sin timeout (tiempo no es crítico)
            tiempo_inicio = time.time()
            
            try:
                outputs = self.session.run(
                    self.output_names,
                    {self.input_name: imagen_input}
                )
                
                tiempo_inferencia = (time.time() - tiempo_inicio) * 1000  # ms
                
            except Exception as e:
                print(f"⚠️ Error en detección de piezas: {e}")
                return []
            
            # Actualizar estadísticas
            self.tiempo_inferencia = tiempo_inferencia
            self.frames_procesados += 1
            
            # Obtener dimensiones de la imagen de entrada para el decodificador
            imagen_height, imagen_width = imagen.shape[:2]
            
            # Procesar salidas usando el decodificador YOLOv11 con imagen_shape
            detecciones = self.decoder.decode_output(outputs[0], (imagen_height, imagen_width))
            
            return detecciones
            
        except Exception as e:
            print(f"❌ Error en detección: {e}")
            return []
    
    def _procesar_salidas(self, outputs: List[np.ndarray], imagen_shape: Tuple[int, int]) -> List[Dict]:
        """
        Procesa las salidas del modelo ONNX en formato YOLOv11
        
        Args:
            outputs: Lista de arrays de salida del modelo
            imagen_shape: (height, width) de la imagen original
            
        Returns:
            Lista de detecciones procesadas
        """
        detecciones = []
        
        try:
            # Debug: Mostrar información de las salidas
            print(f"🔍 Debug detección - Outputs shapes: {[out.shape for out in outputs]}")
            
            # Formato YOLOv11: [batch, 5, 8400]
            # Donde 5 = max_detections, 8400 = features por detección
            detections_array = outputs[0]
            
            if len(detections_array.shape) == 3:
                detections_array = detections_array[0]  # Remover batch dimension
            
            print(f"🔍 Debug detección - Detections array shape: {detections_array.shape}")
            
            # Para YOLOv11, cada fila (5) representa una detección
            # Los 8400 valores contienen las características de la detección
            # Necesitamos extraer coordenadas y confianza de estos valores
            
            # Debug: Analizar la estructura de los 8400 valores
            print(f"🔍 Debug YOLOv11 - Análisis de estructura:")
            print(f"   - Formato: {detections_array.shape}")
            print(f"   - Valores únicos: {len(np.unique(detections_array))}")
            print(f"   - Rango valores: [{np.min(detections_array):.4f}, {np.max(detections_array):.4f}]")
            print(f"   - Valores > 0: {np.sum(detections_array > 0)}")
            print(f"   - Valores > 1: {np.sum(detections_array > 1)}")
            print(f"   - Valores > 100: {np.sum(detections_array > 100)}")
            
            # Debug: Analizar distribución de valores
            print(f"🔍 Debug YOLOv11 - Distribución de valores:")
            print(f"   - Valores entre 0-1: {np.sum((detections_array >= 0) & (detections_array <= 1))}")
            print(f"   - Valores entre 1-100: {np.sum((detections_array > 1) & (detections_array <= 100))}")
            print(f"   - Valores entre 100-640: {np.sum((detections_array > 100) & (detections_array <= 640))}")
            print(f"   - Valores > 640: {np.sum(detections_array > 640)}")
            
            # Debug: Buscar patrones en los valores
            print(f"🔍 Debug YOLOv11 - Patrones de valores:")
            # Buscar valores que podrían ser coordenadas (múltiplos de 8, 16, 32, etc.)
            for divisor in [8, 16, 32, 64]:
                valores_divisibles = detection_row[detection_row % divisor == 0]
                if len(valores_divisibles) > 0:
                    print(f"   - Valores divisibles por {divisor}: {valores_divisibles[:5]}")
            
            for i in range(detections_array.shape[0]):
                detection_row = detections_array[i]
                
                # Buscar valores significativos (no cercanos a 0)
                valores_significativos = detection_row[detection_row > 0.1]
                
                if len(valores_significativos) > 0:
                    print(f"🔍 Fila {i} - Valores significativos: {valores_significativos[:10]}")
                    
                    # En YOLOv11, necesitamos encontrar las coordenadas y confianza
                    # Los valores más altos suelen ser confianza
                    max_valor = np.max(detection_row)
                    max_idx = np.argmax(detection_row)
                    
                    print(f"🔍 Fila {i} - Max valor: {max_valor:.2f} en índice {max_idx}")
                    
                    # Si hay valores muy altos, podría ser una detección válida
                    if max_valor > 10:  # Umbral para considerar válida
                        # Para YOLOv11, necesitamos interpretar los 8400 valores
                        # Buscar valores que podrían ser coordenadas
                        
                        # Para YOLOv11, buscar coordenadas normalizadas (0.0 a 1.0)
                        # Los valores están en el rango [0, 1] y representan posiciones relativas
                        coord_candidates_norm = detection_row[(detection_row >= 0.0) & (detection_row <= 1.0)]
                        
                        print(f"🔍 Fila {i} - Coordenadas normalizadas: {coord_candidates_norm[:8]}")
                        
                        # Si encontramos suficientes coordenadas normalizadas
                        if len(coord_candidates_norm) >= 4:
                            # Tomar las primeras 4 coordenadas como x1, y1, x2, y2
                            coords_norm = coord_candidates_norm[:4]
                            
                            # Convertir coordenadas normalizadas a píxeles
                            coords_pixels = [int(c * imagen_shape[1] if i % 2 == 0 else c * imagen_shape[0]) 
                                           for i, c in enumerate(coords_norm)]
                            
                            print(f"🔍 Fila {i} - Coordenadas en píxeles: {coords_pixels}")
                            
                            # Intentar diferentes combinaciones de coordenadas
                            # Para evitar bounding boxes inválidos
                            for j in range(0, len(coords_pixels), 2):
                                if j + 1 < len(coords_pixels):
                                    x1, y1 = coords_pixels[j], coords_pixels[j + 1]
                                    
                                    # Buscar x2, y2 en el resto de coordenadas
                                    remaining_coords = [c for k, c in enumerate(coords_pixels) if k not in [j, j + 1]]
                                    if len(remaining_coords) >= 2:
                                        x2, y2 = remaining_coords[0], remaining_coords[1]
                                        
                                        # Asegurar que x1 < x2 y y1 < y2
                                        if x1 > x2:
                                            x1, x2 = x2, x1
                                        if y1 > y2:
                                            y1, y2 = y2, y1
                                        
                                        # Normalizar confianza (dividir por 100 para valores muy altos)
                                        if max_valor > 100:
                                            conf = max_valor / 100
                                        else:
                                            conf = max_valor
                                        
                                        # Validar coordenadas
                                        if x1 < x2 and y1 < y2 and x1 >= 0 and y1 >= 0 and x2 <= imagen_shape[1] and y2 <= imagen_shape[0]:
                                            # Calcular centroide (convertir a int para OpenCV)
                                            centroide_x = int((x1 + x2) // 2)
                                            centroide_y = int((y1 + y2) // 2)
                                            
                                            # Calcular área
                                            area = (x2 - x1) * (y2 - y1)
                                            
                                            # Validar área mínima
                                            if area >= 10:
                                                # Crear detección
                                                deteccion = {
                                                    "clase": "Cople",
                                                    "confianza": float(conf),
                                                    "bbox": {
                                                        "x1": int(x1), "y1": int(y1),
                                                        "x2": int(x2), "y2": int(y2)
                                                    },
                                                    "centroide": {
                                                        "x": centroide_x,
                                                        "y": centroide_y
                                                    },
                                                    "area": area
                                                }
                                                
                                                detecciones.append(deteccion)
                                                print(f"✅ Detección {i} válida: Cople - {conf:.2%} - BBox: ({int(x1)},{int(y1)}) a ({int(x2)},{int(y2)}) - Área: {area}")
                                                break  # Encontró una combinación válida
                                        
                                        if len(detecciones) > 0 and detecciones[-1]["clase"] == "Cople":
                                            break  # Ya encontramos una detección para esta fila
                                    
                                if len(detecciones) > 0 and detecciones[-1]["clase"] == "Cople":
                                    break  # Ya encontramos una detección para esta fila
                        else:
                            print(f"⚠️ No se encontraron coordenadas normalizadas en detección {i}")
            
            # Ordenar por confianza (mayor a menor)
            detecciones.sort(key=lambda x: x["confianza"], reverse=True)
            
            print(f"🎯 Total detecciones válidas: {len(detecciones)}")
            
        except Exception as e:
            print(f"❌ Error procesando salidas del modelo: {e}")
            print(f"   Formato de salida: {[out.shape for out in outputs]}")
        
        return detecciones
    
    def actualizar_umbrales(self, confianza_min: float = None, iou_threshold: float = None):
        """
        Actualiza los umbrales del detector y del decoder
        
        Args:
            confianza_min: Nuevo umbral de confianza
            iou_threshold: Nuevo umbral de IoU
        """
        if confianza_min is not None:
            self.confianza_min = confianza_min
            self.decoder.confianza_min = confianza_min
            print(f"✅ Umbral de confianza actualizado: {confianza_min}")
        
        if iou_threshold is not None:
            self.decoder.iou_threshold = iou_threshold
            print(f"✅ Umbral de IoU actualizado: {iou_threshold}")
    
    def obtener_estadisticas(self) -> Dict:
        """Retorna estadísticas del detector"""
        return {
            "modelo": os.path.basename(self.modelo_path),
            "clases": len(self.clases),
            "frames_procesados": self.frames_procesados,
            "tiempo_inferencia_promedio_ms": self.tiempo_inferencia,
            "confianza_minima": self.confianza_min
        }
    
    def liberar(self):
        """Libera recursos del detector"""
        if self.session:
            self.session = None
        print("✅ Recursos del detector liberados")


class DetectorPiezasCoples(DetectorCoplesONNX):
    """
    Detector específico para piezas de coples
    Usa el modelo CopleDetPz1C1V.onnx
    """
    
    def __init__(self, confianza_min: float = 0.5):
        """
        Inicializa detector de piezas de coples
        
        Args:
            confianza_min: Umbral mínimo de confianza
        """
        modelo_path = os.path.join(ModelsConfig.MODELS_DIR, "CopleDetPz1C1V.onnx")
        clases_path = os.path.join(ModelsConfig.MODELS_DIR, "clases_CopleDetPz1C1V.txt")
        
        super().__init__(modelo_path, clases_path, confianza_min)
        print(f"🎯 Detector de piezas de coples inicializado")
    
    def detectar_piezas_coples(self, imagen: np.ndarray) -> List[Dict]:
        """
        Detecta piezas específicas de coples
        
        Args:
            imagen: Imagen RGB de entrada
            
        Returns:
            Lista de piezas detectadas
        """
        return self.detectar_piezas(imagen)
