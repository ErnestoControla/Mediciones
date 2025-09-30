# analisis_coples/services_real.py

"""
Servicio real para el sistema de análisis de coples integrado con Django
Versión que usa la cámara real y el sistema de análisis completo
"""

import os
import sys
import time
import uuid
import logging
import numpy as np
import cv2
from datetime import datetime
from typing import Dict, Any, Optional
import json

from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

# Importar modelos Django
from .models import ConfiguracionSistema, AnalisisCople
from .resultados_models import (
    ResultadoClasificacion,
    DeteccionPieza,
    DeteccionDefecto,
    SegmentacionDefecto,
    SegmentacionPieza
)

# Importar OpenCV para captura de webcam
import cv2

# Importar sistema real de análisis
from .modules.analysis_system import SistemaAnalisisIntegrado
from .modules.capture.webcam_fallback import WebcamFallback, detectar_mejor_webcam
from .expo_config import WebcamConfig, ModelsConfig

logger = logging.getLogger(__name__)


class ServicioAnalisisCoplesReal:
    """
    Servicio Django que usa el sistema real de análisis de coples
    """
    
    def __init__(self):
        self.inicializado = False
        self.configuracion_activa = None
        self.sistema_analisis = SistemaAnalisisIntegrado()
        self.usando_webcam = False
        
        # Intentar cargar la configuración activa automáticamente
        self._cargar_configuracion_activa()
    
    def _cargar_configuracion_activa(self):
        """Carga la configuración activa de la base de datos"""
        try:
            self.configuracion_activa = ConfiguracionSistema.objects.filter(activa=True).first()
            if self.configuracion_activa:
                logger.info(f"Configuración activa cargada: {self.configuracion_activa.nombre}")
            else:
                logger.warning("No hay configuración activa en la base de datos")
        except Exception as e:
            logger.error(f"Error cargando configuración activa: {e}")
            self.configuracion_activa = None
    
    def inicializar_sistema(self, configuracion_id: Optional[int] = None) -> bool:
        """
        Inicializa el sistema de análisis con la configuración especificada
        
        Args:
            configuracion_id: ID de la configuración a usar. Si es None, usa la activa
            
        Returns:
            bool: True si se inicializó correctamente
        """
        try:
            # Obtener configuración
            if configuracion_id:
                self.configuracion_activa = ConfiguracionSistema.objects.get(id=configuracion_id)
            else:
                self.configuracion_activa = ConfiguracionSistema.objects.filter(activa=True).first()
            
            if not self.configuracion_activa:
                logger.error("No hay configuración activa disponible")
                return False
            
            # Inicializar sistema de análisis real
            if self.sistema_analisis.inicializar():
                self.inicializado = True
                self.usando_webcam = self.sistema_analisis.usando_webcam
                logger.info(f"Sistema de análisis REAL inicializado con configuración: {self.configuracion_activa.nombre}")
                logger.info(f"Usando: {'Webcam' if self.usando_webcam else 'Cámara GigE'}")
                return True
            else:
                logger.error("Error al inicializar el sistema de análisis REAL.")
                return False
            
        except Exception as e:
            logger.error(f"Error inicializando sistema REAL: {e}")
            return False
    
    def _inicializar_webcam(self) -> bool:
        """Inicializa la webcam usando OpenCV"""
        try:
            # Detectar webcam disponible
            webcam_id = self._detectar_webcam()
            if webcam_id is None:
                logger.error("No se encontraron webcams disponibles")
                return False
            
            logger.info(f"📷 Inicializando webcam en dispositivo {webcam_id}")
            
            # Crear objeto VideoCapture
            self.cap = cv2.VideoCapture(webcam_id)
            self.device_id = webcam_id
            
            if not self.cap.isOpened():
                logger.error(f"❌ No se pudo abrir la webcam en dispositivo {webcam_id}")
                return False
            
            # Configurar resolución
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Probar captura
            ret, frame = self.cap.read()
            if not ret or frame is None:
                logger.error("❌ Error en captura de prueba")
                return False
            
            # Obtener resolución real
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"✅ Webcam configurada:")
            logger.info(f"   📐 Resolución: {width}x{height}")
            logger.info(f"   🎬 FPS: {fps:.1f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando webcam: {e}")
            return False
    
    def _detectar_webcam(self) -> Optional[int]:
        """Detecta la mejor webcam disponible"""
        logger.info("🔍 Buscando webcams disponibles...")
        
        # Probar hasta 5 dispositivos
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # Intentar leer un frame para verificar que funciona
                ret, frame = cap.read()
                if ret and frame is not None:
                    logger.info(f"✅ Webcam encontrada en dispositivo {i}")
                    cap.release()
                    return i
                cap.release()
            else:
                cap.release()
        
        logger.error("❌ No se encontraron webcams disponibles")
        return None
    
    def realizar_analisis_completo(self, usuario=None) -> Dict[str, Any]:
        """
        Realiza un análisis completo de cople usando la cámara real
        
        Args:
            usuario: Usuario que realiza el análisis
            
        Returns:
            Dict con el resultado del análisis
        """
        if not self.inicializado:
            return {"error": "Sistema no inicializado"}
        
        try:
            # Generar ID único para el análisis
            id_analisis = f"analisis_{uuid.uuid4().hex[:8]}_{int(time.time())}"
            
            logger.info(f"🔄 Iniciando análisis completo: {id_analisis}")
            
            # Capturar imagen de la cámara
            imagen_capturada = self._capturar_imagen()
            if imagen_capturada is None:
                return {"error": "No se pudo capturar imagen de la cámara"}
            
            logger.info(f"📸 Imagen capturada: {imagen_capturada.shape}")
            
            # Crear registro de análisis en la base de datos
            analisis_db = AnalisisCople.objects.create(
                id_analisis=id_analisis,
                timestamp_captura=timezone.now(),
                tipo_analisis='completo',
                estado='procesando',
                configuracion=self.configuracion_activa,
                usuario=usuario,
                archivo_imagen=f"real_{id_analisis}.jpg",
                archivo_json=f"real_{id_analisis}.json",
                resolucion_ancho=imagen_capturada.shape[1],
                resolucion_alto=imagen_capturada.shape[0],
                resolucion_canales=imagen_capturada.shape[2] if len(imagen_capturada.shape) > 2 else 1,
                tiempo_captura_ms=50.0,
                tiempo_clasificacion_ms=0.0,
                tiempo_deteccion_piezas_ms=0.0,
                tiempo_deteccion_defectos_ms=0.0,
                tiempo_segmentacion_defectos_ms=0.0,
                tiempo_segmentacion_piezas_ms=0.0,
                tiempo_total_ms=0.0,
                metadatos_json={}
            )
            
            # Realizar análisis completo usando el sistema real
            resultados = self.sistema_analisis.analisis_completo()
            
            # Procesar resultados y guardar en base de datos
            self._procesar_resultados_analisis(analisis_db, resultados, imagen_capturada)
            
            logger.info(f"✅ Análisis completo finalizado: {id_analisis}")
            
            return {
                "id_analisis": id_analisis,
                "estado": "completado",
                "resultados": resultados
            }
            
        except Exception as e:
            logger.error(f"Error en análisis completo: {e}")
            return {"error": str(e)}
    
    def realizar_analisis_clasificacion(self, usuario=None) -> Dict[str, Any]:
        """
        Realiza solo clasificación de cople usando la cámara real
        
        Args:
            usuario: Usuario que realiza el análisis
            
        Returns:
            Dict con el resultado del análisis
        """
        if not self.inicializado:
            return {"error": "Sistema no inicializado"}
        
        try:
            # Generar ID único para el análisis
            id_analisis = f"clasificacion_{uuid.uuid4().hex[:8]}_{int(time.time())}"
            
            logger.info(f"🔄 Iniciando análisis de clasificación: {id_analisis}")
            
            # Capturar imagen de la cámara
            imagen_capturada = self._capturar_imagen()
            if imagen_capturada is None:
                return {"error": "No se pudo capturar imagen de la cámara"}
            
            logger.info(f"📸 Imagen capturada: {imagen_capturada.shape}")
            
            # Crear registro de análisis en la base de datos
            analisis_db = AnalisisCople.objects.create(
                id_analisis=id_analisis,
                timestamp_captura=timezone.now(),
                tipo_analisis='clasificacion',
                estado='procesando',
                configuracion=self.configuracion_activa,
                usuario=usuario,
                archivo_imagen=f"real_{id_analisis}.jpg",
                archivo_json=f"real_{id_analisis}.json",
                resolucion_ancho=imagen_capturada.shape[1],
                resolucion_alto=imagen_capturada.shape[0],
                resolucion_canales=imagen_capturada.shape[2] if len(imagen_capturada.shape) > 2 else 1,
                tiempo_captura_ms=50.0,
                tiempo_clasificacion_ms=0.0,
                tiempo_deteccion_piezas_ms=0.0,
                tiempo_deteccion_defectos_ms=0.0,
                tiempo_segmentacion_defectos_ms=0.0,
                tiempo_segmentacion_piezas_ms=0.0,
                tiempo_total_ms=0.0,
                metadatos_json={}
            )
            
            logger.info(f"📝 Registro de análisis creado en BD: {analisis_db.id}")
            
            # Realizar análisis de clasificación usando el sistema real
            resultados = self.sistema_analisis.solo_clasificacion()
            
            # Procesar resultados
            self._procesar_resultados_analisis(analisis_db, resultados, imagen_capturada)
            
            # Verificar que el análisis se guardó correctamente
            analisis_verificado = AnalisisCople.objects.filter(id_analisis=id_analisis).first()
            if analisis_verificado:
                logger.info(f"✅ Análisis verificado en BD: {analisis_verificado.id} - Estado: {analisis_verificado.estado}")
            else:
                logger.error(f"❌ Análisis NO encontrado en BD: {id_analisis}")
            
            logger.info(f"✅ Análisis de clasificación finalizado: {id_analisis}")
            
            return {
                "id_analisis": id_analisis,
                "estado": "completado",
                "resultados": resultados
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de clasificación: {e}")
            return {"error": str(e)}
    
    def _capturar_imagen(self) -> Optional[np.ndarray]:
        """Captura una imagen usando el sistema integrado"""
        try:
            if not self.sistema_analisis or not self.inicializado:
                logger.error("Sistema de análisis no inicializado")
                return None
            
            # Usar el sistema integrado para capturar imagen
            resultado = self.sistema_analisis.capturar_imagen_unica()
            if resultado is None or "error" in resultado:
                logger.error(f"No se pudo capturar frame del sistema integrado: {resultado.get('error', 'Error desconocido')}")
                return None
            
            # Extraer el frame del diccionario de resultados
            frame = resultado.get("frame")
            if frame is None:
                logger.error("Frame no encontrado en resultado de captura")
                return None
            
            logger.info(f"📸 Imagen capturada: {frame.shape}")
            return frame
                
        except Exception as e:
            logger.error(f"Error capturando imagen: {e}")
            return None
    
    def _procesar_frame(self, frame: np.ndarray) -> np.ndarray:
        """Procesa el frame para obtener imagen de 640x640"""
        try:
            height, width = frame.shape[:2]
            
            # Si la imagen ya es 640x640, devolverla tal como está
            if width == 640 and height == 640:
                return frame
            
            # Calcular recorte centrado
            if width >= 640 and height >= 640:
                # Recorte centrado
                start_x = (width - 640) // 2
                start_y = (height - 640) // 2
                return frame[start_y:start_y+640, start_x:start_x+640]
            else:
                # Redimensionar si es menor
                return cv2.resize(frame, (640, 640))
                
        except Exception as e:
            logger.error(f"Error procesando frame: {e}")
            return frame
    
    def _analizar_imagen_webcam(self, imagen: np.ndarray) -> Dict[str, Any]:
        """Analiza una imagen capturada de webcam (versión simplificada)"""
        import random
        
        # Simular análisis basado en características de la imagen
        # En una implementación real, aquí se usarían los modelos de IA
        
        # Análisis básico de la imagen
        altura, ancho = imagen.shape[:2]
        brillo_promedio = np.mean(imagen)
        
        # Simular clasificación basada en características
        if brillo_promedio > 120:
            clase = 'Aceptado'
            confianza = random.uniform(0.8, 0.95)
        else:
            clase = 'Rechazado'
            confianza = random.uniform(0.7, 0.9)
        
        # Simular detecciones
        detecciones_piezas = []
        detecciones_defectos = []
        
        # Generar detecciones basadas en el tamaño de la imagen
        for i in range(random.randint(1, 3)):
            x1 = random.randint(50, ancho - 200)
            y1 = random.randint(50, altura - 200)
            x2 = x1 + random.randint(80, 150)
            y2 = y1 + random.randint(80, 150)
            
            detecciones_piezas.append({
                "clase": f"Pieza_{i+1}",
                "confianza": random.uniform(0.8, 0.95),
                "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                "centroide": {"x": (x1 + x2) // 2, "y": (y1 + y2) // 2},
                "area": (x2 - x1) * (y2 - y1)
            })
        
        return {
            "clasificacion": {
                "clase": clase,
                "confianza": confianza,
                "tiempo_inferencia_ms": 120.0
            },
            "detecciones_piezas": detecciones_piezas,
            "detecciones_defectos": detecciones_defectos,
            "tiempos": {
                "captura_ms": 50.0,
                "clasificacion_ms": 120.0,
                "deteccion_piezas_ms": 200.0,
                "deteccion_defectos_ms": 180.0,
                "segmentacion_defectos_ms": 300.0,
                "segmentacion_piezas_ms": 280.0,
                "total_ms": 1130.0
            },
            "sistema": {
                "version": "1.0.0-webcam",
                "configuracion": self.configuracion_activa.nombre if self.configuracion_activa else "default",
                "camera_type": "webcam"
            }
        }
    
    def _analizar_clasificacion_webcam(self, imagen: np.ndarray) -> Dict[str, Any]:
        """Analiza solo clasificación de una imagen de webcam"""
        import random
        
        # Análisis básico de la imagen
        brillo_promedio = np.mean(imagen)
        
        # Simular clasificación basada en características
        if brillo_promedio > 120:
            clase = 'Aceptado'
            confianza = random.uniform(0.8, 0.95)
        else:
            clase = 'Rechazado'
            confianza = random.uniform(0.7, 0.9)
        
        return {
            "clasificacion": {
                "clase": clase,
                "confianza": confianza,
                "tiempo_inferencia_ms": 120.0
            },
            "tiempos": {
                "captura_ms": 50.0,
                "clasificacion_ms": 120.0,
                "total_ms": 170.0
            },
            "sistema": {
                "version": "1.0.0-webcam",
                "configuracion": self.configuracion_activa.nombre if self.configuracion_activa else "default",
                "camera_type": "webcam"
            }
        }
    
    def _procesar_resultados_analisis(self, analisis_db: AnalisisCople, resultados: Dict[str, Any], imagen: np.ndarray = None):
        """
        Procesa los resultados del análisis y los guarda en la base de datos
        
        Args:
            analisis_db: Instancia del modelo AnalisisCople
            resultados: Resultados del análisis
            imagen: Imagen capturada (opcional, puede venir en resultados)
        """
        try:
            # Obtener imagen de los resultados si no se proporciona
            if imagen is None and "frame" in resultados:
                imagen = resultados["frame"]
            
            # Actualizar tiempos
            if "tiempos" in resultados:
                tiempos = resultados["tiempos"]
                analisis_db.tiempo_captura_ms = tiempos.get('captura_ms', 0.0)
                analisis_db.tiempo_clasificacion_ms = tiempos.get('clasificacion_ms', 0.0)
                analisis_db.tiempo_deteccion_piezas_ms = tiempos.get('deteccion_piezas_ms', 0.0)
                analisis_db.tiempo_deteccion_defectos_ms = tiempos.get('deteccion_defectos_ms', 0.0)
                analisis_db.tiempo_segmentacion_defectos_ms = tiempos.get('segmentacion_defectos_ms', 0.0)
                analisis_db.tiempo_segmentacion_piezas_ms = tiempos.get('segmentacion_piezas_ms', 0.0)
                analisis_db.tiempo_total_ms = tiempos.get('total_ms', 0.0)
            
            # Guardar metadatos JSON completos (convirtiendo frame a base64)
            resultados_json = resultados.copy()
            if "frame" in resultados_json:
                # Convertir frame de numpy a base64 para serialización
                import cv2
                import base64
                frame = resultados_json["frame"]
                if isinstance(frame, np.ndarray):
                    # Convertir de BGR a RGB si es necesario
                    if len(frame.shape) == 3 and frame.shape[2] == 3:
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    else:
                        frame_rgb = frame
                    
                    # Codificar a base64
                    _, buffer = cv2.imencode('.jpg', frame_rgb)
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    resultados_json["frame"] = frame_base64
                    logger.info(f"✅ Frame guardado como base64: {len(frame_base64)} caracteres")
                else:
                    del resultados_json["frame"]  # Remover si no es numpy array
            analisis_db.metadatos_json = resultados_json
            
            # Procesar resultados específicos
            self._guardar_resultados_clasificacion(analisis_db, resultados)
            self._guardar_detecciones_piezas(analisis_db, resultados)
            self._guardar_detecciones_defectos(analisis_db, resultados)
            
            # Guardar imagen procesada si está disponible
            if imagen is not None:
                self._guardar_imagen_procesada(analisis_db, imagen, resultados)
            
            # Marcar como completado
            analisis_db.estado = 'completado'
            analisis_db.save()
            
        except Exception as e:
            logger.error(f"Error procesando resultados: {e}")
            analisis_db.estado = 'error'
            analisis_db.mensaje_error = str(e)
            analisis_db.save()
    
    def _guardar_imagen_procesada(self, analisis_db: AnalisisCople, imagen: np.ndarray, resultados: Dict[str, Any]):
        """Guarda la imagen procesada con los resultados superpuestos"""
        try:
            # Crear imagen procesada con resultados
            imagen_procesada = self._crear_imagen_procesada(imagen, resultados)
            
            # Convertir a bytes
            _, buffer = cv2.imencode('.jpg', imagen_procesada)
            imagen_bytes = buffer.tobytes()
            
            # Guardar en storage
            nombre_archivo = f"procesada_{analisis_db.id_analisis}.jpg"
            archivo = ContentFile(imagen_bytes, name=nombre_archivo)
            
            # Guardar archivo
            ruta_archivo = default_storage.save(f"analisis/{nombre_archivo}", archivo)
            analisis_db.archivo_imagen = ruta_archivo
            analisis_db.save()
            
            logger.info(f"Imagen procesada guardada: {ruta_archivo}")
            
        except Exception as e:
            logger.error(f"Error guardando imagen procesada: {e}")
    
    def _crear_imagen_procesada(self, imagen: np.ndarray, resultados: Dict[str, Any]) -> np.ndarray:
        """Crea una imagen procesada con los resultados superpuestos"""
        try:
            # Copiar imagen original
            imagen_procesada = imagen.copy()
            
            # Dibujar detecciones de piezas
            if "detecciones_piezas" in resultados:
                for deteccion in resultados["detecciones_piezas"]:
                    bbox = deteccion.get("bbox", {})
                    x1, y1 = bbox.get("x1", 0), bbox.get("y1", 0)
                    x2, y2 = bbox.get("x2", 0), bbox.get("y2", 0)
                    
                    # Dibujar rectángulo verde para piezas
                    cv2.rectangle(imagen_procesada, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Dibujar etiqueta
                    etiqueta = f"{deteccion.get('clase', 'Pieza')} ({deteccion.get('confianza', 0):.2f})"
                    cv2.putText(imagen_procesada, etiqueta, (x1, y1-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Dibujar detecciones de defectos
            if "detecciones_defectos" in resultados:
                for deteccion in resultados["detecciones_defectos"]:
                    bbox = deteccion.get("bbox", {})
                    x1, y1 = bbox.get("x1", 0), bbox.get("y1", 0)
                    x2, y2 = bbox.get("x2", 0), bbox.get("y2", 0)
                    
                    # Dibujar rectángulo rojo para defectos
                    cv2.rectangle(imagen_procesada, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    
                    # Dibujar etiqueta
                    etiqueta = f"{deteccion.get('clase', 'Defecto')} ({deteccion.get('confianza', 0):.2f})"
                    cv2.putText(imagen_procesada, etiqueta, (x1, y1-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            # Dibujar resultado de clasificación
            if "clasificacion" in resultados:
                clasificacion = resultados["clasificacion"]
                clase = clasificacion.get("clase", "Desconocido")
                confianza = clasificacion.get("confianza", 0.0)
                
                # Color según resultado
                color = (0, 255, 0) if clase == "Aceptado" else (0, 0, 255)
                
                # Dibujar texto de clasificación
                texto = f"{clase} ({confianza:.2f})"
                cv2.putText(imagen_procesada, texto, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            
            return imagen_procesada
            
        except Exception as e:
            logger.error(f"Error creando imagen procesada: {e}")
            return imagen
    
    def _guardar_resultados_clasificacion(self, analisis_db: AnalisisCople, resultados: Dict[str, Any]):
        """Guarda los resultados de clasificación"""
        if "clasificacion" not in resultados:
            return
        
        clasificacion = resultados["clasificacion"]
        
        ResultadoClasificacion.objects.create(
            analisis=analisis_db,
            clase_predicha=clasificacion.get("clase", ""),
            confianza=clasificacion.get("confianza", 0.0),
            tiempo_inferencia_ms=clasificacion.get("tiempo_inferencia_ms", 0.0)
        )
    
    def _guardar_detecciones_piezas(self, analisis_db: AnalisisCople, resultados: Dict[str, Any]):
        """Guarda las detecciones de piezas"""
        if "detecciones_piezas" not in resultados:
            return
        
        for deteccion in resultados["detecciones_piezas"]:
            bbox = deteccion.get("bbox", {})
            centroide = deteccion.get("centroide", {})
            
            DeteccionPieza.objects.create(
                analisis=analisis_db,
                clase=deteccion.get("clase", ""),
                confianza=deteccion.get("confianza", 0.0),
                bbox_x1=bbox.get("x1", 0),
                bbox_y1=bbox.get("y1", 0),
                bbox_x2=bbox.get("x2", 0),
                bbox_y2=bbox.get("y2", 0),
                centroide_x=centroide.get("x", 0),
                centroide_y=centroide.get("y", 0),
                area=deteccion.get("area", 0)
            )
    
    def _guardar_detecciones_defectos(self, analisis_db: AnalisisCople, resultados: Dict[str, Any]):
        """Guarda las detecciones de defectos"""
        if "detecciones_defectos" not in resultados:
            return
        
        for deteccion in resultados["detecciones_defectos"]:
            bbox = deteccion.get("bbox", {})
            centroide = deteccion.get("centroide", {})
            
            DeteccionDefecto.objects.create(
                analisis=analisis_db,
                clase=deteccion.get("clase", ""),
                confianza=deteccion.get("confianza", 0.0),
                bbox_x1=bbox.get("x1", 0),
                bbox_y1=bbox.get("y1", 0),
                bbox_x2=bbox.get("x2", 0),
                bbox_y2=bbox.get("y2", 0),
                centroide_x=centroide.get("x", 0),
                centroide_y=centroide.get("y", 0),
                area=deteccion.get("area", 0)
            )
    
    def obtener_estadisticas_sistema(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del sistema de análisis
        
        Returns:
            Dict con estadísticas del sistema
        """
        try:
            if not self.inicializado:
                return {"error": "Sistema no inicializado"}
            
            # Obtener estadísticas de la base de datos
            total_analisis = AnalisisCople.objects.count()
            analisis_exitosos = AnalisisCople.objects.filter(estado='completado').count()
            analisis_con_error = AnalisisCople.objects.filter(estado='error').count()
            
            # Obtener estadísticas del sistema real (simplificado)
            estadisticas_camara = {
                "inicializado": self.inicializado,
                "usando_webcam": self.usando_webcam,
                "configuracion_activa": self.configuracion_activa.nombre if self.configuracion_activa else "N/A"
            }
            
            return {
                "sistema_integrado": {
                    "version": "1.0.0-real",
                    "estado": "funcionando",
                    "modo": "real",
                    "camera_type": "webcam"
                },
                "base_datos": {
                    "total_analisis": total_analisis,
                    "analisis_exitosos": analisis_exitosos,
                    "analisis_con_error": analisis_con_error,
                    "tasa_exito": (analisis_exitosos / total_analisis * 100) if total_analisis > 0 else 0
                },
                "configuracion_activa": {
                    "nombre": self.configuracion_activa.nombre if self.configuracion_activa else None,
                    "umbral_confianza": self.configuracion_activa.umbral_confianza if self.configuracion_activa else None,
                    "configuracion_robustez": self.configuracion_activa.configuracion_robustez if self.configuracion_activa else None
                },
                "estadisticas_camara": estadisticas_camara
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {"error": str(e)}
    
    def liberar_sistema(self):
        """Libera los recursos del sistema de análisis"""
        try:
            if self.sistema_analisis:
                self.sistema_analisis.liberar_sistema()
            
            self.inicializado = False
            logger.info("Sistema de análisis REAL liberado")
            
        except Exception as e:
            logger.error(f"Error liberando sistema REAL: {e}")


# Instancia global del servicio real
servicio_analisis_real = ServicioAnalisisCoplesReal()
