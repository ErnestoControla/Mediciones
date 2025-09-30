"""
Motor de segmentación de defectos de coples usando ONNX
Basado en el modelo CopleSegDef1C8V.onnx
"""

import cv2
import numpy as np
import time
import os
from typing import List, Dict, Tuple, Optional

# Importar configuración
from analisis_coples.expo_config import ModelsConfig, GlobalConfig


class SegmentadorDefectosCoples:
    """
    Motor de segmentación de defectos de coples usando ONNX.
    
    Características:
    - Carga y ejecuta modelo ONNX de segmentación de defectos
    - Preprocesamiento automático de imágenes
    - Postprocesamiento de máscaras de segmentación
    - Gestión de confianza y umbrales
    - Estadísticas de rendimiento
    """
    
    def __init__(self, model_path: Optional[str] = None, confianza_min: float = 0.55):
        """
        Inicializa el segmentador de defectos de coples.
        
        Args:
            model_path (str, optional): Ruta al modelo ONNX. Si no se proporciona, usa el por defecto.
            confianza_min (float): Umbral mínimo de confianza para segmentaciones
        """
        self.model_path = model_path or os.path.join(
            ModelsConfig.MODELS_DIR, 
            ModelsConfig.SEGMENTATION_DEFECTOS_MODEL
        )
        self.classes_path = os.path.join(
            ModelsConfig.MODELS_DIR, 
            ModelsConfig.SEGMENTATION_DEFECTOS_CLASSES
        )
        
        # Estado del modelo
        self.model = None
        self.session = None
        self.input_name = None
        self.output_names = None
        self.input_shape = None
        self.output_shapes = None
        
        # Clases del modelo
        self.class_names = []
        self.num_classes = 0
        
        # Estadísticas de inferencia
        self.tiempo_inferencia = 0.0
        self.frames_procesados = 0
        
        # Configuración
        self.confianza_min = confianza_min
        self.input_size = ModelsConfig.INPUT_SIZE  # 640x640
        
        # Cargar clases PRIMERO
        self._cargar_clases()
        
        # Inicializar motor ONNX
        self._inicializar_modelo()
    
    def _cargar_clases(self):
        """Carga las clases desde el archivo de texto."""
        try:
            if os.path.exists(self.classes_path):
                with open(self.classes_path, 'r', encoding='utf-8') as f:
                    self.class_names = [line.strip() for line in f.readlines() if line.strip()]
                self.num_classes = len(self.class_names)
                print(f"✅ Clases de segmentación de defectos cargadas: {self.class_names}")
            else:
                print(f"⚠️ Archivo de clases de segmentación de defectos no encontrado: {self.classes_path}")
                # Clases por defecto para segmentación de defectos
                self.class_names = ["Defecto_Seg_1", "Defecto_Seg_2"]
                self.num_classes = 2
        except Exception as e:
            print(f"❌ Error cargando clases de segmentación de defectos: {e}")
            # Clases por defecto
            self.class_names = ["Defecto_Seg_1", "Defecto_Seg_2"]
            self.num_classes = 2
    
    def _inicializar_modelo(self):
        """Inicializa el motor de segmentación ONNX."""
        try:
            print(f"🎯 Inicializando segmentador de defectos...")
            
            if not os.path.exists(self.model_path):
                print(f"❌ Modelo de segmentación de defectos no encontrado: {self.model_path}")
                return False
            
            import onnxruntime as ort
            
            # Configurar proveedores
            providers = ['CPUExecutionProvider']
            if ort.get_device() == 'GPU':
                providers = ['CUDAExecutionProvider'] + providers
            
            # Crear sesión ONNX
            self.session = ort.InferenceSession(self.model_path, providers=providers)
            
            # Obtener información del modelo
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [output.name for output in self.session.get_outputs()]
            self.input_shape = self.session.get_inputs()[0].shape
            self.output_shapes = [output.shape for output in self.session.get_outputs()]
            
            print(f"🧠 Motor de segmentación de defectos ONNX inicializado:")
            print(f"   📁 Modelo: {os.path.basename(self.model_path)}")
            print(f"   📊 Input: {self.input_name} - Shape: {self.input_shape}")
            print(f"   📊 Outputs: {self.output_names}")
            print(f"   🎯 Clases: {self.num_classes}")
            print(f"   🔧 Proveedores: {providers}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando segmentador de defectos: {e}")
            return False
    
    def preprocesar_imagen(self, imagen: np.ndarray) -> np.ndarray:
        """
        Preprocesa la imagen para el modelo de segmentación (ULTRA-SIMPLIFICADO)
        
        Args:
            imagen: Imagen RGB de entrada (H, W, C)
            
        Returns:
            Imagen preprocesada lista para inferencia
        """
        try:
            # Validar entrada básica
            if imagen is None or imagen.size == 0:
                print("⚠️ Imagen inválida, usando fallback")
                return np.zeros((1, 3, self.input_size, self.input_size), dtype=np.float32)
            
            # Verificar dimensiones
            if len(imagen.shape) != 3 or imagen.shape[2] != 3:
                print("⚠️ Formato de imagen incorrecto, usando fallback")
                return np.zeros((1, 3, self.input_size, self.input_size), dtype=np.float32)
            
            # Crear imagen de fallback directamente (evitar operaciones complejas)
            imagen_fallback = np.zeros((1, 3, self.input_size, self.input_size), dtype=np.float32)
            
            # Solo procesar si la imagen es del tamaño correcto
            if imagen.shape[:2] == (self.input_size, self.input_size):
                try:
                    # Conversión mínima: solo normalización
                    imagen_norm = imagen.astype(np.float32) / 255.0
                    # Transposición simple
                    imagen_chw = np.transpose(imagen_norm, (2, 0, 1))
                    # Batch dimension
                    imagen_fallback[0] = imagen_chw
                    print(f"✅ Preprocesamiento exitoso: {imagen_fallback.shape}")
                except Exception as e:
                    print(f"⚠️ Error en preprocesamiento: {e}, usando fallback")
            else:
                print(f"⚠️ Tamaño incorrecto: {imagen.shape}, usando fallback")
            
            return imagen_fallback
            
        except Exception as e:
            print(f"❌ Error crítico en preprocesamiento: {e}")
            # Retornar imagen de fallback
            fallback = np.zeros((1, 3, self.input_size, self.input_size), dtype=np.float32)
            print(f"⚠️ Usando imagen de fallback: {fallback.shape}")
            return fallback
    
    def segmentar_defectos(self, imagen: np.ndarray) -> List[Dict]:
        """
        Segmenta defectos en la imagen
        
        Args:
            imagen: Imagen RGB de entrada (H, W, C)
            
        Returns:
            Lista de segmentaciones con máscaras, clase y confianza
        """
        try:
            # Debug: Mostrar tamaño de imagen original
            print(f"🔍 Debug imagen segmentación - Original: {imagen.shape}")
            print(f"🔍 Debug imagen segmentación - Input shape esperado: {self.input_size}")
            
            # Preprocesar imagen
            imagen_input = self.preprocesar_imagen(imagen)
            
            # Debug: Mostrar tamaño de imagen procesada
            print(f"🔍 Debug imagen segmentación - Procesada: {imagen_input.shape}")
            
            # Ejecutar inferencia sin timeout (tiempo no es crítico)
            tiempo_inicio = time.time()
            
            try:
                outputs = self.session.run(
                    self.output_names,
                    {self.input_name: imagen_input}
                )
                print("✅ Inferencia ONNX exitosa")
            except Exception as e:
                print(f"⚠️ Error en inferencia ONNX: {e}, usando fallback")
                # Crear outputs de fallback
                outputs = [
                    np.zeros((1, 37, 8400), dtype=np.float32),  # Detections
                    np.zeros((1, 32, 160, 160), dtype=np.float32)  # Mask protos
                ]
            
            tiempo_inferencia = (time.time() - tiempo_inicio) * 1000  # ms
            
            # Actualizar estadísticas
            self.tiempo_inferencia = tiempo_inferencia
            self.frames_procesados += 1
            
            # Obtener dimensiones de la imagen de entrada para el postprocesamiento
            imagen_height, imagen_width = imagen.shape[:2]
            
            # Procesar salidas de segmentación
            segmentaciones = self._procesar_salidas_segmentacion(outputs)
            
            return segmentaciones
            
        except Exception as e:
            print(f"❌ Error en segmentación de defectos: {e}")
            return []
    
    def _procesar_salidas_segmentacion(self, outputs):
        """
        Procesa las salidas del modelo YOLO11-SEG para extraer segmentaciones
        """
        print(f"🔍 Procesando salidas de segmentación...")
        print(f"   Número de outputs: {len(outputs)}")
        
        if len(outputs) > 0:
            print(f"   Shape del primer output: {outputs[0].shape}")
        
        segmentaciones = []
        
        # Procesar outputs de YOLO11-SEG
        print(f"   🔍 DEBUG: Verificando outputs de YOLO11-SEG...")
        print(f"   🔍 DEBUG: Hay {len(outputs)} outputs")
        
        if len(outputs) >= 2:
            # YOLO11-SEG tiene 2 outputs: bboxes + prototipos de máscaras
            detections = outputs[0]  # (1, 37, 8400) - Bboxes + confianza + coeficientes
            mask_protos = outputs[1]  # (1, 32, 160, 160) - Prototipos de máscaras
            
            print(f"   ✅ DEBUG: Output 0 (detections): {detections.shape}")
            print(f"   ✅ DEBUG: Output 1 (mask_protos): {mask_protos.shape}")
            
            # Verificar formato de salida
            if detections.shape[1] != 37:
                print(f"   ⚠️ DEBUG: Formato inesperado. Se esperaba (1, 37, N), se recibió {detections.shape}")
                return segmentaciones
            
            # Transponer para facilitar procesamiento: (1, 37, 8400) -> (8400, 37)
            predictions = detections[0].transpose()  # Shape: (8400, 37)
            
            # Separar componentes
            boxes = predictions[:, :4]  # [x_center, y_center, width, height]
            confidences = predictions[:, 4]  # Puntuaciones de confianza
            mask_coeffs = predictions[:, 5:37]  # 32 coeficientes de máscara
            
            print(f"   🔍 DEBUG: Boxes shape: {boxes.shape}")
            print(f"   🔍 DEBUG: Confidences shape: {confidences.shape}")
            print(f"   🔍 DEBUG: Mask coefficients shape: {mask_coeffs.shape}")
            
            # Aplicar sigmoid a las confianzas
            confidences = self._sigmoid(confidences)
            
            # Filtrar por confianza mínima
            valid_indices = confidences > self.confianza_min
            
            if not np.any(valid_indices):
                print(f"   ❌ No se encontraron detecciones con confianza > {self.confianza_min}")
                return segmentaciones
            
            boxes = boxes[valid_indices]
            confidences = confidences[valid_indices]
            mask_coeffs = mask_coeffs[valid_indices]
            
            print(f"   ✅ {len(boxes)} detecciones pasaron el filtro de confianza")
            
            # Convertir formato de cajas de center_x, center_y, width, height a x1, y1, x2, y2
            boxes_xyxy = self._convert_to_xyxy(boxes)
            
            # Aplicar Non-Maximum Suppression
            indices = cv2.dnn.NMSBoxes(
                boxes_xyxy.tolist(), 
                confidences.tolist(), 
                self.confianza_min, 
                0.35  # IoU threshold
            )
            
            if len(indices) > 0:
                indices = indices.flatten()[:30]  # max_det
                print(f"   ✅ {len(indices)} detecciones después de NMS")
                
                for i in indices:
                    x1, y1, x2, y2 = boxes_xyxy[i]
                    confidence = confidences[i]
                    mask_coeff = mask_coeffs[i]
                    
                    # Calcular centroide
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    
                    # Generar máscara combinando coeficientes con prototipos
                    try:
                        mask = self._generate_mask(mask_coeff, mask_protos, (x1, y1, x2, y2), (640, 640))
                        mask_area = int(np.sum(mask > 0.5)) if mask is not None else 0
                    except Exception as e:
                        print(f"   ⚠️  Error generando máscara: {e}")
                        mask = None
                        mask_area = 0
                    
                    # Crear segmentación con máscaras reales (SIN CONVERSIÓN A LISTA)
                    segmentacion = {
                        "clase": "Defecto",
                        "confianza": float(confidence),
                        "bbox": {
                            "x1": int(x1),
                            "y1": int(y1),
                            "x2": int(x2),
                            "y2": int(y2)
                        },
                        "centroide": {
                            "x": cx,
                            "y": cy
                        },
                        "area": int((x2 - x1) * (y2 - y1)),
                        "area_mascara": mask_area,
                        "mascara": mask,  # Mantener como numpy array (SIN .tolist())
                        "coeficientes_mascara": mask_coeff.tolist()[:5],  # Solo primeros 5 coeficientes
                        "contorno": self._bbox_to_contour(x1, y1, x2, y2)
                    }
                    
                    # Debug de máscara
                    if mask is not None:
                        print(f"   ✅ Máscara creada: {mask.shape}, área: {mask_area}")
                    else:
                        print(f"   ⚠️  Máscara fallback creada: área: {mask_area}")
                    
                    segmentaciones.append(segmentacion)
                    print(f"✅ Segmentación: Defecto - {confidence:.3f} - BBox: ({int(x1)},{int(y1)}) a ({int(x2)},{int(y2)}) - Área: {int((x2 - x1) * (y2 - y1))}")
            else:
                print(f"   ❌ No se encontraron detecciones después de NMS")
        else:
            print(f"   ⚠️ DEBUG: Se esperaban al menos 2 outputs, se recibieron {len(outputs)}")
        
        print(f"🎯 Total segmentaciones encontradas: {len(segmentaciones)}")
        
        # Debug final: verificar que las máscaras estén presentes
        for i, seg in enumerate(segmentaciones):
            if 'mascara' in seg and seg['mascara'] is not None:
                print(f"   ✅ Segmentación {i}: Máscara presente, shape: {len(seg['mascara'])} elementos")
            else:
                print(f"   ❌ Segmentación {i}: Máscara ausente o None")
        
        return segmentaciones
    
    def _sigmoid(self, x):
        """Aplicar función sigmoid para normalizar confianzas"""
        return 1 / (1 + np.exp(-np.clip(x, -250, 250)))
    
    def _convert_to_xyxy(self, boxes_cxcywh):
        """Convertir de formato center_x, center_y, width, height a x1, y1, x2, y2"""
        boxes_xyxy = np.zeros_like(boxes_cxcywh)
        boxes_xyxy[:, 0] = boxes_cxcywh[:, 0] - boxes_cxcywh[:, 2] / 2  # x1
        boxes_xyxy[:, 1] = boxes_cxcywh[:, 1] - boxes_cxcywh[:, 3] / 2  # y1
        boxes_xyxy[:, 2] = boxes_cxcywh[:, 0] + boxes_cxcywh[:, 2] / 2  # x2
        boxes_xyxy[:, 3] = boxes_cxcywh[:, 1] + boxes_cxcywh[:, 3] / 2  # y2
        return boxes_xyxy
    
    def _generate_mask(self, mask_coeffs, mask_protos, bbox, input_shape):
        """
        Genera máscara a partir de coeficientes y prototipos de YOLO11
        """
        try:
            # Extraer prototipos (shape: [1, 32, 160, 160])
            protos = mask_protos[0]  # Shape: [32, 160, 160]
            
            # Aplicar coeficientes a prototipos
            # mask_coeffs shape: [32], protos shape: [32, 160, 160]
            mask = np.tensordot(mask_coeffs, protos, axes=([0], [0]))  # Shape: [160, 160]
            
            # Aplicar sigmoid para normalizar
            mask = self._sigmoid(mask)
            
            # Redimensionar a input_shape
            H, W = input_shape
            if mask.shape != (H, W):
                mask = cv2.resize(mask, (W, H))
            
            # Recortar a la región del bounding box para mejorar precisión
            x1, y1, x2, y2 = map(int, bbox)
            mask_cropped = np.zeros_like(mask)
            
            # Aplicar máscara solo en la región del bbox
            if x1 < W and y1 < H and x2 > 0 and y2 > 0:
                # Asegurar que las coordenadas estén dentro de los límites
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(W, x2)
                y2 = min(H, y2)
                
                # Extraer región de la máscara original
                bbox_mask = mask[y1:y2, x1:x2]
                # Aplicar umbral más estricto en la región del bbox
                bbox_mask_binary = (bbox_mask > 0.5).astype(np.float32)
                mask_cropped[y1:y2, x1:x2] = bbox_mask_binary
            
            print(f"   ✅ Máscara generada (con prototipos): {mask.shape}, rango: [{mask.min():.3f}, {mask.max():.3f}]")
            print(f"   📊 Píxeles activos: {np.sum(mask_cropped > 0.5)} de {mask_cropped.size}")
            
            return mask_cropped
            
        except Exception as e:
            print(f"   ⚠️  Error con prototipos: {e}, usando fallback")
            # Fallback: máscara rectangular simple
            x1, y1, x2, y2 = map(int, bbox)
            H, W = input_shape
            
            mask = np.zeros((H, W), dtype=np.float32)
            mask[y1:y2, x1:x2] = 1.0
            
            print(f"   ✅ Máscara fallback generada: {mask.shape}, píxeles activos: {np.sum(mask > 0.5)}")
            return mask
    
    def _bbox_to_contour(self, x1, y1, x2, y2):
        """Convierte bounding box a formato de contorno OpenCV"""
        return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene estadísticas de rendimiento del segmentador
        
        Returns:
            Dict con estadísticas de rendimiento
        """
        return {
            "tipo": "Segmentador de Defectos",
            "modelo": os.path.basename(self.model_path),
            "clases": self.class_names,
            "num_clases": self.num_classes,
            "confianza_minima": self.confianza_min,
            "tiempo_inferencia_promedio_ms": self.tiempo_inferencia,
            "frames_procesados": self.frames_procesados,
            "input_shape": self.input_shape,
            "output_shapes": self.output_shapes
        }
    
    def liberar(self):
        """Libera recursos del segmentador"""
        try:
            if self.session:
                self.session = None
            print("✅ Recursos del segmentador de defectos liberados")
        except Exception as e:
            print(f"❌ Error liberando segmentador de defectos: {e}")
