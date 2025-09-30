# analisis_coples/services.py

"""
Servicios para el sistema de análisis de coples integrado con Django
"""

import os
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

# Agregar el path de los módulos del sistema de análisis
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Importar el sistema de análisis existente
from modules.analysis_system import SistemaAnalisisIntegrado
from analisis_config import GlobalConfig, FileConfig
from utils import guardar_imagen_clasificacion

# Importar modelos Django
from .models import ConfiguracionSistema, AnalisisCople
from .resultados_models import (
    ResultadoClasificacion,
    DeteccionPieza,
    DeteccionDefecto,
    SegmentacionDefecto,
    SegmentacionPieza
)

logger = logging.getLogger(__name__)


class ServicioAnalisisCoples:
    """
    Servicio Django que integra el sistema de análisis de coples
    """
    
    def __init__(self):
        self.sistema_analisis = None
        self.inicializado = False
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
            
            # Crear sistema de análisis
            self.sistema_analisis = SistemaAnalisisIntegrado()
            
            # Aplicar configuración
            self._aplicar_configuracion()
            
            # Inicializar sistema
            if not self.sistema_analisis.inicializar():
                logger.error("Error inicializando sistema de análisis")
                return False
            
            self.inicializado = True
            logger.info(f"Sistema de análisis inicializado con configuración: {self.configuracion_activa.nombre}")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando sistema: {e}")
            return False
    
    def _aplicar_configuracion(self):
        """Aplica la configuración activa al sistema de análisis"""
        if not self.configuracion_activa or not self.sistema_analisis:
            return
        
        # Aplicar configuración de robustez
        self.sistema_analisis.aplicar_configuracion_robustez(
            self.configuracion_activa.configuracion_robustez
        )
        
        # Aplicar umbrales personalizados si es necesario
        if hasattr(self.sistema_analisis, 'detector_piezas') and self.sistema_analisis.detector_piezas:
            self.sistema_analisis.detector_piezas.confianza_min = self.configuracion_activa.umbral_confianza
            self.sistema_analisis.detector_piezas.decoder.iou_threshold = self.configuracion_activa.umbral_iou
        
        if hasattr(self.sistema_analisis, 'detector_defectos') and self.sistema_analisis.detector_defectos:
            self.sistema_analisis.detector_defectos.confianza_min = self.configuracion_activa.umbral_confianza
            self.sistema_analisis.detector_defectos.decoder.iou_threshold = self.configuracion_activa.umbral_iou
    
    def realizar_analisis_completo(self, usuario=None) -> Dict[str, Any]:
        """
        Realiza un análisis completo de cople
        
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
            
            # Crear registro de análisis en la base de datos
            analisis_db = AnalisisCople.objects.create(
                id_analisis=id_analisis,
                timestamp_captura=timezone.now(),
                tipo_analisis='completo',
                estado='procesando',
                configuracion=self.configuracion_activa,
                usuario=usuario,
                archivo_imagen="",  # Se actualizará después
                archivo_json="",    # Se actualizará después
                resolucion_ancho=640,  # Valores por defecto
                resolucion_alto=640,
                resolucion_canales=3,
                tiempo_captura_ms=0.0,
                tiempo_clasificacion_ms=0.0,
                tiempo_deteccion_piezas_ms=0.0,
                tiempo_deteccion_defectos_ms=0.0,
                tiempo_segmentacion_defectos_ms=0.0,
                tiempo_segmentacion_piezas_ms=0.0,
                tiempo_total_ms=0.0,
                metadatos_json={}
            )
            
            # Realizar análisis con el sistema integrado
            resultados = self.sistema_analisis.analisis_completo()
            
            if "error" in resultados:
                # Actualizar estado de error
                analisis_db.estado = 'error'
                analisis_db.mensaje_error = resultados["error"]
                analisis_db.save()
                return resultados
            
            # Procesar resultados y guardar en base de datos
            self._procesar_resultados_analisis(analisis_db, resultados)
            
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
        Realiza solo clasificación de cople
        
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
            
            # Crear registro de análisis en la base de datos
            analisis_db = AnalisisCople.objects.create(
                id_analisis=id_analisis,
                timestamp_captura=timezone.now(),
                tipo_analisis='clasificacion',
                estado='procesando',
                configuracion=self.configuracion_activa,
                usuario=usuario,
                archivo_imagen="",
                archivo_json="",
                resolucion_ancho=640,
                resolucion_alto=640,
                resolucion_canales=3,
                tiempo_captura_ms=0.0,
                tiempo_clasificacion_ms=0.0,
                tiempo_deteccion_piezas_ms=0.0,
                tiempo_deteccion_defectos_ms=0.0,
                tiempo_segmentacion_defectos_ms=0.0,
                tiempo_segmentacion_piezas_ms=0.0,
                tiempo_total_ms=0.0,
                metadatos_json={}
            )
            
            # Realizar análisis de clasificación
            resultados = self.sistema_analisis.solo_clasificacion()
            
            if "error" in resultados:
                analisis_db.estado = 'error'
                analisis_db.mensaje_error = resultados["error"]
                analisis_db.save()
                return resultados
            
            # Procesar resultados
            self._procesar_resultados_analisis(analisis_db, resultados)
            
            return {
                "id_analisis": id_analisis,
                "estado": "completado",
                "resultados": resultados
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de clasificación: {e}")
            return {"error": str(e)}
    
    def _procesar_resultados_analisis(self, analisis_db: AnalisisCople, resultados: Dict[str, Any]):
        """
        Procesa los resultados del análisis y los guarda en la base de datos
        
        Args:
            analisis_db: Instancia del modelo AnalisisCople
            resultados: Resultados del análisis del sistema integrado
        """
        try:
            # Actualizar información básica
            if "frame" in resultados:
                frame = resultados["frame"]
                analisis_db.resolucion_ancho = frame.shape[1]
                analisis_db.resolucion_alto = frame.shape[0]
                analisis_db.resolucion_canales = frame.shape[2] if len(frame.shape) > 2 else 1
            
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
            
            # Guardar metadatos JSON completos
            analisis_db.metadatos_json = resultados
            
            # Guardar archivos si están disponibles
            if "frame" in resultados:
                self._guardar_archivos_analisis(analisis_db, resultados)
            
            # Procesar resultados específicos
            self._guardar_resultados_clasificacion(analisis_db, resultados)
            self._guardar_detecciones_piezas(analisis_db, resultados)
            self._guardar_detecciones_defectos(analisis_db, resultados)
            self._guardar_segmentaciones_defectos(analisis_db, resultados)
            self._guardar_segmentaciones_piezas(analisis_db, resultados)
            
            # Marcar como completado
            analisis_db.estado = 'completado'
            analisis_db.save()
            
        except Exception as e:
            logger.error(f"Error procesando resultados: {e}")
            analisis_db.estado = 'error'
            analisis_db.mensaje_error = str(e)
            analisis_db.save()
    
    def _guardar_archivos_analisis(self, analisis_db: AnalisisCople, resultados: Dict[str, Any]):
        """Guarda los archivos de imagen y JSON del análisis"""
        try:
            # Generar nombres de archivo
            timestamp = analisis_db.timestamp_captura.strftime("%Y%m%d_%H%M%S")
            nombre_base = f"{analisis_db.tipo_analisis}_{timestamp}_{analisis_db.id_analisis}"
            
            archivo_imagen = f"{nombre_base}.jpg"
            archivo_json = f"{nombre_base}.json"
            
            # Actualizar nombres de archivo
            analisis_db.archivo_imagen = archivo_imagen
            analisis_db.archivo_json = archivo_json
            
        except Exception as e:
            logger.error(f"Error guardando archivos: {e}")
    
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
    
    def _guardar_segmentaciones_defectos(self, analisis_db: AnalisisCople, resultados: Dict[str, Any]):
        """Guarda las segmentaciones de defectos"""
        if "segmentaciones_defectos" not in resultados:
            return
        
        for segmentacion in resultados["segmentaciones_defectos"]:
            bbox = segmentacion.get("bbox", {})
            centroide = segmentacion.get("centroide", {})
            
            SegmentacionDefecto.objects.create(
                analisis=analisis_db,
                clase=segmentacion.get("clase", ""),
                confianza=segmentacion.get("confianza", 0.0),
                bbox_x1=bbox.get("x1", 0),
                bbox_y1=bbox.get("y1", 0),
                bbox_x2=bbox.get("x2", 0),
                bbox_y2=bbox.get("y2", 0),
                centroide_x=centroide.get("x", 0),
                centroide_y=centroide.get("y", 0),
                area_mascara=segmentacion.get("area", 0),
                coeficientes_mascara=segmentacion.get("coeficientes_mascara", [])
            )
    
    def _guardar_segmentaciones_piezas(self, analisis_db: AnalisisCople, resultados: Dict[str, Any]):
        """Guarda las segmentaciones de piezas"""
        if "segmentaciones_piezas" not in resultados:
            return
        
        for segmentacion in resultados["segmentaciones_piezas"]:
            bbox = segmentacion.get("bbox", {})
            centroide = segmentacion.get("centroide", {})
            
            SegmentacionPieza.objects.create(
                analisis=analisis_db,
                clase=segmentacion.get("clase", ""),
                confianza=segmentacion.get("confianza", 0.0),
                bbox_x1=bbox.get("x1", 0),
                bbox_y1=bbox.get("y1", 0),
                bbox_x2=bbox.get("x2", 0),
                bbox_y2=bbox.get("y2", 0),
                centroide_x=centroide.get("x", 0),
                centroide_y=centroide.get("y", 0),
                area_mascara=segmentacion.get("area", 0),
                ancho_mascara=segmentacion.get("ancho_mascara", 0),
                alto_mascara=segmentacion.get("alto_mascara", 0),
                coeficientes_mascara=segmentacion.get("coeficientes_mascara", [])
            )
    
    def obtener_estadisticas_sistema(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del sistema de análisis
        
        Returns:
            Dict con estadísticas del sistema
        """
        try:
            if not self.inicializado or not self.sistema_analisis:
                return {"error": "Sistema no inicializado"}
            
            # Obtener estadísticas del sistema integrado
            stats_sistema = self.sistema_analisis.obtener_estadisticas()
            
            # Obtener estadísticas de la base de datos
            total_analisis = AnalisisCople.objects.count()
            analisis_exitosos = AnalisisCople.objects.filter(estado='completado').count()
            analisis_con_error = AnalisisCople.objects.filter(estado='error').count()
            
            return {
                "sistema_integrado": stats_sistema,
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
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {"error": str(e)}
    
    def liberar_sistema(self):
        """Libera los recursos del sistema de análisis"""
        try:
            if self.sistema_analisis:
                self.sistema_analisis.liberar()
                self.sistema_analisis = None
            
            self.inicializado = False
            logger.info("Sistema de análisis liberado")
            
        except Exception as e:
            logger.error(f"Error liberando sistema: {e}")


# Instancia global del servicio
servicio_analisis = ServicioAnalisisCoples()
