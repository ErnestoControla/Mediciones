"""
Configuración del sistema de análisis de coples
Contiene todas las constantes y parámetros configurables
"""

import os

# ==================== CONFIGURACIÓN DE CÁMARA ====================
class CameraConfig:
    """Configuración de la cámara GigE"""
    
    # Conexión
    DEFAULT_IP = "172.16.1.21"
    MAX_CAMERAS = 16
    
    # Resolución nativa de la cámara
    NATIVE_WIDTH = 4112
    NATIVE_HEIGHT = 2176
    
    # Parámetros de captura optimizados para resolución estándar
    EXPOSURE_TIME = 20000      # 20ms - tiempo de exposición optimizado
    FRAMERATE = 10.0          # 10 FPS - reducido para menor carga CPU
    PACKET_SIZE = 9000        # Tamaño de paquete jumbo
    NUM_BUFFERS = 2           # Solo 2 buffers para minimizar memoria
    GAIN = 2.0               # Ganancia mínima para mejor calidad
    
    # Configuración del ROI
    ROI_WIDTH = 640
    ROI_HEIGHT = 640
    ROI_OFFSET_X = 1736      # Centrado horizontalmente: (4112 - 640) / 2
    ROI_OFFSET_Y = 768       # Centrado verticalmente: (2176 - 640) / 2
    
    # Timeouts (en segundos)
    FRAME_TIMEOUT = 0.1       # 100ms timeout para frames
    STARTUP_TIMEOUT = 5.0     # 5s timeout para primer frame
    SHUTDOWN_TIMEOUT = 2.0    # 2s timeout para cerrar thread

# ==================== CONFIGURACIÓN DE WEBCAM FALLBACK ====================
class WebcamConfig:
    """Configuración de webcam como fallback"""
    
    # Habilitar fallback automático
    ENABLE_FALLBACK = True
    
    # Configuración de webcam
    DEFAULT_DEVICE_ID = 0     # ID del dispositivo por defecto
    WIDTH = 640              # Ancho de la imagen objetivo
    HEIGHT = 640             # Alto de la imagen objetivo
    FPS = 30                 # Frames por segundo
    USE_CROP = True          # Usar recorte en lugar de redimensionado
    
    # Resolución nativa detectada de la webcam
    NATIVE_WIDTH = 1280      # Resolución nativa real detectada
    NATIVE_HEIGHT = 720      # Resolución nativa real detectada
    
    # Búsqueda de dispositivos
    MAX_DEVICES_TO_CHECK = 10  # Máximo número de dispositivos a verificar
    
    # Timeouts
    DETECTION_TIMEOUT = 3.0    # Timeout para detectar webcams
    INIT_TIMEOUT = 5.0         # Timeout para inicializar webcam

# ==================== CONFIGURACIÓN DE MODELOS ====================
class ModelsConfig:
    """Configuración de los modelos ONNX"""
    
    # Directorio de modelos
    MODELS_DIR = "/app/analisis_coples/Modelos"
    
    # Modelo de clasificación
    CLASSIFICATION_MODEL = "CopleClasDef2C1V.onnx"
    CLASSIFICATION_CLASSES = "clases_CopleClasDef2C1V.txt"
    
    # Modelos de detección
    DETECTION_DEFECTOS_MODEL = "CopleDetDef1C2V.onnx"
    DETECTION_DEFECTOS_CLASSES = "clases_CopleDetDef1C2V.txt"
    DETECTION_PARTS_MODEL = "CopleDetPZ1C1V.onnx"
    
    # Modelos de segmentación
    SEGMENTATION_DEFECTOS_MODEL = "CopleSegDef1C8V.onnx"
    SEGMENTATION_DEFECTOS_CLASSES = "clases_CopleSegDef1C8V.txt"
    SEGMENTATION_PARTS_MODEL = "CopleSegPZ1C1V.onnx"
    SEGMENTATION_PARTS_CLASSES = "clases_CopleSegPZ1C1V.txt"
    
    # Parámetros de inferencia - CONFIGURACIÓN ALTA PRECISIÓN
    INPUT_SIZE = 640          # Resolución del modelo (640x640)
    CONFIDENCE_THRESHOLD = 0.55  # Configuración alta precisión (mejor calidad de detección)
    IOU_THRESHOLD = 0.35      # IoU threshold alto para eliminar duplicados
    MAX_DETECTIONS = 30       # Aumentado para permitir más detecciones
    
    # Configuración ONNX
    INTRA_OP_THREADS = 2
    INTER_OP_THREADS = 2
    PROVIDERS = ['CPUExecutionProvider']

