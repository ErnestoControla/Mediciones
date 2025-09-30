"""
Decodificador específico para YOLOv11
Interpreta el formato de salida (1, 5, 8400) y lo convierte a coordenadas reales
"""

import numpy as np
import cv2
from typing import List, Tuple, Dict, Any

class YOLOv11Decoder:
    """
    Decodificador optimizado para modelos YOLOv11 ONNX
    Maneja el formato específico (1, 5, 8400) con sigmoid y conversión de coordenadas
    """
    
    def __init__(self, confianza_min: float = 0.55, iou_threshold: float = 0.35, max_det: int = 30, class_names: List[str] = None):
        """
        Inicializa el decodificador YOLOv11
        
        Args:
            confianza_min: Umbral mínimo de confianza (aumentado a 0.55 para mayor precisión)
            iou_threshold: Umbral de IoU para NMS (reducido a 0.35 para ser más agresivo)
            max_det: Número máximo de detecciones (reducido a 30 para mayor calidad)
            class_names: Lista de nombres de clases para usar en las detecciones
        """
        self.confianza_min = confianza_min
        self.iou_threshold = iou_threshold
        self.max_det = max_det
        self.class_names = class_names or ["Cople"]  # Por defecto usa "Cople" si no se proporcionan clases
        print(f"🎯 YOLOv11Decoder inicializado - Conf: {confianza_min}, IoU: {iou_threshold}, MaxDet: {max_det}, Clases: {self.class_names}")
    
    def decode_output(self, outputs: np.ndarray, imagen_shape: Tuple[int, int] = (640, 640)) -> List[Dict]:
        """
        Decodifica las predicciones del modelo YOLOv11 ONNX
        
        Args:
            outputs: Salida del modelo ONNX con shape (1, 5, 8400)
                    - 5 = [x, y, w, h, conf] para 1 clase
                    - 8400 = número de anchors (80×80 + 40×40 + 20×20)
            imagen_shape: Tamaño de la imagen de entrada (height, width)
            
        Returns:
            Lista de detecciones con formato estándar
        """
        try:
            print(f"🔍 YOLOv11Decoder - Input shape: {outputs.shape}")
            print(f"🔍 YOLOv11Decoder - Imagen shape: {imagen_shape}")
            
            # Verificar formato de salida
            if len(outputs.shape) != 3 or outputs.shape[1] != 5:
                raise ValueError(f"Formato inesperado. Se esperaba shape (1, 5, N), se recibió {outputs.shape}")
            
            # Transponer para facilitar procesamiento: (1, 5, 8400) -> (8400, 5)
            predictions = outputs[0].transpose()  # Shape: (8400, 5)
            print(f"🔍 YOLOv11Decoder - Predictions shape: {predictions.shape}")
            
            # Separar coordenadas y confianzas
            boxes = predictions[:, :4]  # [x_center, y_center, width, height]
            confidences = predictions[:, 4]  # Puntuaciones de confianza (logits)
            
            print(f"🔍 YOLOv11Decoder - Boxes shape: {boxes.shape}")
            print(f"🔍 YOLOv11Decoder - Confidences shape: {confidences.shape}")
            print(f"🔍 YOLOv11Decoder - Rango confidences: [{np.min(confidences):.4f}, {np.max(confidences):.4f}]")
            
            # CRÍTICO: Aplicar sigmoid a las confianzas
            confidences_sigmoid = self._sigmoid(confidences)
            print(f"🔍 YOLOv11Decoder - Rango confidences (sigmoid): [{np.min(confidences_sigmoid):.4f}, {np.max(confidences_sigmoid):.4f}]")
            
            # Filtrar por confianza mínima (más estricto)
            valid_indices = confidences_sigmoid > self.confianza_min
            valid_count = np.sum(valid_indices)
            print(f"🔍 YOLOv11Decoder - Detecciones válidas (conf > {self.confianza_min}): {valid_count}")
            
            if valid_count == 0:
                print("⚠️ YOLOv11Decoder - No se encontraron detecciones con confianza suficiente")
                return []
            
            # Filtrar predicciones válidas
            boxes_valid = boxes[valid_indices]
            confidences_valid = confidences_sigmoid[valid_indices]
            
            # Convertir de formato center_x, center_y, width, height a x1, y1, x2, y2
            boxes_xyxy = self._convert_to_xyxy(boxes_valid)
            print(f"🔍 YOLOv11Decoder - Boxes XYXY shape: {boxes_xyxy.shape}")
            
            # Aplicar Non-Maximum Suppression con parámetros más agresivos
            indices = cv2.dnn.NMSBoxes(
                boxes_xyxy.tolist(), 
                confidences_valid.tolist(), 
                self.confianza_min, 
                self.iou_threshold
            )
            
            print(f"🔍 YOLOv11Decoder - NMS aplicado, índices válidos: {len(indices) if len(indices) > 0 else 0}")
            
            detecciones = []
            
            if len(indices) > 0:
                # Limitar número máximo de detecciones
                indices = indices.flatten()[:self.max_det]
                
                for i, idx in enumerate(indices):
                    x1, y1, x2, y2 = boxes_xyxy[idx]
                    confidence = confidences_valid[idx]
                    
                    # Validar coordenadas dentro de la imagen
                    if (x1 >= 0 and y1 >= 0 and x2 <= imagen_shape[1] and y2 <= imagen_shape[0] and
                        x1 < x2 and y1 < y2):
                        
                        # Calcular centroide y área
                        centroid_x = int((x1 + x2) / 2)
                        centroid_y = int((y1 + y2) / 2)
                        area = int((x2 - x1) * (y2 - y1))
                        
                        # Validar área mínima (aumentada para evitar detecciones muy pequeñas)
                        if area >= 100:  # Aumentado de 10 a 100
                            # Usar la primera clase disponible o "Cople" por defecto
                            clase_nombre = self.class_names[0] if self.class_names else "Cople"
                            
                            detection = {
                                "clase": clase_nombre,
                                "confianza": float(confidence),
                                "bbox": {
                                    "x1": int(x1),
                                    "y1": int(y1),
                                    "x2": int(x2),
                                    "y2": int(y2)
                                },
                                "centroide": {
                                    "x": centroid_x,
                                    "y": centroid_y
                                },
                                "area": area
                            }
                            
                            detecciones.append(detection)
                            print(f"✅ YOLOv11Decoder - Detección {i+1}: {clase_nombre} - {confidence:.3f} - BBox: ({int(x1)},{int(y1)}) a ({int(x2)},{int(y2)}) - Área: {area}")
                        else:
                            print(f"⚠️ YOLOv11Decoder - Detección {i+1} descartada por área insuficiente: {area}")
                    else:
                        print(f"⚠️ YOLOv11Decoder - Detección {i+1} descartada por coordenadas inválidas: ({x1:.1f},{y1:.1f}) a ({x2:.1f},{y2:.1f})")
            
            print(f"🎯 YOLOv11Decoder - Total detecciones finales: {len(detecciones)}")
            return detecciones
            
        except Exception as e:
            print(f"❌ YOLOv11Decoder - Error en decodificación: {e}")
            return []
    
    def _sigmoid(self, x: np.ndarray) -> np.ndarray:
        """
        Aplicar función sigmoid para normalizar confianzas
        
        Args:
            x: Array de logits
            
        Returns:
            Array de confianzas normalizadas entre 0 y 1
        """
        # Clip para evitar overflow en exponencial
        x_clipped = np.clip(x, -250, 250)
        return 1 / (1 + np.exp(-x_clipped))
    
    def _convert_to_xyxy(self, boxes_cxcywh: np.ndarray) -> np.ndarray:
        """
        Convertir de formato center_x, center_y, width, height a x1, y1, x2, y2
        
        Args:
            boxes_cxcywh: Array de cajas en formato (center_x, center_y, width, height)
            
        Returns:
            Array de cajas en formato (x1, y1, x2, y2)
        """
        boxes_xyxy = np.zeros_like(boxes_cxcywh)
        
        # x1 = center_x - width/2
        boxes_xyxy[:, 0] = boxes_cxcywh[:, 0] - boxes_cxcywh[:, 2] / 2
        # y1 = center_y - height/2
        boxes_xyxy[:, 1] = boxes_cxcywh[:, 1] - boxes_cxcywh[:, 3] / 2
        # x2 = center_x + width/2
        boxes_xyxy[:, 2] = boxes_cxcywh[:, 0] + boxes_cxcywh[:, 2] / 2
        # y2 = center_y + height/2
        boxes_xyxy[:, 3] = boxes_cxcywh[:, 1] + boxes_cxcywh[:, 3] / 2
        
        return boxes_xyxy
    
    def _scale_coordinates(self, coords: Tuple[float, float, float, float], 
                          input_shape: Tuple[int, int], 
                          original_shape: Tuple[int, int]) -> Tuple[float, float, float, float]:
        """
        Escalar coordenadas del tamaño de entrada al tamaño original
        
        Args:
            coords: Coordenadas (x1, y1, x2, y2)
            input_shape: Tamaño de entrada del modelo (height, width)
            original_shape: Tamaño original de la imagen (height, width)
            
        Returns:
            Coordenadas escaladas
        """
        x1, y1, x2, y2 = coords
        input_h, input_w = input_shape
        orig_h, orig_w = original_shape
        
        # Calcular factores de escala
        scale_x = orig_w / input_w
        scale_y = orig_h / input_h
        
        # Aplicar escalado
        x1 = x1 * scale_x
        y1 = y1 * scale_y
        x2 = x2 * scale_x
        y2 = y2 * scale_y
        
        return x1, y1, x2, y2
