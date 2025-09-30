"""
Utilidades comunes para el sistema de análisis de coples
"""

import os
import time
import json
import cv2
import numpy as np
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Importar configuración
from config import FileConfig, GlobalConfig


def verificar_dependencias() -> bool:
    """
    Verifica que todas las dependencias necesarias estén disponibles.
    
    Returns:
        bool: True si todas las dependencias están disponibles
    """
    dependencias_ok = True
    
    # Verificar OpenCV
    try:
        cv2_version = cv2.__version__
        print(f"✅ OpenCV {cv2_version} disponible")
    except ImportError:
        print("❌ OpenCV no disponible")
        dependencias_ok = False
    
    # Verificar NumPy
    try:
        np_version = np.__version__
        print(f"✅ NumPy {np_version} disponible")
    except ImportError:
        print("❌ NumPy no disponible")
        dependencias_ok = False
    
    # Verificar ONNX Runtime
    try:
        import onnxruntime as ort
        ort_version = ort.__version__
        print(f"✅ ONNX Runtime {ort_version} disponible")
    except ImportError:
        print("⚠️ ONNX Runtime no disponible (se instalará automáticamente)")
    
    return dependencias_ok


def mostrar_info_sistema():
    """Muestra información del sistema y dependencias."""
    print("🚀 SISTEMA DE ANÁLISIS DE COPLES")
    print("=" * 50)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python: {os.sys.version.split()[0]}")
    print(f"📁 Directorio de trabajo: {os.getcwd()}")
    print("=" * 50)


def generar_nombre_archivo(timestamp: str, count: int, extension: str = None) -> str:
    """
    Genera un nombre de archivo único.
    
    Args:
        timestamp (str): Timestamp en formato específico
        count (int): Contador de archivo
        extension (str, optional): Extensión del archivo
        
    Returns:
        str: Nombre del archivo generado
    """
    if extension is None:
        extension = FileConfig.IMAGE_FORMAT
    
    # Remover extensión si ya está incluida
    if extension.startswith('.'):
        extension = extension[1:]
    
    filename = FileConfig.FILENAME_TEMPLATE.format(
        timestamp=timestamp,
        count=count,
        ext=f".{extension}"
    )
    
    return filename


def guardar_imagen_clasificacion(
    imagen: np.ndarray, 
    clase_predicha: str, 
    confianza: float,
    tiempo_captura: float,
    tiempo_inferencia: float,
    count: int
) -> Tuple[Optional[str], Optional[str]]:
    """
    Guarda la imagen clasificada y genera el archivo JSON correspondiente.
    
    Args:
        imagen (np.ndarray): Imagen a guardar
        clase_predicha (str): Clase predicha
        confianza (float): Nivel de confianza
        tiempo_captura (float): Tiempo de captura en ms
        tiempo_inferencia (float): Tiempo de inferencia en ms
        count (int): Contador de archivo
        
    Returns:
        tuple: (ruta_imagen, ruta_json) o (None, None) si hay error
    """
    try:
        # Asegurar que el directorio de salida existe
        GlobalConfig.ensure_output_dir()
        
        # Generar timestamp
        timestamp = time.strftime(FileConfig.TIMESTAMP_FORMAT)
        
        # Generar nombres de archivo
        nombre_imagen = generar_nombre_archivo(timestamp, count, FileConfig.IMAGE_FORMAT)
        nombre_json = generar_nombre_archivo(timestamp, count, FileConfig.JSON_FORMAT)
        
        # Rutas completas
        ruta_imagen = os.path.join(FileConfig.OUTPUT_DIR, nombre_imagen)
        ruta_json = os.path.join(FileConfig.OUTPUT_DIR, nombre_json)
        
        # Guardar imagen
        cv2.imwrite(ruta_imagen, imagen)
        print(f"📁 Imagen guardada: {ruta_imagen}")
        
        # Crear datos JSON
        datos_json = {
            'archivo_imagen': nombre_imagen,
            'clase_predicha': clase_predicha,
            'confianza': confianza,
            'tiempo_captura_ms': tiempo_captura,
            'tiempo_inferencia_ms': tiempo_inferencia,
            'tiempo_total_ms': tiempo_captura + tiempo_inferencia,
            'timestamp': datetime.now().isoformat(),
            'modelo': 'CopleClasDef2C1V.onnx',
            'resolucion': {
                'ancho': imagen.shape[1],
                'alto': imagen.shape[0],
                'canales': imagen.shape[2] if len(imagen.shape) > 2 else 1
            }
        }
        
        # Guardar JSON
        with open(ruta_json, 'w', encoding='utf-8') as f:
            json.dump(datos_json, f, indent=2, ensure_ascii=False)
        
        print(f"📁 JSON guardado: {ruta_json}")
        
        return ruta_imagen, ruta_json
        
    except Exception as e:
        print(f"❌ Error guardando archivos: {e}")
        return None, None


