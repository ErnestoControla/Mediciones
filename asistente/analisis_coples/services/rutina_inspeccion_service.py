"""
Servicio de Rutina de Inspección Multi-Ángulo.

Flujo:
1. Iniciar rutina (crear registro en BD)
2. Capturar 6 imágenes automáticamente (cada 3 segundos)
3. Analizar cada imagen (solo defectos)
4. Generar imagen consolidada (Grid 2x3)
5. Generar reporte consolidado
6. Finalizar rutina
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

from ..models import ConfiguracionSistema, RutinaInspeccion, AnalisisCople
from .segmentation_analysis_service import get_segmentation_analysis_service

logger = logging.getLogger(__name__)

User = get_user_model()


class RutinaInspeccionService:
    """
    Servicio para ejecutar rutinas de inspección multi-ángulo.
    
    Simula un brazo robótico que captura 6 imágenes del mismo objeto
    desde diferentes ángulos y genera un reporte consolidado.
    """
    
    def __init__(self):
        """Inicializa el servicio"""
        self.segmentation_service = get_segmentation_analysis_service()
        self.num_angulos = 6  # Número de ángulos a capturar
        self.delay_entre_capturas = 5  # Segundos entre capturas (aumentado para prevenir segfaults)
    
    def iniciar_rutina(
        self,
        usuario: Optional[User] = None,
        configuracion_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Inicia una nueva rutina de inspección.
        
        Args:
            usuario: Usuario que ejecuta la rutina
            configuracion_id: ID de configuración a usar (opcional)
        
        Returns:
            Dict con información de la rutina creada
        """
        try:
            logger.info("🔍 Iniciando rutina de inspección multi-ángulo...")
            
            # Generar ID único para la rutina
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            id_rutina = f"rutina_{uuid.uuid4().hex[:8]}_{timestamp}"
            
            # Obtener configuración
            config = None
            if configuracion_id:
                config = ConfiguracionSistema.objects.filter(id=configuracion_id).first()
            if not config:
                config = ConfiguracionSistema.objects.filter(activa=True).first()
            
            # Crear registro de rutina
            rutina = RutinaInspeccion.objects.create(
                id_rutina=id_rutina,
                timestamp_inicio=timezone.now(),
                estado='en_progreso',
                configuracion=config,
                usuario=usuario,
                num_imagenes_capturadas=0
            )
            
            logger.info(f"✅ Rutina creada: {id_rutina}")
            
            return {
                'success': True,
                'rutina_id': rutina.id,
                'id_rutina': id_rutina,
                'num_angulos': self.num_angulos,
                'delay_segundos': self.delay_entre_capturas,
                'mensaje': f'Rutina iniciada. Se capturarán {self.num_angulos} imágenes con {self.delay_entre_capturas}s entre cada una.'
            }
            
        except Exception as e:
            logger.error(f"❌ Error iniciando rutina: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Error iniciando rutina: {str(e)}'
            }
    
    def ejecutar_barrido_automatico(
        self,
        rutina_id: int,
        usuario: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el barrido automático de 6 ángulos.
        
        NOTA: Este método es síncrono y bloqueará por ~18 segundos (6 fotos x 3s).
        Para una implementación asíncrona, usar Celery o similar.
        
        Args:
            rutina_id: ID de la rutina
            usuario: Usuario que ejecuta la rutina
        
        Returns:
            Dict con resultado del barrido
        """
        try:
            rutina = RutinaInspeccion.objects.get(id=rutina_id)
            analisis_ids = []
            
            logger.info(f"📸 Iniciando barrido automático para rutina {rutina.id_rutina}")
            logger.info(f"   Se capturarán {self.num_angulos} imágenes con {self.delay_entre_capturas}s entre cada una")
            
            for angulo in range(1, self.num_angulos + 1):
                logger.info(f"\n🎬 Capturando ángulo {angulo}/{self.num_angulos}...")
                
                # Capturar y analizar imagen
                resultado = self.segmentation_service.analizar_imagen(
                    tipo_analisis='medicion_defectos',
                    usuario=usuario,
                    configuracion_id=rutina.configuracion_id if rutina.configuracion else None
                )
                
                if 'error' in resultado:
                    logger.error(f"❌ Error en ángulo {angulo}: {resultado['error']}")
                    # Continuar con los demás ángulos
                    continue
                
                # Guardar ID del análisis (analisis_id es el ID numérico de BD)
                analisis_ids.append(resultado['analisis_id'])
                
                # Actualizar contador de imágenes
                rutina.num_imagenes_capturadas = angulo
                rutina.save()
                
                logger.info(f"✅ Ángulo {angulo} completado: {resultado['id_analisis']}")
                
                # Liberar recursos del segmentador para evitar acumulación de memoria
                # y posibles segfaults en inferencias consecutivas
                if self.segmentation_service.segmentador_defectos:
                    logger.info(f"🧹 Liberando segmentador de defectos (evitar segfaults)...")
                    del self.segmentation_service.segmentador_defectos
                    self.segmentation_service.segmentador_defectos = None
                    import gc
                    gc.collect()
                    logger.info(f"✅ Recursos liberados")
                
                # Esperar antes de la siguiente captura (excepto en la última)
                if angulo < self.num_angulos:
                    logger.info(f"⏳ Esperando {self.delay_entre_capturas}s antes del siguiente ángulo...")
                    time.sleep(self.delay_entre_capturas)
            
            logger.info(f"\n✅ Barrido completado: {len(analisis_ids)} ángulos capturados")
            
            return {
                'success': True,
                'analisis_ids': analisis_ids,
                'num_capturas': len(analisis_ids),
                'mensaje': f'Barrido completado: {len(analisis_ids)} imágenes capturadas'
            }
            
        except RutinaInspeccion.DoesNotExist:
            return {
                'success': False,
                'error': 'Rutina no encontrada'
            }
        except Exception as e:
            logger.error(f"❌ Error ejecutando barrido: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Error en barrido: {str(e)}'
            }
    
    def finalizar_rutina(
        self,
        rutina_id: int
    ) -> Dict[str, Any]:
        """
        Finaliza la rutina: genera imagen consolidada y reporte.
        
        Args:
            rutina_id: ID de la rutina
        
        Returns:
            Dict con resultado de la finalización
        """
        try:
            rutina = RutinaInspeccion.objects.get(id=rutina_id)
            
            logger.info(f"🏁 Finalizando rutina {rutina.id_rutina}...")
            
            # Obtener todos los análisis de esta rutina
            # Los análisis se crean en el orden de captura
            analisis_list = AnalisisCople.objects.filter(
                tipo_analisis='medicion_defectos',
                timestamp_procesamiento__gte=rutina.timestamp_inicio,
                usuario=rutina.usuario
            ).order_by('timestamp_procesamiento')[:rutina.num_imagenes_capturadas]
            
            if analisis_list.count() != self.num_angulos:
                logger.warning(f"⚠️  Se esperaban {self.num_angulos} análisis, se encontraron {analisis_list.count()}")
            
            # Generar imagen consolidada
            imagen_consolidada_path = self._generar_imagen_consolidada(rutina, analisis_list)
            
            # Generar reporte consolidado
            reporte = self._generar_reporte_consolidado(rutina, analisis_list)
            
            # Actualizar rutina
            rutina.timestamp_fin = timezone.now()
            rutina.estado = 'completado'
            rutina.imagen_consolidada = imagen_consolidada_path
            rutina.reporte_json = reporte
            rutina.save()
            
            logger.info(f"✅ Rutina finalizada: {rutina.id_rutina}")
            
            return {
                'success': True,
                'rutina_id': rutina.id,
                'id_rutina': rutina.id_rutina,
                'num_analisis': analisis_list.count(),
                'imagen_consolidada': imagen_consolidada_path,
                'reporte': reporte,
                'mensaje': 'Rutina finalizada exitosamente'
            }
            
        except RutinaInspeccion.DoesNotExist:
            return {
                'success': False,
                'error': 'Rutina no encontrada'
            }
        except Exception as e:
            logger.error(f"❌ Error finalizando rutina: {e}", exc_info=True)
            
            # Marcar rutina como error
            try:
                rutina = RutinaInspeccion.objects.get(id=rutina_id)
                rutina.estado = 'error'
                rutina.timestamp_fin = timezone.now()
                rutina.save()
            except:
                pass
            
            return {
                'success': False,
                'error': f'Error finalizando rutina: {str(e)}'
            }
    
    def _generar_imagen_consolidada(
        self,
        rutina: RutinaInspeccion,
        analisis_list
    ) -> str:
        """
        Genera una imagen consolidada con grid 2x3 de las imágenes procesadas.
        
        Args:
            rutina: Registro de rutina
            analisis_list: QuerySet de análisis
        
        Returns:
            Path relativo de la imagen guardada
        """
        logger.info("🎨 Generando imagen consolidada (Grid 2x3)...")
        
        try:
            # Dimensiones para cada celda del grid
            cell_width = 320  # Ancho de cada imagen en el grid
            cell_height = 320  # Alto de cada imagen en el grid
            
            # Grid 2 filas x 3 columnas
            grid_height = 2 * cell_height
            grid_width = 3 * cell_width
            
            # Crear imagen base
            grid_image = np.ones((grid_height, grid_width, 3), dtype=np.uint8) * 240  # Fondo gris claro
            
            # Colocar cada imagen procesada en el grid
            for idx, analisis in enumerate(analisis_list[:6]):  # Máximo 6
                if not analisis.archivo_imagen:
                    logger.warning(f"   ⚠️  Análisis {analisis.id_analisis} sin imagen procesada")
                    continue
                
                # Leer imagen procesada
                try:
                    imagen_path = analisis.archivo_imagen.path
                    imagen = cv2.imread(imagen_path)
                    
                    if imagen is None:
                        logger.warning(f"   ⚠️  No se pudo leer imagen: {imagen_path}")
                        continue
                    
                    # Redimensionar a tamaño de celda
                    imagen_resized = cv2.resize(imagen, (cell_width, cell_height))
                    
                    # Calcular posición en el grid
                    row = idx // 3  # 0 o 1
                    col = idx % 3   # 0, 1 o 2
                    
                    y_start = row * cell_height
                    y_end = y_start + cell_height
                    x_start = col * cell_width
                    x_end = x_start + cell_width
                    
                    # Colocar imagen en el grid
                    grid_image[y_start:y_end, x_start:x_end] = imagen_resized
                    
                    # Agregar etiqueta de ángulo
                    etiqueta = f"Angulo {idx + 1}"
                    cv2.putText(
                        grid_image,
                        etiqueta,
                        (x_start + 10, y_start + 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA
                    )
                    
                    logger.info(f"   ✅ Ángulo {idx + 1} agregado al grid")
                    
                except Exception as e:
                    logger.error(f"   ❌ Error procesando imagen {idx + 1}: {e}")
                    continue
            
            # Guardar imagen consolidada
            media_dir = os.path.join(settings.MEDIA_ROOT, 'rutinas')
            os.makedirs(media_dir, exist_ok=True)
            
            filename = f"rutina_{rutina.id_rutina}_consolidada.jpg"
            filepath = os.path.join(media_dir, filename)
            
            cv2.imwrite(filepath, grid_image)
            
            logger.info(f"✅ Imagen consolidada guardada: {filename}")
            
            return f"rutinas/{filename}"
            
        except Exception as e:
            logger.error(f"❌ Error generando imagen consolidada: {e}", exc_info=True)
            return ""
    
    def _generar_reporte_consolidado(
        self,
        rutina: RutinaInspeccion,
        analisis_list
    ) -> Dict[str, Any]:
        """
        Genera un reporte consolidado con estadísticas de los 6 análisis.
        
        Args:
            rutina: Registro de rutina
            analisis_list: QuerySet de análisis
        
        Returns:
            Dict con reporte consolidado
        """
        logger.info("📊 Generando reporte consolidado...")
        
        try:
            reporte = {
                'id_rutina': rutina.id_rutina,
                'num_angulos': analisis_list.count(),
                'angulos': [],
                'resumen': {
                    'total_defectos': 0,
                    'defectos_por_angulo': [],
                    'tiempo_total_ms': 0,
                }
            }
            
            total_defectos = 0
            defectos_por_angulo = []
            
            # Procesar cada ángulo
            for idx, analisis in enumerate(analisis_list):
                num_defectos = analisis.segmentaciones_defectos.count()
                total_defectos += num_defectos
                defectos_por_angulo.append(num_defectos)
                
                angulo_data = {
                    'angulo_num': idx + 1,
                    'id_analisis': analisis.id_analisis,
                    'num_defectos': num_defectos,
                    'tiempo_ms': analisis.tiempo_total_ms or 0,
                    'timestamp': analisis.timestamp_procesamiento.isoformat()
                }
                
                reporte['angulos'].append(angulo_data)
                logger.info(f"   Ángulo {idx + 1}: {num_defectos} defectos detectados")
            
            # Actualizar resumen
            reporte['resumen']['total_defectos'] = total_defectos
            reporte['resumen']['defectos_por_angulo'] = defectos_por_angulo
            reporte['resumen']['promedio_defectos'] = total_defectos / max(analisis_list.count(), 1)
            reporte['resumen']['tiempo_total_ms'] = sum(a.tiempo_total_ms or 0 for a in analisis_list)
            
            logger.info(f"✅ Reporte generado: {total_defectos} defectos totales")
            
            return reporte
            
        except Exception as e:
            logger.error(f"❌ Error generando reporte: {e}", exc_info=True)
            return {}


# Instancia singleton
_rutina_service_instance = None

def get_rutina_inspeccion_service() -> RutinaInspeccionService:
    """Obtiene la instancia singleton del servicio"""
    global _rutina_service_instance
    
    if _rutina_service_instance is None:
        _rutina_service_instance = RutinaInspeccionService()
        logger.info("✅ RutinaInspeccionService inicializado")
    
    return _rutina_service_instance

