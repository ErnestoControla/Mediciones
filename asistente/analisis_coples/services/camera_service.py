"""
Servicio de control de cámara GigE Vision.

Gestiona:
- Inicialización y liberación de cámara GigE
- Preview a 5 FPS con auto-hibernación
- Estado persistente en BD (EstadoCamara)
- Carga dinámica de modelos (uno a la vez para optimizar RAM)
"""

import logging
import threading
import time
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import cv2

from django.utils import timezone
from django.core.cache import cache

from ..models import EstadoCamara
from ..modules.capture.camera_controller import CamaraTiempoOptimizada
from ..modules.capture.webcam_fallback import WebcamFallback, detectar_mejor_webcam

logger = logging.getLogger(__name__)


class CameraService:
    """
    Servicio de control de cámara GigE con preview y hibernación.
    
    Características:
    - Preview a 5 FPS optimizado para bajo consumo
    - Auto-hibernación después de 1 minuto de inactividad
    - Integración con modelo EstadoCamara (singleton)
    - Prioridad a cámara GigE, fallback a webcam
    """
    
    def __init__(self):
        """Inicializa el servicio de cámara"""
        self.camara_gige: Optional[CamaraTiempoOptimizada] = None
        self.webcam: Optional[WebcamFallback] = None
        self.usando_webcam: bool = False
        
        # Estado de preview
        self.preview_activo: bool = False
        self.preview_thread: Optional[threading.Thread] = None
        self.preview_stop_event: threading.Event = threading.Event()
        
        # Hibernación
        self.hibernacion_timer: Optional[threading.Timer] = None
        self.tiempo_hibernacion_segundos: int = 60  # 1 minuto
        
        # Frame actual del preview
        self.ultimo_frame: Optional[np.ndarray] = None
        self.ultimo_frame_timestamp: Optional[datetime] = None
        self.frame_lock: threading.Lock = threading.Lock()
        
        # Cargar estado de BD
        self._sincronizar_estado_bd()
    
    def _sincronizar_estado_bd(self) -> None:
        """Sincroniza el estado del servicio con la BD"""
        try:
            self.estado_bd = EstadoCamara.get_estado()
            logger.info(f"Estado de cámara cargado: {self.estado_bd}")
        except Exception as e:
            logger.error(f"Error cargando estado de cámara: {e}")
            self.estado_bd = None
    
    def _actualizar_estado_bd(
        self,
        activa: Optional[bool] = None,
        en_preview: Optional[bool] = None,
        hibernada: Optional[bool] = None,
        modelo_cargado: Optional[str] = None,
        frame_rate: Optional[int] = None
    ) -> None:
        """
        Actualiza el estado en la base de datos.
        
        Args:
            activa: Si la cámara está activa
            en_preview: Si está en modo preview
            hibernada: Si está hibernada
            modelo_cargado: Modelo ONNX cargado ('piezas', 'defectos', 'ninguno')
            frame_rate: FPS del preview
        """
        try:
            estado = EstadoCamara.get_estado()
            
            if activa is not None:
                estado.activa = activa
            if en_preview is not None:
                estado.en_preview = en_preview
            if hibernada is not None:
                estado.hibernada = hibernada
            if modelo_cargado is not None:
                estado.modelo_cargado = modelo_cargado
            if frame_rate is not None:
                estado.frame_rate_actual = frame_rate
            
            estado.save()
            self.estado_bd = estado
            logger.debug(f"Estado actualizado: {estado}")
            
        except Exception as e:
            logger.error(f"Error actualizando estado en BD: {e}")
    
    def inicializar_camara(self, ip_camara: str = "172.16.1.24") -> Dict[str, Any]:
        """
        Inicializa la cámara GigE o webcam como fallback.
        
        Args:
            ip_camara: Dirección IP de la cámara GigE
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            logger.info(f"Inicializando cámara GigE en {ip_camara}...")
            
            # Intentar cámara GigE primero
            self.camara_gige = CamaraTiempoOptimizada(ip=ip_camara)
            
            if self.camara_gige.configurar_camara():
                self.usando_webcam = False
                self._actualizar_estado_bd(activa=True, hibernada=False)
                
                logger.info("✅ Cámara GigE inicializada correctamente")
                return {
                    'success': True,
                    'tipo_camara': 'gige',
                    'ip': ip_camara,
                    'message': 'Cámara GigE inicializada correctamente'
                }
            else:
                logger.warning("No se pudo inicializar cámara GigE, intentando webcam...")
                
                # Fallback a webcam
                webcam_id = detectar_mejor_webcam()
                if webcam_id is not None:
                    self.webcam = WebcamFallback(webcam_id)
                    if self.webcam.inicializar():
                        self.usando_webcam = True
                        self._actualizar_estado_bd(activa=True, hibernada=False)
                        
                        logger.info(f"✅ Webcam inicializada correctamente (ID: {webcam_id})")
                        return {
                            'success': True,
                            'tipo_camara': 'webcam',
                            'webcam_id': webcam_id,
                            'message': f'Webcam inicializada (ID: {webcam_id}) - Fallback de GigE'
                        }
                
                logger.error("No se pudo inicializar ninguna cámara")
                return {
                    'success': False,
                    'error': 'No se pudo inicializar cámara GigE ni webcam'
                }
                
        except Exception as e:
            logger.error(f"Error inicializando cámara: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def liberar_camara(self) -> Dict[str, Any]:
        """
        Libera la cámara y detiene el preview.
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Detener preview si está activo
            if self.preview_activo:
                self.detener_preview()
            
            # Cancelar timer de hibernación
            if self.hibernacion_timer:
                self.hibernacion_timer.cancel()
                self.hibernacion_timer = None
            
            # Liberar cámara
            if self.camara_gige:
                self.camara_gige.liberar()
                self.camara_gige = None
            
            if self.webcam:
                self.webcam.liberar()
                self.webcam = None
            
            self.usando_webcam = False
            self._actualizar_estado_bd(
                activa=False, 
                en_preview=False, 
                hibernada=False
            )
            
            logger.info("✅ Cámara liberada correctamente")
            return {
                'success': True,
                'message': 'Cámara liberada correctamente'
            }
            
        except Exception as e:
            logger.error(f"Error liberando cámara: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def capturar_imagen(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Captura una imagen de la cámara actual.
        
        Returns:
            Tuple[bool, Optional[np.ndarray]]: (éxito, imagen)
        """
        try:
            if self.usando_webcam and self.webcam:
                imagen = self.webcam.capturar_frame()
                return (True, imagen) if imagen is not None else (False, None)
            
            elif self.camara_gige:
                imagen = self.camara_gige.capturar_frame()
                return (True, imagen) if imagen is not None else (False, None)
            
            else:
                logger.error("No hay cámara inicializada")
                return (False, None)
                
        except Exception as e:
            logger.error(f"Error capturando imagen: {e}")
            return (False, None)
    
    def iniciar_preview(self, fps: int = 5) -> Dict[str, Any]:
        """
        Inicia el preview de la cámara a FPS especificados.
        
        Args:
            fps: Cuadros por segundo (default: 5)
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            if self.preview_activo:
                return {
                    'success': False,
                    'error': 'Preview ya está activo'
                }
            
            if not (self.camara_gige or self.webcam):
                return {
                    'success': False,
                    'error': 'No hay cámara inicializada'
                }
            
            # Si es cámara GigE, iniciar captura continua
            if self.camara_gige and not self.usando_webcam:
                logger.info("🚀 Iniciando captura continua de cámara GigE...")
                if not self.camara_gige.iniciar_captura_continua():
                    logger.error("❌ Error iniciando captura continua de GigE")
                    return {
                        'success': False,
                        'error': 'Error iniciando captura continua de cámara GigE'
                    }
                logger.info("✅ Captura continua GigE iniciada")
            
            # Configurar FPS
            self.fps_preview = fps
            self.frame_interval = 1.0 / fps
            
            # Iniciar thread de preview
            self.preview_stop_event.clear()
            self.preview_thread = threading.Thread(
                target=self._preview_loop,
                daemon=True
            )
            self.preview_thread.start()
            
            self.preview_activo = True
            self._actualizar_estado_bd(en_preview=True, hibernada=False, frame_rate=fps)
            
            # Iniciar timer de hibernación
            self._programar_hibernacion()
            
            logger.info(f"✅ Preview iniciado a {fps} FPS")
            return {
                'success': True,
                'fps': fps,
                'message': f'Preview iniciado a {fps} FPS'
            }
            
        except Exception as e:
            logger.error(f"Error iniciando preview: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def detener_preview(self) -> Dict[str, Any]:
        """
        Detiene el preview de la cámara.
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            if not self.preview_activo:
                return {
                    'success': False,
                    'error': 'Preview no está activo'
                }
            
            # Señalar al thread que pare
            self.preview_stop_event.set()
            
            # Esperar a que termine el thread
            if self.preview_thread and self.preview_thread.is_alive():
                self.preview_thread.join(timeout=2.0)
            
            # Si es cámara GigE, detener captura continua
            if self.camara_gige and not self.usando_webcam:
                logger.info("🛑 Deteniendo captura continua de cámara GigE...")
                self.camara_gige.detener_captura()
                logger.info("✅ Captura continua GigE detenida")
            
            self.preview_activo = False
            self._actualizar_estado_bd(en_preview=False)
            
            logger.info("✅ Preview detenido")
            return {
                'success': True,
                'message': 'Preview detenido'
            }
            
        except Exception as e:
            logger.error(f"Error deteniendo preview: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def hibernar(self) -> Dict[str, Any]:
        """
        Hiberna la cámara (detiene preview, mantiene conexión).
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            logger.info("⏸ Hibernando cámara...")
            
            # Detener preview pero mantener cámara conectada
            if self.preview_activo:
                self.detener_preview()
            
            self._actualizar_estado_bd(hibernada=True, en_preview=False)
            
            logger.info("✅ Cámara hibernada")
            return {
                'success': True,
                'message': 'Cámara hibernada correctamente'
            }
            
        except Exception as e:
            logger.error(f"Error hibernando cámara: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def reactivar_preview(self, fps: int = 5) -> Dict[str, Any]:
        """
        Reactiva el preview desde hibernación.
        
        Args:
            fps: Cuadros por segundo
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            estado = EstadoCamara.get_estado()
            
            if not estado.hibernada:
                return self.iniciar_preview(fps)
            
            logger.info("▶ Reactivando preview desde hibernación...")
            
            # Quitar hibernación y reiniciar preview
            self._actualizar_estado_bd(hibernada=False)
            return self.iniciar_preview(fps)
            
        except Exception as e:
            logger.error(f"Error reactivando preview: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def obtener_frame_preview(self) -> Optional[bytes]:
        """
        Obtiene el último frame del preview en formato JPEG.
        
        Returns:
            bytes: Imagen JPEG encodificada o None
        """
        try:
            with self.frame_lock:
                if self.ultimo_frame is None:
                    return None
                
                # Encodificar a JPEG con calidad optimizada para preview
                _, buffer = cv2.imencode(
                    '.jpg',
                    self.ultimo_frame,
                    [cv2.IMWRITE_JPEG_QUALITY, 85]
                )
                return buffer.tobytes()
                
        except Exception as e:
            logger.error(f"Error obteniendo frame de preview: {e}")
            return None
    
    def _preview_loop(self) -> None:
        """
        Loop principal del preview (ejecuta en thread separado).
        Captura frames a la velocidad configurada.
        """
        logger.info(f"🎬 Iniciando loop de preview a {self.fps_preview} FPS...")
        
        while not self.preview_stop_event.is_set():
            try:
                inicio = time.time()
                
                # Capturar frame
                exito, frame = self.capturar_imagen()
                
                if exito and frame is not None:
                    # Guardar frame para preview
                    with self.frame_lock:
                        self.ultimo_frame = frame.copy()
                        self.ultimo_frame_timestamp = datetime.now()
                    
                    # Almacenar en cache para acceso rápido
                    cache.set('camera_preview_frame', frame, timeout=2)
                
                # Control de FPS
                tiempo_transcurrido = time.time() - inicio
                tiempo_espera = max(0, self.frame_interval - tiempo_transcurrido)
                
                if tiempo_espera > 0:
                    self.preview_stop_event.wait(timeout=tiempo_espera)
                
            except Exception as e:
                logger.error(f"Error en loop de preview: {e}")
                time.sleep(0.1)
        
        logger.info("🛑 Preview loop detenido")
    
    def _programar_hibernacion(self) -> None:
        """Programa la hibernación automática después de 1 minuto"""
        # Cancelar timer anterior si existe
        if self.hibernacion_timer:
            self.hibernacion_timer.cancel()
        
        # Programar nueva hibernación
        self.hibernacion_timer = threading.Timer(
            self.tiempo_hibernacion_segundos,
            self._ejecutar_hibernacion_automatica
        )
        self.hibernacion_timer.daemon = True
        self.hibernacion_timer.start()
        
        logger.debug(f"⏰ Hibernación programada en {self.tiempo_hibernacion_segundos}s")
    
    def _ejecutar_hibernacion_automatica(self) -> None:
        """Ejecuta la hibernación automática"""
        logger.info("⏰ Tiempo de hibernación alcanzado, hibernando cámara...")
        self.hibernar()
    
    def resetear_timer_hibernacion(self) -> None:
        """Resetea el timer de hibernación (al interactuar con la cámara)"""
        if self.preview_activo:
            self._programar_hibernacion()
            logger.debug("🔄 Timer de hibernación reseteado")
    
    def obtener_estado(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual de la cámara.
        
        Returns:
            Dict con información del estado
        """
        try:
            estado_bd = EstadoCamara.get_estado()
            
            return {
                'activa': estado_bd.activa,
                'en_preview': estado_bd.en_preview,
                'hibernada': estado_bd.hibernada,
                'modelo_cargado': estado_bd.modelo_cargado,
                'frame_rate_actual': estado_bd.frame_rate_actual,
                'ultimo_uso': estado_bd.ultimo_uso.isoformat() if estado_bd.ultimo_uso else None,
                'usando_webcam': self.usando_webcam,
                'tiene_frame': self.ultimo_frame is not None
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado: {e}")
            return {
                'error': str(e)
            }


# Instancia singleton del servicio
_camera_service_instance: Optional[CameraService] = None


def get_camera_service() -> CameraService:
    """
    Obtiene la instancia singleton del servicio de cámara.
    
    Returns:
        CameraService: Instancia del servicio
    """
    global _camera_service_instance
    
    if _camera_service_instance is None:
        _camera_service_instance = CameraService()
    
    return _camera_service_instance

