"""
Motor de detección de defectos de coples usando ONNX
Basado en el modelo CopleDetDef1C2V.onnx
"""

import cv2
import numpy as np
import time
import os
from typing import List, Dict, Tuple, Optional

# Importar configuración
from analisis_coples.expo_config import ModelsConfig, GlobalConfig

# Importar decodificador YOLOv11
from .yolov11_decoder import YOLOv11Decoder


class DetectorDefectosCoples:
    """
    Motor de detección de defectos de coples usando ONNX.
    
    Características:
    - Carga y ejecuta modelo ONNX de detección de defectos
    - Preprocesamiento automático de imágenes
    - Postprocesamiento con decodificador YOLOv11
    - Gestión de confianza y NMS
    - Estadísticas de rendimiento
    """
    
    def __init__(self, model_path: Optional[str] = None, confianza_min: float = 0.3):
        """
        Inicializa el detector de defectos de coples.
        
        Args:
            model_path (str, optional): Ruta al modelo ONNX. Si no se proporciona, usa el por defecto.
            confianza_min (float): Umbral mínimo de confianza para detecciones
        """
        self.model_path = model_path or os.path.join(
            ModelsConfig.MODELS_DIR, 
            ModelsConfig.DETECTION_DEFECTOS_MODEL
        )
        self.classes_path = os.path.join(
            ModelsConfig.MODELS_DIR, 
            ModelsConfig.DETECTION_DEFECTOS_CLASSES
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
        
        # Decodificador YOLOv11 DESPUÉS de cargar clases
        self.decoder = YOLOv11Decoder(
            confianza_min=confianza_min,
            iou_threshold=0.35,
            max_det=30,
            class_names=self.class_names  # Pasar las clases del detector de defectos
        )
    
    def _cargar_clases(self):
        """Carga las clases desde el archivo de texto."""
        try:
            if os.path.exists(self.classes_path):
                with open(self.classes_path, 'r', encoding='utf-8') as f:
                    self.class_names = [line.strip() for line in f.readlines() if line.strip()]
                self.num_classes = len(self.class_names)
                print(f"✅ Clases de defectos cargadas: {self.class_names}")
            else:
                print(f"⚠️ Archivo de clases de defectos no encontrado: {self.classes_path}")
                # Clases por defecto para defectos
                self.class_names = ["Defecto_1", "Defecto_2"]
                self.num_classes = 2
        except Exception as e:
            print(f"❌ Error cargando clases de defectos: {e}")
            # Clases por defecto
            self.class_names = ["Defecto_1", "Defecto_2"]
            self.num_classes = 2
    
    def inicializar(self) -> bool:
        """
        Inicializa el motor de detección de defectos.
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            print(f"🎯 Inicializando detector de defectos...")
            
            # Verificar que el modelo existe
            if not os.path.exists(self.model_path):
                print(f"❌ Modelo de defectos no encontrado: {self.model_path}")
                return False
            
            # Cargar modelo ONNX
            import onnxruntime as ort
            
            # Configurar proveedores
            providers = ['CPUExecutionProvider']
            if ort.get_device() == 'GPU':
                providers = ['CUDAExecutionProvider'] + providers
            
            # Crear sesión
            self.session = ort.InferenceSession(
                self.model_path, 
                providers=providers
            )
            
            # Obtener información del modelo
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [output.name for output in self.session.get_outputs()]
            self.input_shape = self.session.get_inputs()[0].shape
            self.output_shapes = [output.shape for output in self.session.get_outputs()]
            
            print(f"🧠 Motor de detección de defectos ONNX inicializado:")
            print(f"   📁 Modelo: {os.path.basename(self.model_path)}")
            print(f"   📊 Input: {self.input_name} - Shape: {self.input_shape}")
            print(f"   📊 Outputs: {self.output_names}")
            print(f"   🎯 Clases: {self.num_classes}")
            print(f"   🔧 Proveedores: {providers}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando detector de defectos: {e}")
            return False
    
    def preprocesar_imagen(self, imagen: np.ndarray) -> np.ndarray:
        """
        Preprocesa la imagen para el modelo de detección de defectos
        
        Args:
            imagen: Imagen RGB de entrada (H, W, C)
            
        Returns:
            Imagen preprocesada lista para inferencia
        """
        try:
            # Redimensionar a la entrada del modelo
            imagen_resized = cv2.resize(imagen, (self.input_size, self.input_size))
            
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
    
    def detectar_defectos(self, imagen: np.ndarray) -> List[Dict]:
        """
        Detecta defectos en la imagen
        
        Args:
            imagen: Imagen RGB de entrada (H, W, C)
            
        Returns:
            Lista de detecciones con bbox, clase y confianza
        """
        try:
            # Debug: Mostrar tamaño de imagen original
            print(f"🔍 Debug imagen defectos - Original: {imagen.shape}")
            print(f"🔍 Debug imagen defectos - Input shape esperado: {self.input_size}")
            
            # Preprocesar imagen
            imagen_input = self.preprocesar_imagen(imagen)
            
            # Debug: Mostrar tamaño de imagen procesada
            print(f"🔍 Debug imagen defectos - Procesada: {imagen_input.shape}")
            
            # Ejecutar inferencia sin timeout (tiempo no es crítico)
            tiempo_inicio = time.time()
            
            try:
                outputs = self.session.run(
                    self.output_names,
                    {self.input_name: imagen_input}
                )
                
                tiempo_inferencia = (time.time() - tiempo_inicio) * 1000  # ms
                
            except Exception as e:
                print(f"⚠️ Error en detección de defectos: {e}")
                return []
            
            # Actualizar estadísticas
            self.tiempo_inferencia = tiempo_inferencia
            self.frames_procesados += 1
            
            # Obtener dimensiones de la imagen de entrada para el decodificador
            imagen_height, imagen_width = imagen.shape[:2]
            
            # Procesar salidas usando el decodificador YOLOv11
            detecciones = self.decoder.decode_output(outputs[0], (imagen_height, imagen_width))
            
            return detecciones
            
        except Exception as e:
            print(f"❌ Error en detección de defectos: {e}")
            return []
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene estadísticas de rendimiento del detector
        
        Returns:
            Dict con estadísticas de rendimiento
        """
        return {
            "tipo": "Detector de Defectos",
            "modelo": os.path.basename(self.model_path),
            "clases": self.class_names,
            "num_clases": self.num_classes,
            "confianza_minima": self.confianza_min,
            "tiempo_inferencia_promedio_ms": self.tiempo_inferencia,
            "frames_procesados": self.frames_procesados,
            "input_shape": self.input_shape,
            "output_shapes": self.output_shapes
        }
    
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
    
    def liberar(self):
        """Libera recursos del detector"""
        try:
            if self.session:
                self.session = None
            print("✅ Recursos del detector de defectos liberados")
        except Exception as e:
            print(f"❌ Error liberando detector de defectos: {e}")
