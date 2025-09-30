"""
Motor de inferencia ONNX para clasificación de coples
"""

import cv2
import numpy as np
import time
import os
import json
from typing import Tuple, Dict, Any, Optional

# Importar configuración
from analisis_coples.expo_config import ModelsConfig, GlobalConfig


class ClasificadorCoplesONNX:
    """
    Motor de inferencia ONNX para clasificación de coples.
    
    Características:
    - Carga y ejecuta modelos ONNX de clasificación
    - Preprocesamiento automático de imágenes
    - Postprocesamiento de resultados
    - Gestión de clases y confianza
    - Estadísticas de rendimiento
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Inicializa el clasificador de coples.
        
        Args:
            model_path (str, optional): Ruta al modelo ONNX. Si no se proporciona, usa el por defecto.
        """
        self.model_path = model_path or os.path.join(
            ModelsConfig.MODELS_DIR, 
            ModelsConfig.CLASSIFICATION_MODEL
        )
        self.classes_path = os.path.join(
            ModelsConfig.MODELS_DIR, 
            ModelsConfig.CLASSIFICATION_CLASSES
        )
        
        # Estado del modelo
        self.model = None
        self.session = None
        self.input_name = None
        self.output_name = None
        self.input_shape = None
        self.output_shape = None
        
        # Clases del modelo
        self.class_names = []
        self.num_classes = 0
        
        # Estadísticas de inferencia
        self.inference_times = []
        self.total_inferences = 0
        self.procesamiento_activo = False
        
        # Configuración
        self.confidence_threshold = ModelsConfig.CONFIDENCE_THRESHOLD
        self.input_size = ModelsConfig.INPUT_SIZE  # 640x640
        
        # Cargar clases
        self._cargar_clases()
    
    def _cargar_clases(self):
        """Carga las clases desde el archivo de texto."""
        try:
            if os.path.exists(self.classes_path):
                with open(self.classes_path, 'r', encoding='utf-8') as f:
                    self.class_names = [line.strip() for line in f.readlines() if line.strip()]
                self.num_classes = len(self.class_names)
                print(f"✅ Clases cargadas: {self.class_names}")
            else:
                print(f"⚠️ Archivo de clases no encontrado: {self.classes_path}")
                # Clases por defecto
                self.class_names = ["Aceptado", "Rechazado"]
                self.num_classes = 2
        except Exception as e:
            print(f"❌ Error cargando clases: {e}")
            # Clases por defecto
            self.class_names = ["Aceptado", "Rechazado"]
            self.num_classes = 2
    
    def inicializar(self) -> bool:
        """
        Inicializa el motor de inferencia ONNX.
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            print(f"🧠 Inicializando clasificador ONNX: {self.model_path}")
            
            # Verificar que el modelo existe
            if not os.path.exists(self.model_path):
                print(f"❌ Modelo no encontrado: {self.model_path}")
                return False
            
            # Intentar importar ONNX Runtime
            try:
                import onnxruntime as ort
                print("✅ ONNX Runtime disponible")
            except ImportError:
                print("❌ ONNX Runtime no disponible. Instala con: pip install onnxruntime")
                return False
            
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
            
            # Obtener información del modelo
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
            self.input_shape = self.session.get_inputs()[0].shape
            self.output_shape = self.session.get_outputs()[0].shape
            
            print(f"   📊 Input: {self.input_name} - Shape: {self.input_shape}")
            print(f"   📊 Output: {self.output_name} - Shape: {self.output_shape}")
            print(f"   🎯 Clases: {self.num_classes}")
            
            self.procesamiento_activo = True
            print("✅ Clasificador inicializado correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando clasificador: {e}")
            return False
    
    def preprocesar_imagen(self, imagen: np.ndarray) -> np.ndarray:
        """
        Preprocesa la imagen para la inferencia.
        
        Args:
            imagen (np.ndarray): Imagen de entrada (BGR)
            
        Returns:
            np.ndarray: Imagen preprocesada en formato [1, 3, 640, 640]
        """
        try:
            # Convertir BGR a RGB
            imagen_rgb = cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)
            
            # Redimensionar a tamaño del modelo
            imagen_resized = cv2.resize(imagen_rgb, (self.input_size, self.input_size))
            
            # Normalizar a [0, 1]
            imagen_normalized = imagen_resized.astype(np.float32) / 255.0
            
            # Transponer de [H, W, C] a [C, H, W] para formato ONNX
            imagen_transposed = np.transpose(imagen_normalized, (2, 0, 1))
            
            # Agregar dimensión de batch: [C, H, W] -> [1, C, H, W]
            imagen_batch = np.expand_dims(imagen_transposed, axis=0)
            
            return imagen_batch
            
        except Exception as e:
            print(f"❌ Error preprocesando imagen: {e}")
            return None
    
    def clasificar(self, imagen: np.ndarray) -> Tuple[Optional[str], float, float]:
        """
        Clasifica una imagen de cople.
        
        Args:
            imagen (np.ndarray): Imagen de entrada (BGR)
            
        Returns:
            tuple: (clase_predicha, confianza, tiempo_inferencia) o (None, 0, 0) si hay error
        """
        if not self.procesamiento_activo or self.session is None:
            return None, 0, 0
        
        try:
            start_time = time.time()
            
            # Preprocesar imagen
            imagen_procesada = self.preprocesar_imagen(imagen)
            if imagen_procesada is None:
                return None, 0, 0
            
            # Ejecutar inferencia
            outputs = self.session.run([self.output_name], {self.input_name: imagen_procesada})
            
            # Calcular tiempo de inferencia
            tiempo_inferencia = (time.time() - start_time) * 1000
            
            # Procesar resultados
            clase_predicha, confianza = self._procesar_resultados(outputs[0])
            
            # Actualizar estadísticas
            self.inference_times.append(tiempo_inferencia)
            self.total_inferences += 1
            
            # Mantener solo los últimos 100 tiempos
            if len(self.inference_times) > 100:
                self.inference_times = self.inference_times[-100:]
            
            return clase_predicha, confianza, tiempo_inferencia
            
        except Exception as e:
            print(f"❌ Error en clasificación: {e}")
            return None, 0, 0
    
    def _procesar_resultados(self, output: np.ndarray) -> Tuple[str, float]:
        """
        Procesa los resultados de la inferencia.
        
        Args:
            output (np.ndarray): Salida del modelo
            
        Returns:
            tuple: (clase_predicha, confianza)
        """
        try:
            # Obtener probabilidades
            if output.ndim > 1:
                probabilities = output[0]  # Remover dimensión de batch
            else:
                probabilities = output
            
            # Encontrar clase con mayor probabilidad
            class_idx = np.argmax(probabilities)
            confidence = float(probabilities[class_idx])
            
            # Verificar umbral de confianza
            if confidence < self.confidence_threshold:
                # Si la confianza es muy baja, usar la clase por defecto
                class_idx = 0  # "Aceptado" por defecto
                confidence = 0.5  # Confianza neutral
            
            # Obtener nombre de la clase
            if 0 <= class_idx < len(self.class_names):
                clase_predicha = self.class_names[class_idx]
            else:
                clase_predicha = "Desconocido"
            
            return clase_predicha, confidence
            
        except Exception as e:
            print(f"❌ Error procesando resultados: {e}")
            return "Error", 0.0
    
    def obtener_info_modelo(self) -> Dict[str, Any]:
        """
        Obtiene información del modelo.
        
        Returns:
            dict: Información del modelo
        """
        return {
            'modelo_path': self.model_path,
            'num_clases': self.num_classes,
            'nombres_clases': self.class_names,
            'input_shape': self.input_shape,
            'output_shape': self.output_shape,
            'procesamiento_activo': self.procesamiento_activo,
            'total_inferences': self.total_inferences,
            'confidence_threshold': self.confidence_threshold,
            'input_size': self.input_size
        }
    
    def mostrar_configuracion(self):
        """Muestra la configuración del clasificador."""
        print(f"\n🧠 CONFIGURACIÓN DEL CLASIFICADOR:")
        print(f"   Modelo: {self.model_path}")
        print(f"   Clases: {self.num_classes}")
        print(f"   Nombres: {', '.join(self.class_names)}")
        print(f"   Input Shape: {self.input_shape}")
        print(f"   Output Shape: {self.output_shape}")
        print(f"   Threshold: {self.confidence_threshold}")
        print(f"   Input Size: {self.input_size}x{self.input_size}")
        print(f"   Estado: {'ACTIVO' if self.procesamiento_activo else 'INACTIVO'}")
        print(f"   Inferencias: {self.total_inferences}")
    
    def obtener_estadisticas_inferencia(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de inferencia.
        
        Returns:
            dict: Estadísticas de inferencia
        """
        if not self.inference_times:
            return {
                'total_inferences': 0,
                'tiempo_promedio': 0,
                'tiempo_min': 0,
                'tiempo_max': 0,
                'tiempo_std': 0
            }
        
        tiempos = np.array(self.inference_times)
        return {
            'total_inferences': self.total_inferences,
            'tiempo_promedio': float(np.mean(tiempos)),
            'tiempo_min': float(np.min(tiempos)),
            'tiempo_max': float(np.max(tiempos)),
            'tiempo_std': float(np.std(tiempos))
        }
    
    def cambiar_umbral_confianza(self, nuevo_umbral: float) -> bool:
        """
        Cambia el umbral de confianza.
        
        Args:
            nuevo_umbral (float): Nuevo umbral (0.0 - 1.0)
            
        Returns:
            bool: True si el cambio fue exitoso
        """
        try:
            if 0.0 <= nuevo_umbral <= 1.0:
                self.confidence_threshold = nuevo_umbral
                print(f"✅ Umbral de confianza cambiado a: {nuevo_umbral}")
                return True
            else:
                print(f"❌ Umbral debe estar entre 0.0 y 1.0")
                return False
        except Exception as e:
            print(f"❌ Error cambiando umbral: {e}")
            return False
    
    def liberar(self):
        """Libera los recursos del clasificador."""
        try:
            print("🧹 Liberando recursos del clasificador...")
            
            if self.session:
                self.session = None
            
            self.procesamiento_activo = False
            self.inference_times.clear()
            
            print("✅ Recursos del clasificador liberados")
            
        except Exception as e:
            print(f"⚠️ Error liberando recursos: {e}")
