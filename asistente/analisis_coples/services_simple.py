# analisis_coples/services_simple.py

"""
Servicio simplificado para el sistema de análisis de coples integrado con Django
Versión que funciona sin dependencias de cámara GigE
"""

import os
import sys
import time
import uuid
import logging
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

logger = logging.getLogger(__name__)


class ServicioAnalisisCoplesSimple:
    """
    Servicio Django simplificado que simula el sistema de análisis de coples
    Versión que funciona sin dependencias de cámara GigE
    """
    
    def __init__(self):
        self.inicializado = False
        self.configuracion_activa = None
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
            
            self.inicializado = True
            logger.info(f"Sistema de análisis inicializado con configuración: {self.configuracion_activa.nombre}")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando sistema: {e}")
            return False
    
    def realizar_analisis_completo(self, usuario=None) -> Dict[str, Any]:
        """
        Simula un análisis completo de cople
        
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
                archivo_imagen=f"simulacion_{id_analisis}.jpg",
                archivo_json=f"simulacion_{id_analisis}.json",
                resolucion_ancho=640,
                resolucion_alto=640,
                resolucion_canales=3,
                tiempo_captura_ms=50.0,
                tiempo_clasificacion_ms=120.0,
                tiempo_deteccion_piezas_ms=200.0,
                tiempo_deteccion_defectos_ms=180.0,
                tiempo_segmentacion_defectos_ms=300.0,
                tiempo_segmentacion_piezas_ms=280.0,
                tiempo_total_ms=1130.0,
                metadatos_json={}
            )
            
            # Simular análisis completo
            resultados = self._simular_analisis_completo()
            
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
        Simula solo clasificación de cople
        
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
                archivo_imagen=f"simulacion_{id_analisis}.jpg",
                archivo_json=f"simulacion_{id_analisis}.json",
                resolucion_ancho=640,
                resolucion_alto=640,
                resolucion_canales=3,
                tiempo_captura_ms=50.0,
                tiempo_clasificacion_ms=120.0,
                tiempo_deteccion_piezas_ms=0.0,
                tiempo_deteccion_defectos_ms=0.0,
                tiempo_segmentacion_defectos_ms=0.0,
                tiempo_segmentacion_piezas_ms=0.0,
                tiempo_total_ms=170.0,
                metadatos_json={}
            )
            
            # Simular análisis de clasificación
            resultados = self._simular_analisis_clasificacion()
            
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
    
    def _simular_analisis_completo(self) -> Dict[str, Any]:
        """Simula un análisis completo"""
        import random
        
        # Simular clasificación
        clase = random.choice(['Aceptado', 'Rechazado'])
        confianza = random.uniform(0.7, 0.95)
        
        # Simular detecciones de piezas
        detecciones_piezas = []
        for i in range(random.randint(1, 3)):
            x1 = random.randint(50, 200)
            y1 = random.randint(50, 200)
            x2 = x1 + random.randint(80, 150)
            y2 = y1 + random.randint(80, 150)
            detecciones_piezas.append({
                "clase": f"Pieza_{i+1}",
                "confianza": random.uniform(0.8, 0.95),
                "bbox": {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2
                },
                "centroide": {
                    "x": (x1 + x2) // 2,
                    "y": (y1 + y2) // 2
                },
                "area": (x2 - x1) * (y2 - y1)
            })
        
        # Simular detecciones de defectos
        detecciones_defectos = []
        for i in range(random.randint(0, 2)):
            x1 = random.randint(100, 300)
            y1 = random.randint(100, 300)
            x2 = x1 + random.randint(40, 80)
            y2 = y1 + random.randint(40, 80)
            detecciones_defectos.append({
                "clase": f"Defecto_{i+1}",
                "confianza": random.uniform(0.6, 0.9),
                "bbox": {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2
                },
                "centroide": {
                    "x": (x1 + x2) // 2,
                    "y": (y1 + y2) // 2
                },
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
                "version": "1.0.0",
                "configuracion": self.configuracion_activa.nombre if self.configuracion_activa else "default"
            }
        }
    
    def _simular_analisis_clasificacion(self) -> Dict[str, Any]:
        """Simula un análisis de clasificación"""
        import random
        
        clase = random.choice(['Aceptado', 'Rechazado'])
        confianza = random.uniform(0.7, 0.95)
        
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
                "version": "1.0.0",
                "configuracion": self.configuracion_activa.nombre if self.configuracion_activa else "default"
            }
        }
    
    def _procesar_resultados_analisis(self, analisis_db: AnalisisCople, resultados: Dict[str, Any]):
        """
        Procesa los resultados del análisis y los guarda en la base de datos
        
        Args:
            analisis_db: Instancia del modelo AnalisisCople
            resultados: Resultados del análisis simulado
        """
        try:
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
            
            # Procesar resultados específicos
            self._guardar_resultados_clasificacion(analisis_db, resultados)
            self._guardar_detecciones_piezas(analisis_db, resultados)
            self._guardar_detecciones_defectos(analisis_db, resultados)
            
            # Marcar como completado
            analisis_db.estado = 'completado'
            analisis_db.save()
            
        except Exception as e:
            logger.error(f"Error procesando resultados: {e}")
            analisis_db.estado = 'error'
            analisis_db.mensaje_error = str(e)
            analisis_db.save()
    
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
            
            return {
                "sistema_integrado": {
                    "version": "1.0.0-simulado",
                    "estado": "funcionando",
                    "modo": "simulacion"
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
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {"error": str(e)}
    
    def liberar_sistema(self):
        """Libera los recursos del sistema de análisis"""
        try:
            self.inicializado = False
            logger.info("Sistema de análisis liberado")
            
        except Exception as e:
            logger.error(f"Error liberando sistema: {e}")


# Instancia global del servicio simplificado
servicio_analisis = ServicioAnalisisCoplesSimple()