def calcular_estadisticas_tiempo(tiempos: list) -> Dict[str, float]:
    """
    Calcula estadísticas de una lista de tiempos.
    
    Args:
        tiempos (list): Lista de tiempos en milisegundos
        
    Returns:
        dict: Estadísticas calculadas
    """
    if not tiempos:
        return {
            'promedio': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0,
            'total': 0.0
        }
    
    tiempos_array = np.array(tiempos)
    
    return {
        'promedio': float(np.mean(tiempos_array)),
        'std': float(np.std(tiempos_array)),
        'min': float(np.min(tiempos_array)),
        'max': float(np.max(tiempos_array)),
        'total': float(np.sum(tiempos_array))
    }


def formatear_tiempo(tiempo_ms: float) -> str:
    """
    Formatea un tiempo en milisegundos a formato legible.
    
    Args:
        tiempo_ms (float): Tiempo en milisegundos
        
    Returns:
        str: Tiempo formateado
    """
    if tiempo_ms < 1.0:
        return f"{tiempo_ms:.3f} ms"
    elif tiempo_ms < 1000.0:
        return f"{tiempo_ms:.1f} ms"
    else:
        return f"{tiempo_ms/1000:.2f} s"


def limpiar_memoria():
    """Limpia la memoria del sistema."""
    try:
        import gc
        gc.collect()
        
        # Limpiar memoria de OpenCV si es posible
        try:
            cv2.destroyAllWindows()
            cv2.waitKey(1)
        except:
            pass
        
        print("🧹 Memoria limpiada")
        
    except Exception as e:
        print(f"⚠️ Error limpiando memoria: {e}")


def verificar_archivo_modelo(ruta_modelo: str) -> bool:
    """
    Verifica que un archivo de modelo existe y es válido.
    
    Args:
        ruta_modelo (str): Ruta al archivo del modelo
        
    Returns:
        bool: True si el archivo es válido
    """
    try:
        # Verificar que el archivo existe
        if not os.path.exists(ruta_modelo):
            print(f"❌ Modelo no encontrado: {ruta_modelo}")
            return False
        
        # Verificar que es un archivo
        if not os.path.isfile(ruta_modelo):
            print(f"❌ No es un archivo válido: {ruta_modelo}")
            return False
        
        # Verificar extensión
        if not ruta_modelo.lower().endswith('.onnx'):
            print(f"❌ Extensión no válida (debe ser .onnx): {ruta_modelo}")
            return False
        
        # Verificar tamaño del archivo
        tamano = os.path.getsize(ruta_modelo)
        if tamano < 1024:  # Menos de 1KB
            print(f"❌ Archivo demasiado pequeño: {tamano} bytes")
            return False
        
        print(f"✅ Modelo válido: {ruta_modelo} ({tamano/1024/1024:.1f} MB)")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando modelo: {e}")
        return False


def crear_directorio_salida() -> bool:
    """
    Crea el directorio de salida si no existe.
    
    Returns:
        bool: True si el directorio se creó o ya existía
    """
    try:
        if not os.path.exists(FileConfig.OUTPUT_DIR):
            os.makedirs(FileConfig.OUTPUT_DIR)
            print(f"📁 Directorio de salida creado: {FileConfig.OUTPUT_DIR}")
        else:
            print(f"📁 Directorio de salida ya existe: {FileConfig.OUTPUT_DIR}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando directorio de salida: {e}")
        return False


def obtener_info_imagen(imagen: np.ndarray) -> Dict[str, Any]:
    """
    Obtiene información básica de una imagen.
    
    Args:
        imagen (np.ndarray): Imagen a analizar
        
    Returns:
        dict: Información de la imagen
    """
    try:
        info = {
            'forma': imagen.shape,
            'tipo_dato': str(imagen.dtype),
            'dimensiones': len(imagen.shape),
            'tamano_bytes': imagen.nbytes
        }
        
        if len(imagen.shape) >= 2:
            info.update({
                'ancho': imagen.shape[1],
                'alto': imagen.shape[0]
            })
        
        if len(imagen.shape) == 3:
            info['canales'] = imagen.shape[2]
        
        return info
        
    except Exception as e:
        print(f"❌ Error obteniendo info de imagen: {e}")
        return {}


def log_performance(operacion: str, tiempo_ms: float, detalles: str = ""):
    """
    Registra información de rendimiento.
    
    Args:
        operacion (str): Nombre de la operación
        tiempo_ms (float): Tiempo en milisegundos
        detalles (str): Detalles adicionales
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    if detalles:
        print(f"⏱️  [{timestamp}] {operacion}: {tiempo_ms:.2f} ms - {detalles}")
    else:
        print(f"⏱️  [{timestamp}] {operacion}: {tiempo_ms:.2f} ms")


def mostrar_progreso(actual: int, total: int, descripcion: str = "Progreso"):
    """
    Muestra una barra de progreso simple.
    
    Args:
        actual (int): Valor actual
        total (int): Valor total
        descripcion (str): Descripción del progreso
    """
    if total <= 0:
        return
    
    porcentaje = (actual / total) * 100
    barra_largo = 30
    completado = int((actual / total) * barra_largo)
    
    barra = "█" * completado + "░" * (barra_largo - completado)
    
    print(f"\r{descripcion}: |{barra}| {porcentaje:.1f}% ({actual}/{total})", end="")
    
    if actual >= total:
        print()  # Nueva línea al completar
