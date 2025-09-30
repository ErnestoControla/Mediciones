"""
Motor de segmentación de piezas de coples usando ONNX
Basado en el modelo CopleSegPZ1C1V.onnx
"""

import cv2
import numpy as np
import time
import os
from typing import List, Dict, Tuple, Optional

# Importar configuración
from config import ModelsConfig, GlobalConfig


class SegmentadorPiezasCoples:
    """
    Motor de segmentación de piezas de coples usando ONNX.
    
    Características:
    - Carga y ejecuta modelo ONNX de segmentación de piezas
    - Preprocesamiento automático de imágenes
    - Postprocesamiento de máscaras de segmentación
    - Gestión de confianza y umbrales
    - Estadísticas de rendimiento
    """
    
    def __init__(self, model_path: Optional[str] = None, confianza_min: float = 0.55):
        """
        Inicializa el segmentador de piezas de coples.
        
        Args:
            model_path (str, optional): Ruta al modelo ONNX. Si no se proporciona, usa el por defecto.
            confianza_min (float): Umbral mínimo de confianza para segmentaciones
        """
        self.model_path = model_path or os.path.join(
            ModelsConfig.MODELS_DIR, 
            ModelsConfig.SEGMENTATION_PARTS_MODEL
        )
        self.classes_path = os.path.join(
            ModelsConfig.MODELS_DIR, 
            ModelsConfig.SEGMENTATION_PARTS_CLASSES
        )
        
        # Estado del modelo
        self.model = None
        self.session = None
        self.input_name = None
        self.output_names = None
        self.input_shape = None
        self.output_shapes = None
        self.classes = []
        
        # Parámetros de configuración
        self.confianza_min = confianza_min
        self.input_size = ModelsConfig.INPUT_SIZE
        
        # FILTROS DE CALIDAD SIMPLIFICADOS - ALINEADOS CON DEFECTOS
        self.min_area_mascara = 100         # Simplificado desde 500
        self.min_ancho_mascara = 10         # Simplificado desde 15  
        self.min_alto_mascara = 10          # Simplificado desde 15
        self.min_area_bbox = 100            # Simplificado desde 200
        self.min_cobertura_bbox = 0.1       # Simplificado desde 0.15 (10%)
        self.min_densidad_mascara = 0.03    # Simplificado desde 0.05 (3%)
        self.max_ratio_aspecto = 10.0       # Simplificado desde 15.0
        
        # Filtros básicos
        self.umbral_mascara = 0.3           # Umbral para binarizar máscaras
        self.min_pixels_contorno = 30       # Simplificado desde 50
        
        # Estadísticas
        self.stats = {
            'inicializado': False,
            'inferencias_totales': 0,
            'tiempo_total': 0.0,
            'tiempo_promedio': 0.0,
            'ultima_inferencia': 0.0
        }
        
        # Inicializar modelo
        self._inicializar_modelo()
    
    def _inicializar_modelo(self):
        """Inicializa el modelo ONNX y carga las clases."""
        try:
            # Verificar que el archivo del modelo existe
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Modelo no encontrado: {self.model_path}")
            
            # Verificar que el archivo de clases existe
            if not os.path.exists(self.classes_path):
                raise FileNotFoundError(f"Archivo de clases no encontrado: {self.classes_path}")
            
            # Cargar clases
            self._cargar_clases()
            
            # Importar ONNX Runtime
            try:
                import onnxruntime as ort
                print("✅ ONNX Runtime disponible")
            except ImportError:
                raise ImportError("ONNX Runtime no está instalado")
            
            # Configurar sesión ONNX
            providers = ModelsConfig.PROVIDERS
            session_options = ort.SessionOptions()
            session_options.intra_op_num_threads = ModelsConfig.INTRA_OP_THREADS
            session_options.inter_op_num_threads = ModelsConfig.INTER_OP_THREADS
            
            # Crear sesión
            self.session = ort.InferenceSession(
                self.model_path, 
                sess_options=session_options,
                providers=providers
            )
            
            # Obtener información de entrada y salida
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [output.name for output in self.session.get_outputs()]
            self.input_shape = self.session.get_inputs()[0].shape
            self.output_shapes = [output.shape for output in self.session.get_outputs()]
            
            print(f"🧠 Motor de segmentación de piezas ONNX inicializado:")
            print(f"   📁 Modelo: {os.path.basename(self.model_path)}")
            print(f"   📊 Input: {self.input_name} - Shape: {self.input_shape}")
            print(f"   📊 Outputs: {self.output_names}")
            print(f"   🎯 Clases: {len(self.classes)}")
            print(f"   🔧 Proveedores: {providers}")
            
            # Verificar información detallada del modelo
            print("=== INFO DEL MODELO ===")
            for input_meta in self.session.get_inputs():
                print(f"Input: {input_meta.name}, Shape: {input_meta.shape}, Type: {input_meta.type}")
                
            for output_meta in self.session.get_outputs():
                print(f"Output: {output_meta.name}, Shape: {output_meta.shape}, Type: {output_meta.type}")
            print("=== FIN INFO MODELO ===")
            
            self.stats['inicializado'] = True
            
        except Exception as e:
            print(f"❌ Error inicializando segmentador de piezas: {e}")
            self.stats['inicializado'] = False
            raise
    
    def _cargar_clases(self):
        """Carga las clases desde el archivo de texto."""
        try:
            with open(self.classes_path, 'r', encoding='utf-8') as f:
                self.classes = [line.strip() for line in f.readlines() if line.strip()]
            
            print(f"✅ Clases de segmentación de piezas cargadas: {self.classes}")
            
        except Exception as e:
            print(f"❌ Error cargando clases de segmentación de piezas: {e}")
            self.classes = []
            raise
    
    def preprocesar_imagen(self, imagen: np.ndarray) -> np.ndarray:
        """
        Preprocesa la imagen para la inferencia ONNX.
        VERSIÓN MEJORADA con validaciones adicionales.
        
        Args:
            imagen (np.ndarray): Imagen de entrada (H, W, C)
            
        Returns:
            np.ndarray: Imagen preprocesada (1, C, H, W)
        """
        try:
            # Validar entrada
            if imagen is None:
                raise ValueError("Imagen de entrada es None")
            
            if not isinstance(imagen, np.ndarray):
                raise ValueError(f"Imagen debe ser numpy array, recibido: {type(imagen)}")
            
            if len(imagen.shape) != 3:
                raise ValueError(f"Imagen debe tener 3 dimensiones (H, W, C), recibido: {imagen.shape}")
            
            h, w, c = imagen.shape
            if c != 3:
                raise ValueError(f"Imagen debe tener 3 canales, recibido: {c}")
            
            if h <= 0 or w <= 0:
                raise ValueError(f"Dimensiones de imagen inválidas: {h}x{w}")
            
            # Validar rango de valores
            if imagen.dtype != np.uint8:
                print(f"⚠️ Imagen no es uint8, tipo actual: {imagen.dtype}")
                if imagen.dtype == np.float32 or imagen.dtype == np.float64:
                    # Asumir que está en rango [0, 1] y convertir a [0, 255]
                    imagen = (imagen * 255).astype(np.uint8)
                else:
                    imagen = imagen.astype(np.uint8)
            
            # Verificar rango de valores
            min_val, max_val = np.min(imagen), np.max(imagen)
            if min_val < 0 or max_val > 255:
                print(f"⚠️ Rango de valores inesperado: [{min_val}, {max_val}], normalizando...")
                imagen = np.clip(imagen, 0, 255).astype(np.uint8)
            
            # Debug información de entrada
            print(f"🔍 Debug imagen segmentación piezas - Original: {imagen.shape}")
            print(f"🔍 Debug imagen segmentación piezas - Input shape esperado: {self.input_size}")
            print(f"🔍 Debug imagen segmentación piezas - Dtype: {imagen.dtype}, rango: [{min_val}, {max_val}]")
            
            # Redimensionar a la resolución del modelo
            imagen_resized = cv2.resize(imagen, (self.input_size, self.input_size))
            print(f"🔍 Imagen redimensionada: {imagen_resized.shape}")
            
            # Convertir de BGR a RGB
            imagen_rgb = cv2.cvtColor(imagen_resized, cv2.COLOR_BGR2RGB)
            print(f"🔍 Convertida a RGB: {imagen_rgb.shape}")
            
            # Normalizar a [0, 1]
            imagen_normalizada = imagen_rgb.astype(np.float32) / 255.0
            print(f"🔍 Normalizada: {imagen_normalizada.shape}, dtype: {imagen_normalizada.dtype}, rango: [{np.min(imagen_normalizada):.3f}, {np.max(imagen_normalizada):.3f}]")
            
            # Transponer a formato CHW (1, 3, H, W)
            imagen_chw = np.transpose(imagen_normalizada, (2, 0, 1))
            imagen_batch = np.expand_dims(imagen_chw, axis=0)
            
            print(f"✅ Preprocesamiento exitoso: {imagen_batch.shape}")
            print(f"🔍 Debug imagen segmentación piezas - Procesada: {imagen_batch.shape}")
            
            return imagen_batch
            
        except Exception as e:
            print(f"❌ Error en preprocesamiento de imagen: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def debug_modelo_salidas(self, outputs: List[np.ndarray], imagen_shape: Tuple[int, int]):
        """Debug las salidas del modelo para entender qué está pasando"""
        print("=== DEBUG MODELO ===")
        for i, output in enumerate(outputs):
            print(f"Output {i}: {output.shape}")
            print(f"  Min: {output.min():.3f}, Max: {output.max():.3f}")
            print(f"  Mean: {output.mean():.3f}, Std: {output.std():.3f}")
            
            # Guardar para inspección manual
            try:
                np.save(f"debug_output_{i}.npy", output)
                print(f"  Guardado en: debug_output_{i}.npy")
            except Exception as e:
                print(f"  Error guardando: {e}")
        
        # Verificar si las salidas tienen el formato esperado
        if len(outputs) >= 2:
            detections = outputs[0]
            if len(detections.shape) == 3:
                print(f"Detections: {detections.shape[1]} channels, {detections.shape[2]} anchors")
            
            mask_protos = outputs[1] 
            if len(mask_protos.shape) == 4:
                print(f"Mask prototypes: {mask_protos.shape[1]} prototypes, {mask_protos.shape[2]}x{mask_protos.shape[3]} resolution")
                print(f"Mask ratio esperado: {imagen_shape[0] // mask_protos.shape[2]} (debería ser 4)")
        
        print("=== FIN DEBUG MODELO ===")

    def _procesar_salidas_yolo11_seg(self, outputs: List[np.ndarray], imagen_shape: Tuple[int, int]) -> List[Dict]:
        """
        Procesa las salidas del modelo YOLO11-SEG para obtener segmentaciones.
        VERSIÓN CORREGIDA con verificación dinámica de dimensiones.
        
        Args:
            outputs (List[np.ndarray]): Salidas del modelo ONNX
            imagen_shape (Tuple[int, int]): Forma de la imagen original (H, W)
            
        Returns:
            List[Dict]: Lista de segmentaciones detectadas
        """
        try:
            print(f"🔍 Procesando salidas de segmentación de piezas...")
            print(f"   Número de outputs: {len(outputs)}")
            
            # Verificar estructura de outputs
            for i, output in enumerate(outputs):
                print(f"   Output {i} shape: {output.shape}")
            
            # YOLOv11-SEG típicamente retorna:
            # output[0]: detections (1, num_classes + 4 + mask_coeffs, anchors)
            # output[1]: mask_prototypes (1, 32, mask_h, mask_w)
            
            if len(outputs) != 2:
                raise ValueError(f"Se esperaban 2 outputs, se recibieron {len(outputs)}")
            
            detections = outputs[0]  # Shape: (1, C, A) donde C = classes + 4 + 32
            mask_protos = outputs[1]  # Shape: (1, 32, H, W)
            
            print(f"🔍 DEBUG: Detections shape: {detections.shape}")
            print(f"🔍 DEBUG: Mask protos shape: {mask_protos.shape}")
            
            # Extraer batch dimension
            detections = detections[0]  # (C, A)
            
            # Determinar número de clases dinámicamente
            total_channels = detections.shape[0]
            num_anchors = detections.shape[1]
            
            # YOLOv11-SEG: 4 (bbox) + num_classes + 32 (mask_coeffs)
            # Para 1 clase: 4 + 1 + 32 = 37 channels
            expected_mask_coeffs = 32
            num_classes = total_channels - 4 - expected_mask_coeffs
            
            print(f"🔍 DEBUG: Total channels: {total_channels}")
            print(f"🔍 DEBUG: Calculadas {num_classes} clases")
            
            if num_classes <= 0:
                raise ValueError(f"Número de clases inválido: {num_classes}")
            
            # Separar componentes
            boxes = detections[:4].T  # (A, 4) - x_center, y_center, width, height
            class_scores = detections[4:4+num_classes].T  # (A, num_classes)
            mask_coeffs = detections[4+num_classes:].T  # (A, 32)
            
            print(f"🔍 DEBUG: Boxes shape: {boxes.shape}")
            print(f"🔍 DEBUG: Class scores shape: {class_scores.shape}")
            print(f"🔍 DEBUG: Mask coeffs shape: {mask_coeffs.shape}")
            
            # Aplicar sigmoid a class scores
            class_scores = 1 / (1 + np.exp(-class_scores))
            
            # Obtener mejores scores y clases
            best_class_scores = np.max(class_scores, axis=1)
            best_classes = np.argmax(class_scores, axis=1)
            
            # Filtrar por confianza mínima
            valid_indices = best_class_scores > self.confianza_min
            
            if not np.any(valid_indices):
                print("⚠️ No hay detecciones que superen el umbral de confianza")
                return []
            
            valid_boxes = boxes[valid_indices]
            valid_scores = best_class_scores[valid_indices]
            valid_classes = best_classes[valid_indices]
            valid_mask_coeffs = mask_coeffs[valid_indices]
            
            print(f"✅ {len(valid_scores)} detecciones pasaron el filtro de confianza")
            
            # Convertir boxes de formato YOLO a XYXY
            boxes_xyxy = self._yolo_to_xyxy(valid_boxes, imagen_shape)
            
            # Verificar que tenemos boxes válidos después de la conversión
            if len(boxes_xyxy) == 0:
                print("⚠️ No hay boxes válidos después de la conversión YOLO a XYXY")
                return []
            
            # Asegurar que los arrays tengan la misma longitud
            if len(boxes_xyxy) != len(valid_scores):
                print(f"⚠️ Inconsistencia en arrays: {len(boxes_xyxy)} boxes vs {len(valid_scores)} scores")
                min_len = min(len(boxes_xyxy), len(valid_scores))
                boxes_xyxy = boxes_xyxy[:min_len]
                valid_scores = valid_scores[:min_len]
                valid_classes = valid_classes[:min_len]
                valid_mask_coeffs = valid_mask_coeffs[:min_len]
                print(f"✅ Arrays ajustados a longitud: {min_len}")
            
            # Aplicar NMS
            indices = self._aplicar_nms(boxes_xyxy, valid_scores)
            print(f"✅ {len(indices)} detecciones después de NMS")
            
            # Procesar segmentaciones
            segmentaciones = []
            mask_protos = mask_protos[0]  # (32, H, W)
            
            for i, idx in enumerate(indices):
                try:
                    confianza = float(valid_scores[idx])
                    clase_idx = valid_classes[idx]
                    bbox = boxes_xyxy[idx]
                    
                    # Verificar que el índice de clase sea válido
                    if 0 <= clase_idx < len(self.classes):
                        clase_nombre = self.classes[clase_idx]
                    else:
                        print(f"⚠️ Índice de clase inválido: {clase_idx}")
                        continue
                    
                    # Generar máscara
                    mask_coeff = valid_mask_coeffs[idx]
                    mask = self._generar_mascara_prototipos(mask_coeff, mask_protos, bbox, imagen_shape)
                    
                    if mask is not None:
                        # Calcular métricas
                        area_mascara = int(np.sum(mask > 0.5))
                        y_coords, x_coords = np.where(mask > 0.5)
                        
                        if len(x_coords) > 0:
                            centroide_x = int(np.mean(x_coords))
                            centroide_y = int(np.mean(y_coords))
                        else:
                            centroide_x = int((bbox[0] + bbox[2]) / 2)
                            centroide_y = int((bbox[1] + bbox[3]) / 2)
                        
                        area_bbox = int((bbox[2] - bbox[0]) * (bbox[3] - bbox[1]))
                        
                        segmentacion = {
                            'clase': clase_nombre,
                            'confianza': confianza,
                            'bbox': {
                                'x1': int(bbox[0]),
                                'y1': int(bbox[1]),
                                'x2': int(bbox[2]),
                                'y2': int(bbox[3])
                            },
                            'centroide': {
                                'x': centroide_x,
                                'y': centroide_y
                            },
                            'area': area_bbox,
                            'area_mascara': area_mascara,
                            'mascara': mask,
                            'alto_mascara': int(bbox[3] - bbox[1]),
                            'ancho_mascara': int(bbox[2] - bbox[0])
                        }
                        
                        # Validar calidad
                        if self._validar_calidad_mascara(segmentacion):
                            segmentaciones.append(segmentacion)
                            print(f"✅ Segmentación: {clase_nombre} - {confianza:.3f}")
                        else:
                            print(f"⚠️ Segmentación descartada por calidad: {clase_nombre}")
                            
                except Exception as e:
                    print(f"⚠️ Error procesando segmentación {i}: {e}")
                    continue
            
            print(f"🎯 Total segmentaciones encontradas: {len(segmentaciones)}")
            return segmentaciones
            
        except Exception as e:
            print(f"❌ Error procesando salidas de segmentación: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _validar_calidad_mascara(self, segmentacion: Dict) -> bool:
        """
        Validación de calidad mejorada con logging detallado.
        
        Args:
            segmentacion (Dict): Diccionario con información de la segmentación
            
        Returns:
            bool: True si la segmentación pasa todos los filtros de calidad
        """
        try:
            bbox = segmentacion['bbox']
            area_bbox = segmentacion['area']
            area_mascara = segmentacion['area_mascara']
            ancho_mascara = segmentacion['ancho_mascara']
            alto_mascara = segmentacion['alto_mascara']
            mascara = segmentacion['mascara']
            confianza = segmentacion['confianza']
            
            # Log de debugging
            print(f"   🔍 Validando máscara:")
            print(f"      Confianza: {confianza:.3f}")
            print(f"      Área bbox: {area_bbox}, Área máscara: {area_mascara}")
            print(f"      Dimensiones: {ancho_mascara}x{alto_mascara}")
            
            # 1. Validar área mínima del BBox
            if area_bbox < self.min_area_bbox:
                print(f"   ❌ BBox muy pequeño: {area_bbox} < {self.min_area_bbox}")
                return False
            
            # 2. Validar área mínima de la máscara
            if area_mascara < self.min_area_mascara:
                print(f"   ❌ Máscara muy pequeña: {area_mascara} < {self.min_area_mascara}")
                return False
            
            # 3. Validar dimensiones mínimas
            if ancho_mascara < self.min_ancho_mascara or alto_mascara < self.min_alto_mascara:
                print(f"   ❌ Dimensiones muy pequeñas: {ancho_mascara}x{alto_mascara}")
                return False
            
            # 4. Validar cobertura del BBox
            cobertura = area_mascara / area_bbox if area_bbox > 0 else 0
            if cobertura < self.min_cobertura_bbox:
                print(f"   ❌ Cobertura muy baja: {cobertura:.2%} < {self.min_cobertura_bbox:.2%}")
                return False
            
            # 5. Validar ratio de aspecto
            ratio_aspecto = max(ancho_mascara, alto_mascara) / max(1, min(ancho_mascara, alto_mascara))
            if ratio_aspecto > self.max_ratio_aspecto:
                print(f"   ❌ Ratio de aspecto muy alto: {ratio_aspecto:.1f} > {self.max_ratio_aspecto}")
                return False
            
            # 6. Validar densidad de la máscara mejorada
            if mascara is not None and isinstance(mascara, np.ndarray):
                # Aplicar umbral más bajo para detectar más detalles
                mask_thresh = (mascara > self.umbral_mascara).astype(np.uint8)
                
                # Validar contornos
                contours, _ = cv2.findContours(mask_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if len(contours) == 0:
                    print(f"   ❌ No se encontraron contornos válidos")
                    return False
                
                # Encontrar el contorno más grande
                contorno_principal = max(contours, key=cv2.contourArea)
                area_contorno = cv2.contourArea(contorno_principal)
                perimetro = cv2.arcLength(contorno_principal, True)
                
                print(f"      Contorno principal: área={area_contorno:.0f}, perímetro={perimetro:.1f}")
                
                # Validar área del contorno principal
                if area_contorno < self.min_area_mascara * 0.5:  # 50% del mínimo
                    print(f"   ❌ Contorno principal muy pequeño: {area_contorno}")
                    return False
                
                # Validar perímetro mínimo
                if perimetro < self.min_pixels_contorno:
                    print(f"   ❌ Perímetro muy pequeño: {perimetro} < {self.min_pixels_contorno}")
                    return False
                
                # Calcular compacidad (4π*área/perímetro²) - valores cerca de 1 son más circulares
                compacidad = (4 * np.pi * area_contorno) / (perimetro * perimetro) if perimetro > 0 else 0
                print(f"      Compacidad: {compacidad:.3f}")
                
                # Validar que no sea demasiado irregular (opcional)
                if compacidad < 0.01:  # Muy irregular
                    print(f"   ⚠️ Forma muy irregular (compacidad: {compacidad:.3f})")
                    # No rechazar por esto, solo advertir
            
            print(f"   ✅ Máscara válida: área={area_mascara}, cobertura={cobertura:.2%}, ratio={ratio_aspecto:.1f}")
            return True
            
        except Exception as e:
            print(f"   ❌ Error validando máscara: {e}")
            return False
    
    def _yolo_to_xyxy(self, boxes: np.ndarray, imagen_shape: Tuple[int, int]) -> np.ndarray:
        """
        Convierte boxes de formato YOLO (x_center, y_center, width, height) a formato XYXY.
        VERSIÓN MEJORADA con validación de coordenadas y manejo de casos edge.
        
        Args:
            boxes (np.ndarray): Boxes en formato YOLO (N, 4)
            imagen_shape (Tuple[int, int]): Forma de la imagen (H, W)
            
        Returns:
            np.ndarray: Boxes en formato XYXY (N, 4)
        """
        try:
            h, w = imagen_shape
            
            # Validar entrada
            if boxes.size == 0:
                return np.array([])
            
            if len(boxes.shape) != 2 or boxes.shape[1] != 4:
                raise ValueError(f"Formato de boxes inválido: {boxes.shape}")
            
            # Convertir de coordenadas normalizadas a píxeles
            x_center = boxes[:, 0] * w
            y_center = boxes[:, 1] * h
            width = boxes[:, 2] * w
            height = boxes[:, 3] * h
            
            # Validar dimensiones
            if np.any(width <= 0) or np.any(height <= 0):
                print(f"⚠️ Dimensiones inválidas detectadas: width=[{np.min(width):.1f}, {np.max(width):.1f}], height=[{np.min(height):.1f}, {np.max(height):.1f}]")
                # Filtrar boxes con dimensiones inválidas
                valid_mask = (width > 0) & (height > 0)
                if not np.any(valid_mask):
                    print("❌ No hay boxes válidos después del filtrado")
                    return np.array([])
                
                x_center = x_center[valid_mask]
                y_center = y_center[valid_mask]
                width = width[valid_mask]
                height = height[valid_mask]
            
            # Convertir a formato XYXY
            x1 = x_center - width / 2
            y1 = y_center - height / 2
            x2 = x_center + width / 2
            y2 = y_center + height / 2
            
            # Asegurar que estén dentro de los límites de la imagen
            x1 = np.clip(x1, 0, w - 1)
            y1 = np.clip(y1, 0, h - 1)
            x2 = np.clip(x2, 0, w - 1)
            y2 = np.clip(y2, 0, h - 1)
            
            # Validar que x2 > x1 y y2 > y1
            valid_boxes = (x2 > x1) & (y2 > y1)
            if not np.any(valid_boxes):
                print("❌ No hay boxes válidos después de la validación de dimensiones")
                return np.array([])
            
            # Filtrar boxes válidos
            if not np.all(valid_boxes):
                print(f"⚠️ Filtrando {np.sum(~valid_boxes)} boxes inválidos")
                x1 = x1[valid_boxes]
                y1 = y1[valid_boxes]
                x2 = x2[valid_boxes]
                y2 = y2[valid_boxes]
            
            # Validar área mínima
            areas = (x2 - x1) * (y2 - y1)
            min_area = 1  # Mínimo 1 píxel
            valid_areas = areas >= min_area
            
            if not np.any(valid_areas):
                print("❌ No hay boxes con área válida")
                return np.array([])
            
            if not np.all(valid_areas):
                print(f"⚠️ Filtrando {np.sum(~valid_areas)} boxes con área muy pequeña")
                x1 = x1[valid_areas]
                y1 = y1[valid_areas]
                x2 = x2[valid_areas]
                y2 = y2[valid_areas]
            
            result = np.column_stack([x1, y1, x2, y2])
            print(f"✅ Convertidos {len(result)} boxes de YOLO a XYXY")
            return result
            
        except Exception as e:
            print(f"❌ Error convirtiendo coordenadas YOLO a XYXY: {e}")
            import traceback
            traceback.print_exc()
            return np.array([])
    
    def _aplicar_nms(self, boxes: np.ndarray, confidences: np.ndarray, iou_threshold: float = 0.35) -> List[int]:
        """
        Aplica Non-Maximum Suppression a las detecciones.
        
        Args:
            boxes (np.ndarray): Boxes en formato XYXY (N, 4)
            confidences (np.ndarray): Confidencias (N,)
            iou_threshold (float): Umbral de IoU para NMS
            
        Returns:
            List[int]: Índices de las detecciones que pasaron NMS
        """
        try:
            # Convertir a formato OpenCV
            boxes_cv = boxes.astype(np.float32)
            confidences_cv = confidences.astype(np.float32)
            
            # Aplicar NMS
            indices = cv2.dnn.NMSBoxes(
                boxes_cv.tolist(),
                confidences_cv.tolist(),
                self.confianza_min,
                iou_threshold
            )
            
            if len(indices) > 0:
                return indices.flatten().tolist()
            else:
                return []
                
        except Exception as e:
            print(f"⚠️ Error en NMS: {e}")
            return []
    
    def _generar_mascara_prototipos(self, mask_coeff: np.ndarray, mask_protos: np.ndarray, 
                                   bbox: np.ndarray, imagen_shape: Tuple[int, int]) -> Optional[np.ndarray]:
        """
        Genera una máscara precisa usando prototipos con post-procesamiento mejorado.
        Basado en mask_ratio: 4 del entrenamiento (máscaras a 1/4 de resolución).
        
        Args:
            mask_coeff (np.ndarray): Coeficientes de la máscara (32,)
            mask_protos (np.ndarray): Prototipos de máscara (32, H, W)
            bbox (np.ndarray): Bounding box (x1, y1, x2, y2)
            imagen_shape (Tuple[int, int]): Forma de la imagen (H, W)
            
        Returns:
            Optional[np.ndarray]: Máscara generada o None si hay error
        """
        try:
            x1, y1, x2, y2 = bbox.astype(int)
            h_img, w_img = imagen_shape
            
            print(f"   🔍 Generando máscara: bbox=({x1},{y1},{x2},{y2})")
            
            # Verificar mask_ratio (debería ser 4 según args_seg_pz.yaml)
            mask_ratio = h_img // mask_protos.shape[2]
            print(f"   🔍 Mask ratio: {mask_ratio} (esperado: 4)")
            
            # Combinar prototipos usando coeficientes
            # mask_protos: (32, H, W), mask_coeff: (32,)
            mask_combined = np.zeros((mask_protos.shape[1], mask_protos.shape[2]), dtype=np.float32)
            
            for i in range(len(mask_coeff)):
                mask_combined += mask_coeff[i] * mask_protos[i]
            
            # Aplicar sigmoid para normalizar
            mask_combined = 1 / (1 + np.exp(-mask_combined))
            
            # Redimensionar la máscara al tamaño de la imagen original
            mask_resized = cv2.resize(mask_combined, (w_img, h_img), interpolation=cv2.INTER_LINEAR)
            
            # POST-PROCESAMIENTO MEJORADO
            
            # 1. Aplicar umbral adaptativo
            threshold = np.percentile(mask_resized, 85)  # 85% de los píxeles
            mask_binary = (mask_resized > threshold).astype(np.float32)
            
            # 2. Aplicar operaciones morfológicas para limpiar la máscara
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            mask_cleaned = cv2.morphologyEx(mask_binary, cv2.MORPH_OPEN, kernel, iterations=1)
            mask_cleaned = cv2.morphologyEx(mask_cleaned, cv2.MORPH_CLOSE, kernel, iterations=2)
            
            # 3. Encontrar el contorno más grande y crear máscara basada en él
            contours, _ = cv2.findContours(mask_cleaned.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if len(contours) > 0:
                # Encontrar el contorno más grande
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Crear máscara basada en el contorno más grande
                mask_final = np.zeros_like(mask_cleaned)
                cv2.fillPoly(mask_final, [largest_contour], 1.0)
                
                # 4. Aplicar suavizado para bordes más naturales
                mask_final = cv2.GaussianBlur(mask_final, (3, 3), 0)
                mask_final = (mask_final > 0.5).astype(np.float32)
                
                # 5. Verificar que la máscara esté dentro del bbox (con tolerancia)
                expansion = 0.2  # 20% de expansión
                w_bbox = x2 - x1
                h_bbox = y2 - y1
                
                x1_exp = max(0, int(x1 - w_bbox * expansion))
                y1_exp = max(0, int(y1 - h_bbox * expansion))
                x2_exp = min(w_img, int(x2 + w_bbox * expansion))
                y2_exp = min(h_img, int(y2 + h_bbox * expansion))
                
                # Aplicar filtro ROI
                roi_mask = np.zeros_like(mask_final)
                roi_mask[y1_exp:y2_exp, x1_exp:x2_exp] = 1.0
                mask_final = mask_final * roi_mask
                
                pixels_finales = np.sum(mask_final > 0.5)
                
                if pixels_finales > 100:  # Umbral mínimo de píxeles
                    print(f"   ✅ Máscara mejorada generada: área={pixels_finales}")
                    return mask_final
                else:
                    print(f"   ⚠️ Máscara con muy pocos píxeles")
                    return None
            else:
                print(f"   ⚠️ No se encontraron contornos válidos")
                return None
                
        except Exception as e:
            print(f"❌ Error generando máscara con prototipos: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def segmentar(self, imagen: np.ndarray) -> List[Dict]:
        """
        Realiza segmentación de piezas en la imagen.
        
        Args:
            imagen (np.ndarray): Imagen de entrada (H, W, C)
            
        Returns:
            List[Dict]: Lista de segmentaciones detectadas
        """
        if not self.stats['inicializado']:
            raise RuntimeError("El segmentador no está inicializado")
        
        inicio = time.time()
        
        try:
            # Preprocesar imagen
            imagen_procesada = self.preprocesar_imagen(imagen)
            
            # Realizar inferencia
            outputs = self.session.run(self.output_names, {self.input_name: imagen_procesada})
            print("✅ Inferencia ONNX exitosa")
            
            # Debug de salidas del modelo (simplificado)
            print("=== DEBUG MODELO SIMPLIFICADO ===")
            for i, output in enumerate(outputs):
                print(f"Output {i}: {output.shape}, rango: [{output.min():.3f}, {output.max():.3f}]")
            print("=== FIN DEBUG MODELO ===")
            
            # Procesar salidas
            segmentaciones = self._procesar_salidas_yolo11_seg(outputs, imagen.shape[:2])
            
            # Actualizar estadísticas
            tiempo_inferencia = time.time() - inicio
            self.stats['inferencias_totales'] += 1
            self.stats['tiempo_total'] += tiempo_inferencia
            self.stats['tiempo_promedio'] = self.stats['tiempo_total'] / self.stats['inferencias_totales']
            self.stats['ultima_inferencia'] = tiempo_inferencia
            
            return segmentaciones
            
        except Exception as e:
            print(f"❌ Error en segmentación de piezas: {e}")
            return []
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene las estadísticas del segmentador.
        
        Returns:
            Dict: Estadísticas del segmentador
        """
        return self.stats.copy()
    
    def configurar_filtros(self, **kwargs):
        """
        Configura los filtros de calidad de máscaras dinámicamente.
        
        Args:
            **kwargs: Parámetros de filtrado a configurar
                - min_area_mascara: Área mínima de máscara
                - min_ancho_mascara: Ancho mínimo de máscara
                - min_alto_mascara: Alto mínimo de máscara
                - min_area_bbox: Área mínima de BBox
                - min_cobertura_bbox: Cobertura mínima del BBox
                - min_densidad_mascara: Densidad mínima de máscara
                - max_ratio_aspecto: Ratio máximo de aspecto
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                    print(f"✅ Filtro {key} configurado: {value}")
                else:
                    print(f"⚠️ Filtro {key} no existe")
        except Exception as e:
            print(f"❌ Error configurando filtros: {e}")
    
    def obtener_filtros_actuales(self) -> Dict:
        """
        Obtiene la configuración actual de todos los filtros.
        
        Returns:
            Dict: Configuración actual de filtros
        """
        return {
            'confianza_min': self.confianza_min,
            'min_area_mascara': self.min_area_mascara,
            'min_ancho_mascara': self.min_ancho_mascara,
            'min_alto_mascara': self.min_alto_mascara,
            'min_area_bbox': self.min_area_bbox,
            'min_cobertura_bbox': self.min_cobertura_bbox,
            'min_densidad_mascara': self.min_densidad_mascara,
            'max_ratio_aspecto': self.max_ratio_aspecto,
            'umbral_mascara': self.umbral_mascara,
            'min_pixels_contorno': self.min_pixels_contorno
        }
    
    def configurar_filtros_permisivos(self):
        """
        Configura filtros muy permisivos para debugging.
        """
        self.min_area_mascara = 100
        self.min_ancho_mascara = 10
        self.min_alto_mascara = 10
        self.min_area_bbox = 100
        self.min_cobertura_bbox = 0.05  # 5%
        self.min_densidad_mascara = 0.01  # 1%
        self.max_ratio_aspecto = 20.0
        self.umbral_mascara = 0.2
        self.min_pixels_contorno = 20
        
        print("🔧 Filtros configurados en modo PERMISIVO para debugging")

    def configurar_filtros_estrictos(self):
        """
        Configura filtros estrictos para producción.
        """
        self.min_area_mascara = 2000
        self.min_ancho_mascara = 40
        self.min_alto_mascara = 40
        self.min_area_bbox = 800
        self.min_cobertura_bbox = 0.4  # 40%
        self.min_densidad_mascara = 0.12  # 12%
        self.max_ratio_aspecto = 8.0
        self.umbral_mascara = 0.5
        self.min_pixels_contorno = 100
        
        print("🔧 Filtros configurados en modo ESTRICTO para producción")
    
    def modo_debug_extremo(self):
        """
        Configura filtros extremadamente permisivos para debugging.
        """
        self.confianza_min = 0.1
        self.min_area_mascara = 50
        self.min_ancho_mascara = 5
        self.min_alto_mascara = 5
        self.min_area_bbox = 50
        self.min_cobertura_bbox = 0.01  # 1%
        self.min_densidad_mascara = 0.001  # 0.1%
        self.max_ratio_aspecto = 50.0
        self.umbral_mascara = 0.1
        self.min_pixels_contorno = 10
        
        print("🔧 Filtros configurados en modo DEBUG EXTREMO")
    
    def liberar(self):
        """Libera los recursos del segmentador."""
        try:
            if self.session is not None:
                del self.session
                self.session = None
            
            self.stats['inicializado'] = False
            print("✅ Recursos del segmentador de piezas liberados")
            
        except Exception as e:
            print(f"⚠️ Error liberando recursos del segmentador de piezas: {e}")
    
    def liberar_recursos(self):
        """Libera los recursos del segmentador (alias para compatibilidad)."""
        self.liberar()