# ==================== CONFIGURACIÓN DE ROBUSTEZ ====================
class RobustezConfig:
    """Configuración para robustez ante cambios de iluminación"""
    
    # Configuraciones de umbrales por condiciones
    UMBRALES_ORIGINAL = {
        'confianza_min': 0.55,
        'iou_threshold': 0.35,
        'descripcion': 'Configuración original - alta precisión'
    }
    
    UMBRALES_MODERADA = {
        'confianza_min': 0.3,
        'iou_threshold': 0.2,
        'descripcion': 'Configuración moderada - mejor rendimiento en condiciones difíciles'
    }
    
    UMBRALES_PERMISIVA = {
        'confianza_min': 0.1,
        'iou_threshold': 0.1,
        'descripcion': 'Configuración permisiva - para condiciones muy difíciles'
    }
    
    UMBRALES_ULTRA_PERMISIVA = {
        'confianza_min': 0.01,
        'iou_threshold': 0.01,
        'descripcion': 'Configuración ultra permisiva - para condiciones extremas'
    }
    
    # Configuración por defecto (alta precisión)
    CONFIGURACION_DEFAULT = UMBRALES_ORIGINAL
    
    # Parámetros de preprocesamiento
    APLICAR_PREPROCESAMIENTO = False  # Por defecto desactivado para evitar colgadas
    CLAHE_CLIP_LIMIT = 2.0
    CLAHE_TILE_GRID_SIZE = (8, 8)
    
    # Límites de ajuste automático
    CONFIANZA_MIN_LIMITE = 0.1
    CONFIANZA_MAX_LIMITE = 0.8
    IOU_MIN_LIMITE = 0.01
    IOU_MAX_LIMITE = 0.5

# ==================== CONFIGURACIÓN DE FUSIÓN DE MÁSCARAS ====================
class FusionConfig:
    """Configuración para fusión de máscaras de objetos pegados"""
    
    # Configuraciones por defecto
    DISTANCIA_MAXIMA_DEFAULT = 30      # píxeles
    OVERLAP_MINIMO_DEFAULT = 0.1       # 10%
    AREA_MINIMA_FUSION_DEFAULT = 100   # píxeles
    
    # Configuraciones específicas por tipo de objeto
    CONFIGURACIONES = {
        'conservadora': {
            'distancia_maxima': 20,
            'overlap_minimo': 0.2,
            'area_minima_fusion': 200,
            'descripcion': 'Configuración conservadora - solo fusiona objetos muy pegados'
        },
        'moderada': {
            'distancia_maxima': 30,
            'overlap_minimo': 0.1,
            'area_minima_fusion': 100,
            'descripcion': 'Configuración moderada - balance entre precisión y fusión'
        },
        'agresiva': {
            'distancia_maxima': 50,
            'overlap_minimo': 0.05,
            'area_minima_fusion': 50,
            'descripcion': 'Configuración agresiva - fusiona objetos cercanos'
        }
    }
    
    # Configuración por defecto
    CONFIGURACION_DEFAULT = 'moderada'

# ==================== CONFIGURACIÓN DE VISUALIZACIÓN ====================
class VisualizationConfig:
    """Configuración de visualización y colores"""
    
    # Colores para clasificación (BGR format)
    ACCEPTED_COLOR = (0, 255, 0)        # Verde para "Aceptado"
    REJECTED_COLOR = (0, 0, 255)        # Rojo para "Rechazado"
    TEXT_COLOR = (255, 255, 255)        # Blanco para texto
    BACKGROUND_COLOR = (0, 0, 0)        # Negro para fondo
    
    # Parámetros de visualización
    FONT = 0  # cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE = 1.0
    FONT_THICKNESS = 2
    TEXT_PADDING = 10
    TEXT_POSITION = (10, 30)            # Posición (x, y) del texto

# ==================== CONFIGURACIÓN DE ARCHIVOS ====================
class FileConfig:
    """Configuración de archivos y directorios"""
    
    # Directorios
    OUTPUT_DIR = "Salida_cople"
    
    # Formatos de archivo
    IMAGE_FORMAT = ".jpg"
    JSON_FORMAT = ".json"
    TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
    
    # Nombres de archivo
    FILENAME_TEMPLATE = "cople_clasificacion_{timestamp}_#{count}{ext}"

# ==================== CONFIGURACIÓN DE ESTADÍSTICAS ====================
class StatsConfig:
    """Configuración de estadísticas y métricas"""
    
    # Tamaños de colas para estadísticas
    CAPTURE_TIMES_QUEUE_SIZE = 100
    PROCESSING_TIMES_QUEUE_SIZE = 100
    INFERENCE_TIMES_QUEUE_SIZE = 100

# ==================== CONFIGURACIÓN GLOBAL ====================
class GlobalConfig:
    """Configuración global del sistema"""
    
    # Rutas comunes
    GIGEV_COMMON_PATH = "../gigev_common"
    
    # Límites de memoria
    BUFFER_MARGIN = 8192  # Margen extra para buffers
    
    # Configuración del sistema
    DEBUG_MODE = True
    SAVE_ORIGINAL_IMAGES = True
    
    @classmethod
    def ensure_output_dir(cls):
        """Asegura que el directorio de salida existe"""
        if not os.path.exists(FileConfig.OUTPUT_DIR):
            os.makedirs(FileConfig.OUTPUT_DIR)
            print(f"📁 Directorio de salida creado: {FileConfig.OUTPUT_DIR}")

# ==================== CONFIGURACIÓN DE DESARROLLO ====================
class DevConfig:
    """Configuración para desarrollo y debugging"""
    
    # Guardar resultados intermedios
    SAVE_INTERMEDIATE_RESULTS = True
    SAVE_DEBUG_IMAGES = True
    
    # Logging detallado
    VERBOSE_LOGGING = True
    SHOW_TIMING_DETAILS = True
