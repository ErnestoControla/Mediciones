"""
Motor de segmentación de piezas de coples usando ONNX
Basado en el modelo CopleSegPZ1C1V.onnx
MEJORADO basándose en el módulo de defectos que funciona bien
"""

import cv2
import numpy as np
import time
import os
from typing import List, Dict, Tuple, Optional

# Importar configuración
from analisis_coples.expo_config import ModelsConfig, GlobalConfig


class SegmentadorPiezasCoples:
    """
    Motor de segmentación de piezas de coples usando ONNX.
    
    Características:
    - Carga y ejecuta modelo ONNX de segmentación de piezas
    - Preprocesamiento automático de imágenes
    - Postprocesamiento de máscaras de segmentación
    - Gestión de confianza y umbrales
    - Estadísticas de rendimiento
    MEJORADO basándose en el módulo de defectos que funciona bien
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
        
        # Clases del modelo
        self.class_names = []
        self.num_classes = 0
        
        # Estadísticas de inferencia
        self.tiempo_inferencia = 0.0
        self.frames_procesados = 0
        
        # Estadísticas del sistema (compatibilidad con sistema integrado)
        self.stats = {
            'inicializado': False,
            'inferencias_totales': 0,
            'tiempo_total': 0.0,
            'tiempo_promedio': 0.0,
            'ultima_inferencia': 0.0
        }
        
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
                print(f"✅ Clases de segmentación de piezas cargadas: {self.class_names}")
            else:
                print(f"⚠️ Archivo de clases de segmentación de piezas no encontrado: {self.classes_path}")
                # Clases por defecto para segmentación de piezas
                self.class_names = ["Cople"]
                self.num_classes = 1
        except Exception as e:
            print(f"❌ Error cargando clases de segmentación de piezas: {e}")
            # Clases por defecto
            self.class_names = ["Cople"]
            self.num_classes = 1
    
    def _inicializar_modelo(self):
        """Inicializa el motor de segmentación ONNX."""
        try:
            print(f"🎯 Inicializando segmentador de piezas...")
            
            if not os.path.exists(self.model_path):
                print(f"❌ Modelo de segmentación de piezas no encontrado: {self.model_path}")
                return False
            
            import onnxruntime as ort
            
            # Configurar proveedores
            providers = ['CPUExecutionProvider']
            
            # Crear sesión ONNX
            self.session = ort.InferenceSession(self.model_path, providers=providers)
            
            # Obtener información del modelo
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [output.name for output in self.session.get_outputs()]
            self.input_shape = self.session.get_inputs()[0].shape
            self.output_shapes = [output.shape for output in self.session.get_outputs()]
            
            print(f"🧠 Motor de segmentación de piezas ONNX inicializado:")
            print(f"   📁 Modelo: {os.path.basename(self.model_path)}")
            print(f"   📊 Input: {self.input_name} - Shape: {self.input_shape}")
            print(f"   📊 Outputs: {self.output_names}")
            print(f"   🎯 Clases: {self.num_classes}")
            print(f"   🔧 Proveedores: {providers}")
            
            # Marcar como inicializado en las estadísticas
            self.stats['inicializado'] = True
            
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando motor de segmentación de piezas: {e}")
            return False
    
    def procesar_imagen(self, imagen: np.ndarray) -> List[Dict]:
        """
        Procesa una imagen y retorna las segmentaciones detectadas.
        
        Args:
            imagen (np.ndarray): Imagen de entrada (BGR)
            
        Returns:
            List[Dict]: Lista de segmentaciones detectadas
        """
        if self.session is None:
            print("❌ Modelo no inicializado")
            return []
        
        try:
            inicio = time.time()
            
            # Preprocesar imagen
            imagen_procesada = self._preprocesar_imagen(imagen)
            
            # Ejecutar inferencia
            outputs = self.session.run(self.output_names, {self.input_name: imagen_procesada})
            
            # Procesar salidas
            segmentaciones = self._procesar_salidas_segmentacion(outputs)
            
            # Actualizar estadísticas
            self.tiempo_inferencia = (time.time() - inicio) * 1000
            self.frames_procesados += 1
            
            # Actualizar estadísticas del sistema
            self.stats['inferencias_totales'] += 1
            self.stats['tiempo_total'] += self.tiempo_inferencia
            self.stats['tiempo_promedio'] = self.stats['tiempo_total'] / self.stats['inferencias_totales']
            self.stats['ultima_inferencia'] = self.tiempo_inferencia
            
            return segmentaciones
            
        except Exception as e:
            print(f"❌ Error procesando imagen: {e}")
            return []
    
    def segmentar(self, imagen: np.ndarray) -> List[Dict]:
        """
        Método de compatibilidad con el sistema integrado.
        Alias para procesar_imagen.
        
        Args:
            imagen (np.ndarray): Imagen de entrada (BGR)
            
        Returns:
            List[Dict]: Lista de segmentaciones detectadas
        """
        return self.procesar_imagen(imagen)
    
    def _preprocesar_imagen(self, imagen: np.ndarray) -> np.ndarray:
        """Preprocesa la imagen para el modelo ONNX."""
        try:
            # Redimensionar a 640x640
            imagen_resized = cv2.resize(imagen, (self.input_size, self.input_size))
            
            # Convertir BGR a RGB
            imagen_rgb = cv2.cvtColor(imagen_resized, cv2.COLOR_BGR2RGB)
            
            # Normalizar a [0, 1]
            imagen_normalizada = imagen_rgb.astype(np.float32) / 255.0
            
            # Transponer a formato CHW (Channels, Height, Width)
            imagen_chw = np.transpose(imagen_normalizada, (2, 0, 1))
            
            # Agregar dimensión de batch
            imagen_batch = np.expand_dims(imagen_chw, axis=0)
            
            return imagen_batch
            
        except Exception as e:
            print(f"❌ Error preprocesando imagen: {e}")
            return None
    
    def _procesar_salidas_segmentacion(self, outputs):
        """
        Procesa las salidas del modelo YOLO11-SEG para extraer segmentaciones
        BASADO EN EL MÉTODO DE DEFECTOS QUE FUNCIONA BIEN
        """
        print(f"🔍 Procesando salidas de segmentación de piezas...")
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
                    
                    # Calcular dimensiones reales de la máscara
                    if mask is not None:
                        # Encontrar píxeles activos en la máscara
                        y_coords, x_coords = np.where(mask > 0.5)
                        if len(x_coords) > 0 and len(y_coords) > 0:
                            ancho_mascara_real = int(np.max(x_coords) - np.min(x_coords))
                            alto_mascara_real = int(np.max(y_coords) - np.min(y_coords))
                        else:
                            # Fallback a dimensiones del bbox
                            ancho_mascara_real = int(x2 - x1)
                            alto_mascara_real = int(y2 - y1)
                    else:
                        # Fallback a dimensiones del bbox
                        ancho_mascara_real = int(x2 - x1)
                        alto_mascara_real = int(y2 - y1)
                    
                    # Crear segmentación con máscaras reales
                    segmentacion = {
                        "clase": "Cople",
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
                        "ancho_mascara": ancho_mascara_real,
                        "alto_mascara": alto_mascara_real,
                        "mascara": mask,  # Mantener como numpy array
                        "coeficientes_mascara": mask_coeff.tolist()[:5],  # Solo primeros 5 coeficientes
                        "contorno": self._bbox_to_contour(x1, y1, x2, y2)
                    }
                    
                    # Debug de máscara
                    if mask is not None:
                        print(f"   ✅ Máscara creada: {mask.shape}, área: {mask_area}")
                    else:
                        print(f"   ⚠️  Máscara fallback creada: área: {mask_area}")
                    
                    segmentaciones.append(segmentacion)
                    print(f"✅ Segmentación: Cople - {confidence:.3f} - BBox: ({int(x1)},{int(y1)}) a ({int(x2)},{int(y2)}) - Área: {int((x2 - x1) * (y2 - y1))} - Máscara: {ancho_mascara_real}x{alto_mascara_real}")
            else:
                print(f"   ❌ No se encontraron detecciones después de NMS")
        else:
            print(f"   ⚠️ DEBUG: Se esperaban al menos 2 outputs, se recibieron {len(outputs)}")
        
        print(f"🎯 Total segmentaciones de piezas encontradas: {len(segmentaciones)}")
        
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
        OPTIMIZADO PARA EVITAR TIMEOUTS DE CPU
        """
        try:
            # OPTIMIZACIÓN: Usar operación más eficiente que np.tensordot
            # Extraer prototipos (shape: [1, 32, 160, 160])
            protos = mask_protos[0]  # Shape: [32, 160, 160]
            
            # OPTIMIZACIÓN: Usar np.dot en lugar de np.tensordot para mejor rendimiento
            # Reshape para operación más eficiente
            protos_reshaped = protos.reshape(32, -1)  # Shape: [32, 160*160]
            mask_flat = np.dot(mask_coeffs, protos_reshaped)  # Shape: [160*160]
            mask = mask_flat.reshape(160, 160)  # Shape: [160, 160]
            
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
                # Aplicar umbral MÁS ESTRICTO para evitar máscaras muy grandes
                bbox_mask_binary = (bbox_mask > 0.7).astype(np.float32)  # Cambiado de 0.5 a 0.7
                mask_cropped[y1:y2, x1:x2] = bbox_mask_binary
                
                # Validar que la máscara no sea demasiado grande
                pixels_activos = np.sum(mask_cropped > 0.5)
                area_bbox = (x2 - x1) * (y2 - y1)
                if pixels_activos > area_bbox * 0.8:  # Si cubre más del 80% del bbox
                    print(f"   ⚠️ Máscara muy grande ({pixels_activos} píxeles), usando umbral más estricto")
                    bbox_mask_binary = (bbox_mask > 0.8).astype(np.float32)  # Umbral aún más estricto
                    mask_cropped[y1:y2, x1:x2] = bbox_mask_binary
            
            pixels_activos = np.sum(mask_cropped > 0.5)
            print(f"   ✅ Máscara generada (optimizada): {mask.shape}, rango: [{mask.min():.3f}, {mask.max():.3f}]")
            print(f"   📊 Píxeles activos: {pixels_activos} de {mask_cropped.size}")
            
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
        """Convierte bbox a contorno"""
        return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
    
    def obtener_estadisticas(self) -> Dict:
        """Retorna estadísticas del motor de segmentación"""
        return {
            "inicializado": self.session is not None,
            "modelo": os.path.basename(self.model_path) if self.model_path else None,
            "clases": self.class_names,
            "num_clases": self.num_classes,
            "confianza_minima": self.confianza_min,
            "tiempo_inferencia_promedio_ms": self.tiempo_inferencia,
            "frames_procesados": self.frames_procesados,
        }
    
    def liberar(self):
        """Libera los recursos del motor"""
        if self.session:
            del self.session
            self.session = None
        print("✅ Recursos del segmentador de piezas liberados")
