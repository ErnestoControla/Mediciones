"""
Servicio de análisis de segmentación con mediciones.

Flujo simplificado:
1. Capturar imagen desde CameraService
2. Ejecutar segmentación (piezas o defectos)
3. Calcular mediciones geométricas
4. Generar imagen procesada con máscaras
5. Guardar en BD
"""

import logging
import time
import uuid
import os
import cv2
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.base import ContentFile

from ..models import ConfiguracionSistema, AnalisisCople
from ..resultados_models import SegmentacionPieza, SegmentacionDefecto
from ..modules.measurements import get_measurement_service
from .camera_service import get_camera_service

logger = logging.getLogger(__name__)

User = get_user_model()


class SegmentationAnalysisService:
    """
    Servicio simplificado para análisis de segmentación con mediciones.
    
    Usa la cámara del CameraService y ejecuta solo segmentación + mediciones.
    """
    
    def __init__(self):
        """Inicializa el servicio"""
        self.segmentador_piezas = None
        self.segmentador_defectos = None
        self.measurement_service = get_measurement_service()
        self.camera_service = get_camera_service()
    
    def _inicializar_segmentador(self, tipo: str):
        """
        Inicializa un segmentador específico y libera el otro para ahorrar RAM.
        Solo mantiene un modelo ONNX cargado a la vez.
        
        Args:
            tipo: 'piezas' o 'defectos'
        """
        import sys
        import os
        
        # Agregar path
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Importar segmentadores
        from modules.segmentation.segmentation_piezas_engine import SegmentadorPiezasCoples
        from modules.segmentation.segmentation_defectos_engine import SegmentadorDefectosCoples
        
        if tipo == 'piezas':
            # Liberar segmentador de defectos si existe
            if self.segmentador_defectos is not None:
                logger.info("🔄 Liberando segmentador de defectos para cargar piezas...")
                if hasattr(self.segmentador_defectos, 'liberar'):
                    self.segmentador_defectos.liberar()
                self.segmentador_defectos = None
            
            # Inicializar segmentador de piezas si no existe
            if self.segmentador_piezas is None:
                logger.info("🎯 Inicializando segmentador de piezas...")
                self.segmentador_piezas = SegmentadorPiezasCoples()
                if not self.segmentador_piezas.stats['inicializado']:
                    logger.error("❌ Error inicializando segmentador de piezas")
                    return False
                logger.info("✅ Segmentador de piezas listo")
        
        elif tipo == 'defectos':
            # Liberar segmentador de piezas si existe
            if self.segmentador_piezas is not None:
                logger.info("🔄 Liberando segmentador de piezas para cargar defectos...")
                if hasattr(self.segmentador_piezas, 'liberar'):
                    self.segmentador_piezas.liberar()
                self.segmentador_piezas = None
            
            # Inicializar segmentador de defectos si no existe
            if self.segmentador_defectos is None:
                logger.info("🎯 Inicializando segmentador de defectos...")
                self.segmentador_defectos = SegmentadorDefectosCoples()
                if not self.segmentador_defectos._inicializar_modelo():
                    logger.error("❌ Error inicializando segmentador de defectos")
                    return False
                logger.info("✅ Segmentador de defectos listo")
        
        return True
    
    def analizar_imagen(
        self,
        tipo_analisis: str,
        usuario: Optional[User] = None,
        configuracion_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analiza una imagen capturando desde la cámara activa.
        
        Args:
            tipo_analisis: 'medicion_piezas' o 'medicion_defectos'
            usuario: Usuario que ejecuta el análisis
            configuracion_id: ID de configuración (opcional)
            
        Returns:
            Dict con resultado del análisis e ID
        """
        try:
            # 1. Verificar que hay cámara activa
            estado_camara = self.camera_service.obtener_estado()
            if not estado_camara['activa']:
                return {
                    'error': 'No hay cámara inicializada. Inicializa la cámara primero.'
                }
            
            # 2. Inicializar el segmentador correcto según el tipo
            tipo_segmentador = 'piezas' if tipo_analisis == 'medicion_piezas' else 'defectos'
            if not self._inicializar_segmentador(tipo_segmentador):
                return {'error': f'Error inicializando segmentador de {tipo_segmentador}'}
            
            # 3. Obtener configuración
            if configuracion_id:
                config = ConfiguracionSistema.objects.get(id=configuracion_id)
            else:
                config = ConfiguracionSistema.objects.filter(activa=True).first()
            
            if not config:
                return {'error': 'No hay configuración activa'}
            
            # Configurar factor de conversión si existe
            if config.factor_conversion_px_mm:
                self.measurement_service.set_conversion_factor(config.factor_conversion_px_mm)
            
            # 4. Capturar imagen desde cámara activa
            logger.info(f"📸 Capturando imagen desde {'GigE' if not estado_camara.get('usando_webcam') else 'Webcam'}...")
            exito, imagen = self.camera_service.capturar_imagen()
            
            if not exito or imagen is None:
                return {'error': 'Error capturando imagen de la cámara'}
            
            logger.info(f"✅ Imagen capturada: {imagen.shape}")
            
            # 5. Generar ID único
            id_analisis = f"analisis_{uuid.uuid4().hex[:8]}_{int(time.time())}"
            
            # 6. Crear registro en BD
            analisis_db = AnalisisCople.objects.create(
                id_analisis=id_analisis,
                timestamp_captura=timezone.now(),
                tipo_analisis=tipo_analisis,
                estado='procesando',
                configuracion=config,
                usuario=usuario,
                archivo_imagen="",  # Se actualizará
                archivo_json="",
                resolucion_ancho=imagen.shape[1],
                resolucion_alto=imagen.shape[0],
                resolucion_canales=imagen.shape[2] if len(imagen.shape) > 2 else 1,
                tiempo_captura_ms=0.0,
                tiempo_segmentacion_defectos_ms=0.0,
                tiempo_segmentacion_piezas_ms=0.0,
                tiempo_total_ms=0.0,
                metadatos_json={}
            )
            
            logger.info(f"📝 Registro creado: {id_analisis}")
            
            # 7. Ejecutar segmentación según tipo
            inicio_seg = time.time()
            
            if tipo_analisis == 'medicion_piezas':
                try:
                    logger.info("🔩 Ejecutando segmentación de piezas...")
                    logger.info(f"   Imagen shape: {imagen.shape}, dtype: {imagen.dtype}")
                    logger.info(f"   Segmentador: {type(self.segmentador_piezas)}")
                    
                    # Ejecutar segmentación
                    segmentaciones = self.segmentador_piezas.segmentar(imagen)
                    
                    logger.info(f"✅ Segmentación completada: {len(segmentaciones) if segmentaciones else 0} resultados")
                    
                    tiempo_seg = (time.time() - inicio_seg) * 1000
                    analisis_db.tiempo_segmentacion_piezas_ms = tiempo_seg
                    
                    # Guardar segmentaciones con mediciones
                    self._guardar_segmentaciones_piezas(analisis_db, segmentaciones, config)
                    
                except Exception as e:
                    logger.error(f"❌ Error en segmentación de piezas: {e}", exc_info=True)
                    analisis_db.estado = 'error'
                    analisis_db.save()
                    return {'error': f'Error en segmentación: {str(e)}'}
                
            elif tipo_analisis == 'medicion_defectos':
                logger.info("⚠️  Ejecutando segmentación de defectos...")
                segmentaciones = self.segmentador_defectos.segmentar(imagen)
                tiempo_seg = (time.time() - inicio_seg) * 1000
                analisis_db.tiempo_segmentacion_defectos_ms = tiempo_seg
                
                # Guardar segmentaciones con mediciones
                self._guardar_segmentaciones_defectos(analisis_db, segmentaciones, config)
            
            # 8. Generar y guardar imagen procesada con máscaras
            logger.info("🖼️  Generando imagen procesada...")
            imagen_procesada = self._generar_imagen_procesada(imagen, segmentaciones, tipo_analisis)
            
            if imagen_procesada is not None:
                try:
                    # Guardar imagen en media
                    _, buffer = cv2.imencode('.jpg', imagen_procesada)
                    imagen_bytes = buffer.tobytes()
                    
                    # Nombre del archivo
                    nombre_archivo = f"analisis_{id_analisis}.jpg"
                    
                    # Guardar en el campo archivo_imagen
                    analisis_db.archivo_imagen.save(
                        nombre_archivo,
                        ContentFile(imagen_bytes),
                        save=False
                    )
                    logger.info(f"💾 Imagen procesada guardada: {nombre_archivo}")
                    
                except Exception as e:
                    logger.error(f"❌ Error guardando imagen procesada: {e}", exc_info=True)
            else:
                logger.warning("⚠️ No se pudo generar imagen procesada")
            
            # 9. Actualizar registro
            analisis_db.tiempo_total_ms = (time.time() - inicio_seg) * 1000
            analisis_db.estado = 'completado'
            analisis_db.save()
            
            logger.info(f"✅ Análisis completado: {id_analisis}")
            logger.info(f"   Segmentaciones: {len(segmentaciones) if segmentaciones else 0}")
            logger.info(f"   Tiempo: {analisis_db.tiempo_total_ms:.0f}ms")
            
            return {
                'id_analisis': id_analisis,
                'analisis_id': analisis_db.id,
                'estado': 'completado',
                'segmentaciones_count': len(segmentaciones) if segmentaciones else 0,
                'tiempo_total_ms': analisis_db.tiempo_total_ms
            }
            
        except Exception as e:
            logger.error(f"❌ Error en análisis: {e}", exc_info=True)
            return {'error': str(e)}
    
    def _guardar_segmentaciones_piezas(
        self,
        analisis_db: AnalisisCople,
        segmentaciones: list,
        config: ConfiguracionSistema
    ):
        """Guarda segmentaciones de piezas con mediciones"""
        import numpy as np
        
        if not segmentaciones:
            logger.warning("No hay segmentaciones de piezas para guardar")
            return
        
        logger.info(f"📐 Guardando {len(segmentaciones)} segmentaciones de piezas...")
        
        for idx, seg in enumerate(segmentaciones):
            # Extraer datos
            bbox = seg.get('bbox', {})
            mascara = seg.get('mascara')
            
            # Calcular mediciones si hay máscara
            mediciones = {}
            if mascara is not None:
                if not isinstance(mascara, np.ndarray):
                    mascara = np.array(mascara, dtype=np.uint8)
                
                mediciones = self.measurement_service.calcular_mediciones_completas(
                    mascara,
                    convertir_a_mm=bool(config.factor_conversion_px_mm)
                )
                logger.info(f"  📏 Pieza {idx}: {mediciones.get('ancho_bbox_px')}x{mediciones.get('alto_bbox_px')}px, área={mediciones.get('area_mascara_px')}px²")
            
            # Guardar en BD
            SegmentacionPieza.objects.create(
                analisis=analisis_db,
                clase=seg.get('clase', 'Cople'),
                confianza=seg.get('confianza', 0.0),
                bbox_x1=bbox.get('x1', 0),
                bbox_y1=bbox.get('y1', 0),
                bbox_x2=bbox.get('x2', 0),
                bbox_y2=bbox.get('y2', 0),
                ancho_bbox_px=mediciones.get('ancho_bbox_px', 0.0),
                alto_bbox_px=mediciones.get('alto_bbox_px', 0.0),
                centroide_x=seg.get('centroide', {}).get('x', 0),
                centroide_y=seg.get('centroide', {}).get('y', 0),
                area_mascara_px=int(mediciones.get('area_mascara_px', 0)),
                ancho_mascara_px=mediciones.get('ancho_bbox_px', 0.0),
                alto_mascara_px=mediciones.get('alto_bbox_px', 0.0),
                perimetro_mascara_px=mediciones.get('perimetro_mascara_px', 0.0),
                excentricidad=mediciones.get('excentricidad', 0.0),
                orientacion_grados=mediciones.get('orientacion_grados', 0.0),
                ancho_bbox_mm=mediciones.get('ancho_bbox_mm'),
                alto_bbox_mm=mediciones.get('alto_bbox_mm'),
                ancho_mascara_mm=mediciones.get('ancho_bbox_mm'),
                alto_mascara_mm=mediciones.get('alto_bbox_mm'),
                perimetro_mascara_mm=mediciones.get('perimetro_mascara_mm'),
                area_mascara_mm=mediciones.get('area_mascara_mm'),
                coeficientes_mascara=seg.get('coeficientes_mascara', [])
            )
        
        logger.info(f"✅ {len(segmentaciones)} segmentaciones de piezas guardadas")
    
    def _guardar_segmentaciones_defectos(
        self,
        analisis_db: AnalisisCople,
        segmentaciones: list,
        config: ConfiguracionSistema
    ):
        """Guarda segmentaciones de defectos con mediciones"""
        import numpy as np
        
        if not segmentaciones:
            logger.warning("No hay segmentaciones de defectos para guardar")
            return
        
        logger.info(f"📐 Guardando {len(segmentaciones)} segmentaciones de defectos...")
        
        for idx, seg in enumerate(segmentaciones):
            # Extraer datos
            bbox = seg.get('bbox', {})
            mascara = seg.get('mascara')
            
            # Calcular mediciones si hay máscara
            mediciones = {}
            if mascara is not None:
                if not isinstance(mascara, np.ndarray):
                    mascara = np.array(mascara, dtype=np.uint8)
                
                mediciones = self.measurement_service.calcular_mediciones_completas(
                    mascara,
                    convertir_a_mm=bool(config.factor_conversion_px_mm)
                )
                logger.info(f"  📏 Defecto {idx}: {mediciones.get('ancho_bbox_px')}x{mediciones.get('alto_bbox_px')}px, área={mediciones.get('area_mascara_px')}px²")
            
            # Guardar en BD
            SegmentacionDefecto.objects.create(
                analisis=analisis_db,
                clase=seg.get('clase', 'Defecto'),
                confianza=seg.get('confianza', 0.0),
                bbox_x1=bbox.get('x1', 0),
                bbox_y1=bbox.get('y1', 0),
                bbox_x2=bbox.get('x2', 0),
                bbox_y2=bbox.get('y2', 0),
                ancho_bbox_px=mediciones.get('ancho_bbox_px', 0.0),
                alto_bbox_px=mediciones.get('alto_bbox_px', 0.0),
                centroide_x=seg.get('centroide', {}).get('x', 0),
                centroide_y=seg.get('centroide', {}).get('y', 0),
                area_mascara_px=int(mediciones.get('area_mascara_px', 0)),
                ancho_mascara_px=mediciones.get('ancho_bbox_px', 0.0),
                alto_mascara_px=mediciones.get('alto_bbox_px', 0.0),
                perimetro_mascara_px=mediciones.get('perimetro_mascara_px', 0.0),
                excentricidad=mediciones.get('excentricidad', 0.0),
                orientacion_grados=mediciones.get('orientacion_grados', 0.0),
                ancho_bbox_mm=mediciones.get('ancho_bbox_mm'),
                alto_bbox_mm=mediciones.get('alto_bbox_mm'),
                ancho_mascara_mm=mediciones.get('ancho_bbox_mm'),
                alto_mascara_mm=mediciones.get('alto_bbox_mm'),
                perimetro_mascara_mm=mediciones.get('perimetro_mascara_mm'),
                area_mascara_mm=mediciones.get('area_mascara_mm'),
                coeficientes_mascara=seg.get('coeficientes_mascara', [])
            )
        
        logger.info(f"✅ {len(segmentaciones)} segmentaciones de defectos guardadas")
    
    def _generar_imagen_procesada(
        self,
        imagen: np.ndarray,
        segmentaciones: list,
        tipo_analisis: str
    ) -> Optional[np.ndarray]:
        """
        Genera imagen procesada con máscaras dibujadas.
        
        Args:
            imagen: Imagen original
            segmentaciones: Lista de segmentaciones con máscaras
            tipo_analisis: Tipo de análisis para el color
            
        Returns:
            Imagen con máscaras dibujadas o None si falla
        """
        try:
            if not segmentaciones:
                logger.warning("No hay segmentaciones para visualizar")
                return None
            
            # Copiar imagen para no modificar la original
            imagen_vis = imagen.copy()
            
            # Definir color según tipo
            if tipo_analisis == 'medicion_piezas':
                color_base = (0, 255, 0)  # Verde para piezas
            else:
                color_base = (0, 0, 255)  # Rojo para defectos
            
            logger.info(f"🎨 Dibujando {len(segmentaciones)} máscaras en imagen...")
            
            # Dibujar cada máscara
            for idx, seg in enumerate(segmentaciones):
                mascara = seg.get('mascara')
                bbox = seg.get('bbox', {})
                
                if mascara is None:
                    continue
                
                # Convertir máscara a numpy si es necesario
                if not isinstance(mascara, np.ndarray):
                    mascara = np.array(mascara, dtype=np.float32)
                
                # Redimensionar si es necesario
                if mascara.shape != imagen.shape[:2]:
                    mascara = cv2.resize(mascara, (imagen.shape[1], imagen.shape[0]))
                
                # Binarizar máscara
                mascara_binaria = (mascara > 0.5).astype(np.uint8)
                
                # Verificar píxeles activos
                pixels_activos = np.sum(mascara_binaria)
                if pixels_activos == 0:
                    logger.warning(f"  ⚠️ Máscara {idx}: Sin píxeles activos")
                    continue
                
                logger.info(f"  ✅ Máscara {idx}: {pixels_activos} píxeles activos")
                
                # Crear overlay con transparencia
                overlay = imagen_vis.copy()
                overlay[mascara_binaria > 0] = color_base
                
                # Combinar con transparencia (alpha=0.4)
                cv2.addWeighted(overlay, 0.4, imagen_vis, 0.6, 0, imagen_vis)
                
                # Dibujar contorno de la máscara
                contornos, _ = cv2.findContours(mascara_binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(imagen_vis, contornos, -1, color_base, 2)
                
                # Dibujar bounding box si existe
                if bbox:
                    x1, y1 = int(bbox.get('x1', 0)), int(bbox.get('y1', 0))
                    x2, y2 = int(bbox.get('x2', 0)), int(bbox.get('y2', 0))
                    cv2.rectangle(imagen_vis, (x1, y1), (x2, y2), color_base, 2)
                    
                    # Agregar etiqueta
                    clase = seg.get('clase', 'Objeto')
                    confianza = seg.get('confianza', 0.0)
                    etiqueta = f"{clase}: {confianza:.2f}"
                    
                    # Fondo para el texto
                    (tw, th), _ = cv2.getTextSize(etiqueta, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.rectangle(imagen_vis, (x1, y1 - th - 10), (x1 + tw, y1), color_base, -1)
                    cv2.putText(imagen_vis, etiqueta, (x1, y1 - 5), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            logger.info(f"✅ Imagen procesada generada: {imagen_vis.shape}")
            return imagen_vis
            
        except Exception as e:
            logger.error(f"❌ Error generando imagen procesada: {e}", exc_info=True)
            return None


# Instancia singleton
_segmentation_service_instance = None

def get_segmentation_analysis_service() -> SegmentationAnalysisService:
    """Obtiene la instancia singleton del servicio"""
    global _segmentation_service_instance
    
    if _segmentation_service_instance is None:
        _segmentation_service_instance = SegmentationAnalysisService()
        logger.info("✅ SegmentationAnalysisService inicializado")
    
    return _segmentation_service_instance

