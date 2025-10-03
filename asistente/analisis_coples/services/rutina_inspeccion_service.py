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
        self.delay_entre_capturas = 2  # Segundos entre capturas (solo captura, sin ONNX)
        self.delay_entre_analisis = 10  # Segundos entre análisis (liberar memoria de ONNX)
    
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
        
        ESTRATEGIA DE 2 FASES (para prevenir segfaults en inferencias consecutivas):
        FASE 1: Capturar 6 imágenes y guardarlas en disco
        FASE 2: Analizar las 6 imágenes guardadas (una por una)
        
        Args:
            rutina_id: ID de la rutina
            usuario: Usuario que ejecuta la rutina
        
        Returns:
            Dict con resultado del barrido
        """
        try:
            rutina = RutinaInspeccion.objects.get(id=rutina_id)
            
            logger.info(f"📸 Iniciando barrido automático para rutina {rutina.id_rutina}")
            logger.info(f"   FASE 1: Capturar {self.num_angulos} imágenes con {self.delay_entre_capturas}s entre cada una")
            logger.info(f"   FASE 2: Analizar las {self.num_angulos} imágenes guardadas")
            
            # FASE 1: CAPTURA DE IMÁGENES (guardar en disco, no RAM)
            imagenes_paths = []
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_rutinas', rutina.id_rutina)
            os.makedirs(temp_dir, exist_ok=True)
            
            for angulo in range(1, self.num_angulos + 1):
                logger.info(f"\n📸 FASE 1 - Capturando imagen {angulo}/{self.num_angulos}...")
                
                # Capturar imagen
                estado_camara = self.segmentation_service.camera_service.obtener_estado()
                if not estado_camara['activa']:
                    logger.error(f"❌ Cámara no activa en ángulo {angulo}")
                    continue
                
                exito, imagen = self.segmentation_service.camera_service.capturar_imagen()
                
                if not exito or imagen is None:
                    logger.error(f"❌ Error capturando imagen en ángulo {angulo}")
                    continue
                
                # Guardar imagen en disco (PNG sin pérdida, evita corrupción de JPEG)
                filename = f"angulo_{angulo}.png"
                filepath = os.path.join(temp_dir, filename)
                
                # Verificar imagen antes de guardar
                logger.info(f"   📊 Imagen a guardar: shape={imagen.shape}, dtype={imagen.dtype}, min={imagen.min()}, max={imagen.max()}")
                
                # Guardar en PNG (sin compresión/pérdida)
                exito_guardado = cv2.imwrite(filepath, imagen)
                
                if not exito_guardado:
                    logger.error(f"❌ Error guardando imagen {angulo}")
                    continue
                
                # Verificar que se guardó correctamente leyendo de vuelta
                test_read = cv2.imread(filepath)
                if test_read is None:
                    logger.error(f"❌ Imagen {angulo} corrupta en disco, no se puede leer")
                    continue
                
                logger.info(f"   ✅ Verificación: imagen leída correctamente, shape={test_read.shape}")
                
                imagenes_paths.append({
                    'angulo': angulo,
                    'filepath': filepath,
                    'timestamp': timezone.now()
                })
                
                # Actualizar contador
                rutina.num_imagenes_capturadas = angulo
                rutina.save()
                
                logger.info(f"✅ Imagen {angulo} guardada y verificada en disco: {filename}")
                
                # Esperar antes de la siguiente captura (delay corto, solo captura)
                if angulo < self.num_angulos:
                    logger.info(f"⏳ Esperando {self.delay_entre_capturas}s...")
                    time.sleep(self.delay_entre_capturas)
            
            logger.info(f"\n✅ FASE 1 COMPLETADA: {len(imagenes_paths)} imágenes guardadas en disco")
            
            # FASE 2: ANÁLISIS DE IMÁGENES (desde disco, con delay largo)
            logger.info(f"\n🔍 FASE 2 - Analizando {len(imagenes_paths)} imágenes desde disco...")
            logger.info(f"   Delay entre análisis: {self.delay_entre_analisis}s (liberar memoria ONNX)")
            analisis_ids = []
            
            for idx, imagen_data in enumerate(imagenes_paths):
                angulo = imagen_data['angulo']
                filepath = imagen_data['filepath']
                
                logger.info(f"\n🔬 Analizando imagen {idx + 1}/{len(imagenes_paths)} (Ángulo {angulo})...")
                
                # Leer imagen desde disco
                imagen = cv2.imread(filepath)
                if imagen is None:
                    logger.error(f"❌ Error leyendo imagen desde {filepath}")
                    continue
                
                # Verificar integridad de la imagen leída
                logger.info(f"   📊 Imagen leída: shape={imagen.shape}, dtype={imagen.dtype}, min={imagen.min()}, max={imagen.max()}")
                
                # Validar que la imagen sea correcta
                if imagen.shape != (640, 640, 3):
                    logger.error(f"❌ Imagen con shape incorrecto: {imagen.shape}, esperado (640, 640, 3)")
                    continue
                
                if imagen.dtype != np.uint8:
                    logger.error(f"❌ Imagen con dtype incorrecto: {imagen.dtype}, esperado uint8")
                    continue
                
                if np.isnan(imagen).any() or np.isinf(imagen).any():
                    logger.error(f"❌ Imagen contiene NaN o Inf")
                    continue
                
                logger.info(f"   ✅ Imagen válida, procediendo con análisis...")
                
                # Analizar imagen (crea análisis en BD)
                resultado = self._analizar_imagen_guardada(
                    imagen=imagen,
                    usuario=usuario,
                    configuracion=rutina.configuracion,
                    timestamp_captura=imagen_data['timestamp']
                )
                
                if 'error' in resultado:
                    logger.error(f"❌ Error analizando ángulo {angulo}: {resultado['error']}")
                    continue
                
                analisis_ids.append(resultado['analisis_id'])
                logger.info(f"✅ Ángulo {angulo} analizado: {resultado['id_analisis']}")
                
                # Liberar segmentador y esperar antes del siguiente análisis
                if self.segmentation_service.segmentador_defectos:
                    logger.info(f"🧹 Liberando segmentador...")
                    del self.segmentation_service.segmentador_defectos
                    self.segmentation_service.segmentador_defectos = None
                    import gc
                    gc.collect()
                    logger.info(f"✅ Memoria liberada")
                
                # Delay largo entre análisis para dar tiempo a liberar memoria ONNX
                if idx < len(imagenes_paths) - 1:
                    logger.info(f"⏳ Esperando {self.delay_entre_analisis}s antes del siguiente análisis...")
                    time.sleep(self.delay_entre_analisis)
            
            # Limpiar archivos temporales
            try:
                import shutil
                shutil.rmtree(temp_dir)
                logger.info(f"🗑️  Imágenes temporales eliminadas: {temp_dir}")
            except Exception as e:
                logger.warning(f"⚠️  No se pudieron eliminar archivos temporales: {e}")
            
            logger.info(f"\n✅ FASE 2 COMPLETADA: {len(analisis_ids)} imágenes analizadas")
            logger.info(f"\n✅ Barrido total completado: {len(analisis_ids)} ángulos exitosos")
            
            return {
                'success': True,
                'analisis_ids': analisis_ids,
                'num_capturas': len(analisis_ids),
                'mensaje': f'Barrido completado: {len(analisis_ids)} imágenes capturadas y analizadas'
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
    
    def _analizar_imagen_guardada(
        self,
        imagen: np.ndarray,
        usuario: Optional[User],
        configuracion: Optional[ConfiguracionSistema],
        timestamp_captura
    ) -> Dict[str, Any]:
        """
        Analiza una imagen ya capturada (no captura nueva).
        Similar a analizar_imagen pero usa imagen ya guardada.
        """
        try:
            # Inicializar segmentador de defectos
            if not self.segmentation_service._inicializar_segmentador('defectos'):
                return {'error': 'Error inicializando segmentador de defectos'}
            
            # Configurar factor de conversión si existe
            if configuracion and configuracion.factor_conversion_px_mm:
                self.segmentation_service.measurement_service.set_conversion_factor(
                    configuracion.factor_conversion_px_mm
                )
            
            # Generar ID único
            id_analisis = f"analisis_{uuid.uuid4().hex[:8]}_{int(time.time())}"
            
            # Crear registro en BD
            analisis_db = AnalisisCople.objects.create(
                id_analisis=id_analisis,
                timestamp_captura=timestamp_captura,
                tipo_analisis='medicion_defectos',
                estado='procesando',
                configuracion=configuracion,
                usuario=usuario,
                archivo_imagen="",
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
            
            # Ejecutar segmentación
            inicio_seg = time.time()
            segmentaciones = self.segmentation_service.segmentador_defectos.segmentar(imagen)
            tiempo_seg = (time.time() - inicio_seg) * 1000
            analisis_db.tiempo_segmentacion_defectos_ms = tiempo_seg
            
            # Guardar segmentaciones
            self.segmentation_service._guardar_segmentaciones_defectos(
                analisis_db, segmentaciones, configuracion
            )
            
            # Generar imagen procesada
            imagen_procesada = self.segmentation_service._generar_imagen_procesada(
                imagen, segmentaciones, 'medicion_defectos'
            )
            
            # Guardar imagen procesada (inline, igual que en segmentation_analysis_service)
            if imagen_procesada is not None:
                try:
                    from django.core.files.base import ContentFile
                    
                    # Codificar imagen
                    _, buffer = cv2.imencode('.jpg', imagen_procesada)
                    imagen_bytes = buffer.tobytes()
                    
                    # Nombre del archivo
                    nombre_archivo = f"analisis_{id_analisis}.jpg"
                    
                    # Guardar usando ContentFile
                    analisis_db.archivo_imagen = ContentFile(imagen_bytes, name=nombre_archivo)
                    logger.info(f"💾 Imagen procesada guardada: {nombre_archivo}")
                    
                except Exception as e:
                    logger.error(f"❌ Error guardando imagen procesada: {e}", exc_info=True)
            
            # Finalizar
            analisis_db.tiempo_total_ms = tiempo_seg
            analisis_db.estado = 'completado'
            analisis_db.save()
            
            return {
                'id_analisis': id_analisis,
                'analisis_id': analisis_db.id,
                'estado': 'completado',
                'segmentaciones_count': len(segmentaciones) if segmentaciones else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error analizando imagen: {e}", exc_info=True)
            return {'error': str(e)}
    
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

