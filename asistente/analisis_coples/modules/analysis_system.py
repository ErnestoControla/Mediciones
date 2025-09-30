"""
Sistema Integrado de Análisis de Coples
Combina clasificación y detección en un solo pipeline
"""

import numpy as np
import cv2
import time
import json
from typing import Dict, List, Tuple, Optional
import os
import sys

# Agregar path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# from modules.capture import CamaraTiempoOptimizada  # Comentado temporalmente - usar solo webcam
from modules.capture.webcam_fallback import WebcamFallback, detectar_mejor_webcam
from modules.classification import ClasificadorCoplesONNX, ProcesadorImagenClasificacion
# from modules.detection import DetectorPiezasCoples, ProcesadorPiezasCoples, DetectorDefectosCoples, ProcesadorDefectos  # Comentado temporalmente
# from modules.segmentation import SegmentadorDefectosCoples, ProcesadorSegmentacionDefectos  # Comentado temporalmente
from modules.metadata_standard import MetadataStandard
# from modules.segmentation.segmentation_piezas_engine import SegmentadorPiezasCoples  # Comentado temporalmente
# from modules.segmentation.piezas_segmentation_processor import ProcesadorSegmentacionPiezas  # Comentado temporalmente
from modules.preprocessing.illumination_robust import RobustezIluminacion
from modules.adaptive_thresholds import UmbralesAdaptativos
from analisis_coples.expo_config import GlobalConfig, RobustezConfig, WebcamConfig


class SistemaAnalisisIntegrado:
    """
    Sistema que integra clasificación y detección de coples
    """
    
    def __init__(self):
        """Inicializa el sistema integrado de análisis"""
        # Componentes del sistema
        self.camara = None
        self.webcam_fallback = None
        self.usando_webcam = False
        self.clasificador = None
        self.detector_piezas = None
        self.detector_defectos = None
        self.segmentador_defectos = None
        self.segmentador_piezas = None
        self.procesador_clasificacion = None
        self.procesador_deteccion_piezas = None
        self.procesador_deteccion_defectos = None
        self.procesador_segmentacion_defectos = None
        self.procesador_segmentacion_piezas = None
        
        # Componentes de robustez
        self.robustez_iluminacion = RobustezIluminacion()
        self.umbrales_adaptativos = UmbralesAdaptativos()
        
        # Estado del sistema
        self.inicializado = False
        self.contador_resultados = 0
        
        # Directorios de salida por módulo
        self.directorios_salida = {
            "clasificacion": "Salida_cople/Salida_clas_def",
            "deteccion_piezas": "Salida_cople/Salida_det_pz",
            "deteccion_defectos": "Salida_cople/Salida_det_def",
            "segmentacion_defectos": "Salida_cople/Salida_seg_def",
            "segmentacion_piezas": "Salida_cople/Salida_seg_pz"
        }
        
        # Crear directorios si no existen
        for directorio in self.directorios_salida.values():
            if not os.path.exists(directorio):
                os.makedirs(directorio)
    
    def _inicializar_webcam_fallback(self) -> bool:
        """
        Inicializa el fallback a webcam
        
        Returns:
            bool: True si se inicializó correctamente
        """
        try:
            # Detectar mejor webcam disponible
            webcam_id = detectar_mejor_webcam()
            if webcam_id is None:
                print("❌ No se encontraron webcams disponibles")
                return False
            
            print(f"📷 Usando webcam en dispositivo {webcam_id}")
            
            # Crear e inicializar webcam
            self.webcam_fallback = WebcamFallback(
                device_id=webcam_id,
                width=WebcamConfig.WIDTH,
                height=WebcamConfig.HEIGHT,
                use_crop=WebcamConfig.USE_CROP
            )
            
            if not self.webcam_fallback.inicializar():
                print("❌ Error inicializando webcam")
                return False
            
            # Marcar que estamos usando webcam
            self.usando_webcam = True
            
            return True
            
        except Exception as e:
            print(f"❌ Error en fallback a webcam: {e}")
            return False
    
    def inicializar(self) -> bool:
        """
        Inicializa todos los componentes del sistema
        
        Returns:
            True si se inicializó correctamente
        """
        try:
            print("🚀 Inicializando sistema integrado de análisis...")
            
            # 1. Inicializar webcam directamente (sin cámara GigE)
            print("📷 Inicializando webcam...")
            if not self._inicializar_webcam_fallback():
                print("❌ Error inicializando webcam")
                return False
            else:
                print("✅ Webcam inicializada correctamente")
            
            # 2. Inicializar clasificador
            print("🧠 Inicializando clasificador...")
            self.clasificador = ClasificadorCoplesONNX()
            if not self.clasificador.inicializar():
                print("❌ Error inicializando clasificador")
                return False
            self.procesador_clasificacion = ProcesadorImagenClasificacion()
            
            # 3. Inicializar detector de piezas (COMENTADO - Solo clasificación)
            # print("🎯 Inicializando detector de piezas...")
            # self.detector_piezas = DetectorPiezasCoples()
            # self.procesador_deteccion_piezas = ProcesadorPiezasCoples()
            
            # 4. Inicializar detector de defectos (COMENTADO - Solo clasificación)
            # print("🎯 Inicializando detector de defectos...")
            # self.detector_defectos = DetectorDefectosCoples()
            # if not self.detector_defectos.inicializar():
            #     print("❌ Error inicializando detector de defectos")
            #     return False
            # self.procesador_deteccion_defectos = ProcesadorDefectos()
            
            # 5. Inicializar segmentador de defectos (COMENTADO - Solo clasificación)
            # print("🎯 Inicializando segmentador de defectos...")
            # self.segmentador_defectos = SegmentadorDefectosCoples()
            # if not self.segmentador_defectos._inicializar_modelo():
            #     print("❌ Error inicializando segmentador de defectos")
            #     return False
            # self.procesador_segmentacion_defectos = ProcesadorSegmentacionDefectos()
            
            # 6. Inicializar segmentador de piezas (COMENTADO - Solo clasificación)
            # print("🎯 Inicializando segmentador de piezas...")
            # self.segmentador_piezas = SegmentadorPiezasCoples()
            # if not self.segmentador_piezas.stats['inicializado']:
            #     print("❌ Error inicializando segmentador de piezas")
            #     return False
            # self.procesador_segmentacion_piezas = ProcesadorSegmentacionPiezas()
            
            # 7. Iniciar captura continua (solo para cámara GigE)
            if not self.usando_webcam:
                print("🎬 Iniciando captura continua...")
                if not self.camara.iniciar_captura_continua():
                    print("❌ Error iniciando captura continua")
                    return False
            else:
                print("🎬 Iniciando captura continua de webcam...")
                if not self.webcam_fallback.iniciar_captura_continua():
                    print("❌ Error iniciando captura continua de webcam")
                    return False
            
            # 7. Aplicar configuración de robustez por defecto
            print("🔧 Aplicando configuración de robustez por defecto...")
            config_default = RobustezConfig.CONFIGURACION_DEFAULT
            if config_default == RobustezConfig.UMBRALES_ORIGINAL:
                self.aplicar_configuracion_robustez("original")
            elif config_default == RobustezConfig.UMBRALES_MODERADA:
                self.aplicar_configuracion_robustez("moderada")
            elif config_default == RobustezConfig.UMBRALES_PERMISIVA:
                self.aplicar_configuracion_robustez("permisiva")
            elif config_default == RobustezConfig.UMBRALES_ULTRA_PERMISIVA:
                self.aplicar_configuracion_robustez("ultra_permisiva")
            else:
                self.aplicar_configuracion_robustez("original")  # Fallback a original
            
            self.inicializado = True
            print("✅ Sistema integrado inicializado correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando sistema: {e}")
            return False
    
    def capturar_imagen_unica(self) -> Dict:
        """
        Captura una sola imagen para procesamiento por módulos
        
        Returns:
            Diccionario con la imagen capturada y metadatos
        """
        if not self.inicializado:
            return {"error": "Sistema no inicializado"}
        
        try:
            tiempo_inicio = time.time()
            
            # Capturar imagen usando webcam
            if self.webcam_fallback is not None:
                # Para webcam, usar captura síncrona que es más confiable
                resultado_captura = self.webcam_fallback.obtener_frame_sincrono()
            else:
                return {"error": "Webcam no inicializada"}
                
            if resultado_captura is None or resultado_captura[0] is None:
                return {"error": "No se pudo capturar imagen"}
            
            # resultado_captura es una tupla: (frame, tiempo_acceso_ms, timestamp)
            frame, tiempo_acceso_ms, timestamp = resultado_captura
            
            tiempo_captura = (time.time() - tiempo_inicio) * 1000
            
            # Crear timestamp único para esta captura
            timestamp_captura = time.strftime("%Y%m%d_%H%M%S")
            
            resultados = {
                "frame": frame,
                "timestamp_captura": timestamp_captura,
                "tiempos": {
                    "captura_ms": tiempo_captura,
                    "tiempo_acceso_ms": tiempo_acceso_ms
                },
                "timestamp_original": timestamp
            }
            
            print(f"📷 Imagen capturada: {timestamp_captura}")
            return resultados
            
        except Exception as e:
            print(f"❌ Error capturando imagen: {e}")
            return {"error": str(e)}
    
    def analisis_completo(self) -> Dict:
        """
        Realiza análisis completo: clasificación + detección de manera SECUENCIAL
        
        Returns:
            Diccionario con resultados completos
        """
        if not self.inicializado:
            return {"error": "Sistema no inicializado"}
        
        try:
            print("🚀 INICIANDO ANÁLISIS COMPLETO SECUENCIAL...")
            
            # 1. Pausar captura continua temporalmente
            print("⏸️ Pausando captura continua para análisis...")
            self.camara.pausar_captura_continua()
            
            # 2. Capturar imagen única
            print("📷 Capturando imagen única...")
            resultado_captura = self.capturar_imagen_unica()
            if "error" in resultado_captura:
                # Reanudar captura continua en caso de error
                self.camara.reanudar_captura_continua()
                return resultado_captura
            
            frame = resultado_captura["frame"]
            timestamp_captura = resultado_captura["timestamp_captura"]
            tiempo_captura = resultado_captura["tiempos"]["captura_ms"]  # Usar tiempo de capturar_imagen_unica
            print(f"✅ Imagen capturada en {tiempo_captura:.2f} ms")
            
            # Verificar frame capturado (logs simplificados)
            print(f"📊 Frame capturado: {frame.shape if hasattr(frame, 'shape') else 'No shape'}")
            
            # CORREGIDO: Iniciar cronómetro total DESPUÉS de captura, ANTES de procesamiento
            tiempo_inicio_total = time.time()
            
            # 3. CLASIFICACIÓN (SECUENCIAL)
            print("\n🧠 EJECUTANDO CLASIFICACIÓN...")
            
            tiempo_clasificacion_inicio = time.time()
            resultado_clasificacion = self.clasificador.clasificar(frame)
            tiempo_clasificacion = (time.time() - tiempo_clasificacion_inicio) * 1000
            clase_predicha, confianza, tiempo_inferencia_clas = resultado_clasificacion
            print(f"✅ Clasificación completada en {tiempo_clasificacion:.2f} ms")
            print(f"   Resultado: {clase_predicha} ({confianza:.2%})")
            
            # 4. DETECCIÓN DE PIEZAS (SECUENCIAL)
            # DETECCIÓN DE PIEZAS COMENTADA - Solo clasificación
            # print("\n🎯 EJECUTANDO DETECCIÓN DE PIEZAS...")
            # 
            # # SOLUCIÓN CRÍTICA: Reinicializar detector de piezas antes de usar
            # print("   🔧 Reinicializando detector de piezas...")
            # try:
            #     self.detector_piezas.liberar()
            #     # Crear nueva instancia del detector de piezas
            #     from modules.detection.detection_engine import DetectorPiezasCoples
            #     self.detector_piezas = DetectorPiezasCoples(confianza_min=0.55)
            #     print("   ✅ Detector de piezas reinicializado correctamente")
            #     
            #     tiempo_deteccion_piezas_inicio = time.time()
            #     detecciones_piezas = self.detector_piezas.detectar_piezas(frame)
            #     tiempo_deteccion_piezas = (time.time() - tiempo_deteccion_piezas_inicio) * 1000
            #     print(f"✅ Detección de piezas completada en {tiempo_deteccion_piezas:.2f} ms")
            #     print(f"   Piezas detectadas: {len(detecciones_piezas)}")
            #     
            # except Exception as e:
            #     print(f"❌ ERROR en detección de piezas: {e}")
            #     detecciones_piezas = []
            #     tiempo_deteccion_piezas = 0
            
            # Simular detecciones vacías para solo clasificación
            detecciones_piezas = []
            tiempo_deteccion_piezas = 0
            
            # 5. DETECCIÓN DE DEFECTOS (COMENTADA - Solo clasificación)
            # print("\n🔍 EJECUTANDO DETECCIÓN DE DEFECTOS...")
            # 
            # # SOLUCIÓN CRÍTICA: Reinicializar detector de defectos antes de usar
            # print("   🔧 Reinicializando detector de defectos...")
            # try:
            #     self.detector_defectos.liberar()
            #     if not self.detector_defectos.inicializar():
            #         print("❌ Error reinicializando detector de defectos")
            #         detecciones_defectos = []
            #         tiempo_deteccion_defectos = 0
            #     else:
            #         print("   ✅ Detector de defectos reinicializado correctamente")
            #         
            #         tiempo_deteccion_defectos_inicio = time.time()
            #         detecciones_defectos = self.detector_defectos.detectar_defectos(frame)
            #         tiempo_deteccion_defectos = (time.time() - tiempo_deteccion_defectos_inicio) * 1000
            #         print(f"✅ Detección de defectos completada en {tiempo_deteccion_defectos:.2f} ms")
            #         print(f"   Defectos detectados: {len(detecciones_defectos)}")
            #         
            # except Exception as e:
            #     print(f"❌ ERROR en detección de defectos: {e}")
            #     print(f"   🔍 Frame original intacto - ID: {id(frame)}")
            #     detecciones_defectos = []
            #     tiempo_deteccion_defectos = (time.time() - tiempo_deteccion_defectos_inicio) * 1000
            
            # Simular detecciones vacías para solo clasificación
            detecciones_defectos = []
            tiempo_deteccion_defectos = 0
            
            # 6. SEGMENTACIÓN DE DEFECTOS (COMENTADA - Solo clasificación)
            # print("\n🎨 EJECUTANDO SEGMENTACIÓN DE DEFECTOS...")
            # print(f"🔍 DEBUG - Frame para segmentación:")
            # print(f"   Tipo: {type(frame)}")
            # print(f"   Shape: {frame.shape if hasattr(frame, 'shape') else 'No shape'}")
            # print(f"   Dtype: {frame.dtype if hasattr(frame, 'dtype') else 'No dtype'}")
            # print(f"   Rango valores: [{frame.min() if hasattr(frame, 'min') else 'N/A'}, {frame.max() if hasattr(frame, 'max') else 'N/A'}]")
            # print(f"   ID del objeto: {id(frame)}")
            # 
            # # SOLUCIÓN CRÍTICA: Reinicializar segmentador antes de usar
            # print("   🔧 Reinicializando segmentador de defectos...")
            # tiempo_segmentacion_inicio = time.time()  # Inicializar antes del try
            # try:
            #     self.segmentador_defectos.liberar()
            #     # Crear nueva instancia del segmentador
            #     from modules.segmentation.segmentation_defectos_engine import SegmentadorDefectosCoples
            #     self.segmentador_defectos = SegmentadorDefectosCoples(confianza_min=0.55)
            #     print("   ✅ Segmentador de defectos reinicializado correctamente")
            #     
            #     tiempo_segmentacion_inicio = time.time()
            #     segmentaciones_defectos = self.segmentador_defectos.segmentar_defectos(frame)
            #     tiempo_segmentacion = (time.time() - tiempo_segmentacion_inicio) * 1000
            #     print(f"✅ Segmentación de defectos completada en {tiempo_segmentacion:.2f} ms")
            #     print(f"   Segmentaciones detectadas: {len(segmentaciones_defectos)}")
            #     
            # except Exception as e:
            #     print(f"❌ ERROR en segmentación de defectos: {e}")
            #     print(f"   🔍 Frame original intacto - ID: {id(frame)}")
            #     segmentaciones_defectos = []
            #     tiempo_segmentacion = (time.time() - tiempo_segmentacion_inicio) * 1000
            
            # Simular segmentaciones vacías para solo clasificación
            segmentaciones_defectos = []
            tiempo_segmentacion = 0
            
            # 6. SEGMENTACIÓN DE PIEZAS (COMENTADA - Solo clasificación)
            # print("\n🎨 EJECUTANDO SEGMENTACIÓN DE PIEZAS...")
            # print(f"🔍 DEBUG - Frame para segmentación de piezas:")
            # print(f"   Tipo: {type(frame)}")
            # print(f"   Shape: {frame.shape if hasattr(frame, 'shape') else 'No shape'}")
            # print(f"   Dtype: {frame.dtype if hasattr(frame, 'dtype') else 'No dtype'}")
            # print(f"   Rango valores: [{frame.min() if hasattr(frame, 'min') else 'N/A'}, {frame.max() if hasattr(frame, 'max') else 'N/A'}]")
            # print(f"   ID del objeto: {id(frame)}")
            # 
            # # SOLUCIÓN CRÍTICA: Reinicializar segmentador de piezas antes de usar
            # print("   🔧 Reinicializando segmentador de piezas...")
            # try:
            #     self.segmentador_piezas.liberar()
            #     # Recrear segmentador de piezas
            #     from modules.segmentation.segmentation_piezas_engine import SegmentadorPiezasCoples
            #     self.segmentador_piezas = SegmentadorPiezasCoples()
            #     if not self.segmentador_piezas.stats['inicializado']:
            #         print("   ❌ Error reinicializando segmentador de piezas")
            #         segmentaciones_piezas = []
            #         tiempo_segmentacion_piezas = 0
            #     else:
            #         print("   ✅ Segmentador de piezas reinicializado correctamente")
            #         
            #         tiempo_segmentacion_piezas_inicio = time.time()
            #         segmentaciones_piezas = self.segmentador_piezas.segmentar(frame)
            #         tiempo_segmentacion_piezas = (time.time() - tiempo_segmentacion_piezas_inicio) * 1000
            #         print(f"✅ Segmentación de piezas completada en {tiempo_segmentacion_piezas:.2f} ms")
            #         print(f"   Segmentaciones detectadas: {len(segmentaciones_piezas)}")
            #     
            # except Exception as e:
            #     print(f"❌ ERROR en segmentación de piezas: {e}")
            #     print(f"   🔍 Frame original intacto - ID: {id(frame)}")
            #     segmentaciones_piezas = []
            #     tiempo_segmentacion_piezas = 0
            
            # Simular segmentaciones vacías para solo clasificación
            segmentaciones_piezas = []
            tiempo_segmentacion_piezas = 0
            
            # 7. Calcular tiempo total (suma de todos los tiempos de procesamiento + captura)
            tiempo_procesamiento_total = (time.time() - tiempo_inicio_total) * 1000
            tiempo_total = tiempo_captura + tiempo_procesamiento_total
            
            # 8. Crear resultados
            resultados = {
                "clasificacion": {
                    "clase": clase_predicha,
                    "confianza": confianza,
                    "tiempo_inferencia": tiempo_inferencia_clas
                },
                "detecciones_piezas": detecciones_piezas,
                "detecciones_defectos": detecciones_defectos,
                "segmentaciones_defectos": segmentaciones_defectos,
                "segmentaciones_piezas": segmentaciones_piezas,
                "tiempos": {
                    "captura_ms": tiempo_captura,
                    "clasificacion_ms": tiempo_clasificacion,
                    "deteccion_piezas_ms": tiempo_deteccion_piezas,
                    "deteccion_defectos_ms": tiempo_deteccion_defectos,
                    "segmentacion_defectos_ms": tiempo_segmentacion,
                    "segmentacion_piezas_ms": tiempo_segmentacion_piezas,
                    "total_ms": tiempo_total
                },
                "frame": frame,
                "timestamp_captura": timestamp_captura
            }
            
            # 9. Guardar resultados por módulo
            print("\n💾 GUARDANDO RESULTADOS...")
            self._guardar_por_modulos(resultados)
            
            # 10. Reanudar captura continua
            print("▶️ Reanudando captura continua...")
            self.camara.reanudar_captura_continua()
            
            # 11. Pausa mínima para estabilizar sistema
            print("⏸️ Pausa de 0.5 segundos para estabilizar sistema...")
            time.sleep(0.5)
            
            print(f"\n🎉 ANÁLISIS COMPLETO FINALIZADO EN {tiempo_total:.2f} ms")
            return resultados
            
        except Exception as e:
            print(f"❌ Error en análisis completo: {e}")
            import traceback
            traceback.print_exc()
            # Reanudar captura continua en caso de error
            try:
                self.camara.reanudar_captura_continua()
            except:
                pass
            return {"error": str(e)}
    
    def solo_clasificacion(self) -> Dict:
        """
        Realiza solo clasificación
        
        Returns:
            Diccionario con resultados de clasificación
        """
        if not self.inicializado:
            return {"error": "Sistema no inicializado"}
        
        try:
            # 1. Capturar imagen única
            resultado_captura = self.capturar_imagen_unica()
            if "error" in resultado_captura:
                return resultado_captura
            
            frame = resultado_captura["frame"]
            timestamp_captura = resultado_captura["timestamp_captura"]
            tiempo_captura = resultado_captura["tiempos"]["captura_ms"]
            
            # 2. Clasificación
            tiempo_inicio = time.time()  # CORREGIDO: Iniciar cronómetro DESPUÉS de captura
            tiempo_clasificacion_inicio = time.time()
            resultado_clasificacion = self.clasificador.clasificar(frame)
            tiempo_clasificacion = (time.time() - tiempo_clasificacion_inicio) * 1000
            
            # 3. Calcular tiempo total (captura + procesamiento)
            tiempo_procesamiento = (time.time() - tiempo_inicio) * 1000
            tiempo_total = tiempo_captura + tiempo_procesamiento
            
            # 4. Crear resultados
            # resultado_clasificacion es una tupla: (clase, confianza, tiempo_inferencia)
            clase_predicha, confianza, tiempo_inferencia_clas = resultado_clasificacion
            
            resultados = {
                "clasificacion": {
                    "clase": clase_predicha,
                    "confianza": confianza,
                    "tiempo_inferencia": tiempo_inferencia_clas
                },
                "tiempos": {
                    "captura_ms": tiempo_captura,
                    "clasificacion_ms": tiempo_clasificacion,
                    "total_ms": tiempo_total
                },
                "frame": frame,
                "timestamp_captura": timestamp_captura
            }
            
            # 5. Guardar resultados por módulo
            self._guardar_por_modulos(resultados)
            
            return resultados
            
        except Exception as e:
            print(f"❌ Error en clasificación: {e}")
            return {"error": str(e)}
    
    def solo_deteccion(self) -> Dict:
        """
        Realiza solo detección de piezas
        
        Returns:
            Diccionario con resultados de detección
        """
        if not self.inicializado:
            return {"error": "Sistema no inicializado"}
        
        try:
            # 1. Capturar imagen única
            resultado_captura = self.capturar_imagen_unica()
            if "error" in resultado_captura:
                return resultado_captura
            
            frame = resultado_captura["frame"]
            timestamp_captura = resultado_captura["timestamp_captura"]
            tiempo_captura = resultado_captura["tiempos"]["captura_ms"]
            
            # 2. Detección de piezas
            tiempo_inicio = time.time()  # CORREGIDO: Iniciar cronómetro DESPUÉS de captura
            tiempo_deteccion_inicio = time.time()
            detecciones = self.detector_piezas.detectar_piezas(frame)
            tiempo_deteccion = (time.time() - tiempo_deteccion_inicio) * 1000
            
            # 3. Calcular tiempo total (captura + procesamiento)
            tiempo_procesamiento = (time.time() - tiempo_inicio) * 1000
            tiempo_total = tiempo_captura + tiempo_procesamiento
            
            # 4. Crear resultados
            resultados = {
                "detecciones_piezas": detecciones,
                "tiempos": {
                    "captura_ms": tiempo_captura,
                    "deteccion_piezas_ms": tiempo_deteccion,
                    "total_ms": tiempo_total
                },
                "frame": frame,
                "timestamp_captura": timestamp_captura
            }
            
            # 5. Guardar resultados por módulo
            self._guardar_por_modulos(resultados)
            
            return resultados
            
        except Exception as e:
            print(f"❌ Error en detección de piezas: {e}")
            return {"error": str(e)}
    
    def solo_deteccion_defectos(self) -> Dict:
        """
        Realiza solo detección de defectos (sin clasificación)
        
        Returns:
            Diccionario con resultados de detección de defectos
        """
        if not self.inicializado:
            return {"error": "Sistema no inicializado"}
        
        try:
            # 1. Capturar imagen única
            resultado_captura = self.capturar_imagen_unica()
            if "error" in resultado_captura:
                return resultado_captura
            
            frame = resultado_captura["frame"]
            timestamp_captura = resultado_captura["timestamp_captura"]
            tiempo_captura = resultado_captura["tiempos"]["captura_ms"]
            
            # 2. Detección de defectos
            tiempo_inicio = time.time()  # CORREGIDO: Iniciar cronómetro DESPUÉS de captura
            tiempo_deteccion_inicio = time.time()
            detecciones_defectos = self.detector_defectos.detectar_defectos(frame)
            tiempo_deteccion = (time.time() - tiempo_deteccion_inicio) * 1000
            
            # 3. Calcular tiempo total (captura + procesamiento)
            tiempo_procesamiento = (time.time() - tiempo_inicio) * 1000
            tiempo_total = tiempo_captura + tiempo_procesamiento
            
            # 4. Crear resultados
            resultados = {
                "detecciones_defectos": detecciones_defectos,
                "tiempos": {
                    "captura_ms": tiempo_captura,
                    "deteccion_defectos_ms": tiempo_deteccion,
                    "total_ms": tiempo_total
                },
                "frame": frame,
                "timestamp_captura": timestamp_captura
            }
            
            # 5. Guardar resultados por módulo
            self._guardar_por_modulos(resultados)
            
            return resultados
            
        except Exception as e:
            print(f"❌ Error en detección de defectos: {e}")
            return {"error": str(e)}
    
    def solo_segmentacion_defectos(self) -> Dict:
        """
        Realiza solo segmentación de defectos (sin clasificación ni detección)
        
        Returns:
            Diccionario con resultados de segmentación de defectos
        """
        if not self.inicializado:
            return {"error": "Sistema no inicializado"}
        
        try:
            # 1. Capturar imagen única
            resultado_captura = self.capturar_imagen_unica()
            if "error" in resultado_captura:
                return resultado_captura
            
            frame = resultado_captura["frame"]
            timestamp_captura = resultado_captura["timestamp_captura"]
            tiempo_captura = resultado_captura["tiempos"]["captura_ms"]
            
            # 2. Segmentación de defectos
            tiempo_inicio = time.time()  # CORREGIDO: Iniciar cronómetro DESPUÉS de captura
            tiempo_segmentacion_inicio = time.time()
            segmentaciones_defectos = self.segmentador_defectos.segmentar_defectos(frame)
            tiempo_segmentacion = (time.time() - tiempo_segmentacion_inicio) * 1000
            
            # 3. Calcular tiempo total (captura + procesamiento)
            tiempo_procesamiento = (time.time() - tiempo_inicio) * 1000
            tiempo_total = tiempo_captura + tiempo_procesamiento
            
            # 4. Crear resultados
            resultados = {
                "segmentaciones_defectos": segmentaciones_defectos,
                "tiempos": {
                    "captura_ms": tiempo_captura,
                    "segmentacion_defectos_ms": tiempo_segmentacion,
                    "total_ms": tiempo_total
                },
                "frame": frame,
                "timestamp_captura": timestamp_captura
            }
            
            # 5. Guardar resultados por módulo
            self._guardar_por_modulos(resultados)
            
            return resultados
            
        except Exception as e:
            print(f"❌ Error en segmentación de defectos: {e}")
            return {"error": str(e)}
    
    def solo_segmentacion_piezas(self) -> Dict:
        """
        Realiza solo segmentación de piezas (sin clasificación ni detección)
        
        Returns:
            Diccionario con resultados de segmentación de piezas
        """
        if not self.inicializado:
            return {"error": "Sistema no inicializado"}
        
        try:
            # 1. Capturar imagen única
            resultado_captura = self.capturar_imagen_unica()
            if "error" in resultado_captura:
                return resultado_captura
            
            frame = resultado_captura["frame"]
            timestamp_captura = resultado_captura["timestamp_captura"]
            tiempo_captura = resultado_captura["tiempos"]["captura_ms"]
            
            # 2. Segmentación de piezas
            tiempo_inicio = time.time()  # CORREGIDO: Iniciar cronómetro DESPUÉS de captura
            tiempo_segmentacion_inicio = time.time()
            segmentaciones_piezas = self.segmentador_piezas.segmentar(frame)
            tiempo_segmentacion = (time.time() - tiempo_segmentacion_inicio) * 1000
            
            # 3. Calcular tiempo total (captura + procesamiento)
            tiempo_procesamiento = (time.time() - tiempo_inicio) * 1000
            tiempo_total = tiempo_captura + tiempo_procesamiento
            
            # 4. Crear resultados
            resultados = {
                "frame": frame,
                "timestamp_captura": timestamp_captura,
                "segmentaciones_piezas": segmentaciones_piezas,
                "tiempos": {
                    "captura_ms": tiempo_captura,
                    "segmentacion_piezas_ms": tiempo_segmentacion,
                    "total_ms": tiempo_total
                }
            }
            
            # 5. Procesar y guardar resultados
            self.procesador_segmentacion_piezas.procesar_segmentaciones(
                frame, segmentaciones_piezas, timestamp_captura, resultados["tiempos"]
            )
            
            # 6. Mostrar resultados
            print(f"\n🎯 SEGMENTACIÓN DE PIEZAS:")
            print(f"   Segmentaciones detectadas: {len(segmentaciones_piezas)}")
            for i, seg in enumerate(segmentaciones_piezas):
                print(f"   Segmentación #{i+1}: {seg['clase']} - {seg['confianza']:.2%}")
                print(f"     BBox: ({seg['bbox']['x1']}, {seg['bbox']['y1']}) a ({seg['bbox']['x2']}, {seg['bbox']['y2']})")
                print(f"     Centroide: ({seg['centroide']['x']}, {seg['centroide']['y']})")
                print(f"     Área: {seg['area']}")
                print(f"     Dimensiones máscara: {seg['ancho_mascara']}x{seg['alto_mascara']}")
            
            print(f"\n⏱️  TIEMPOS:")
            print(f"   Captura:      {tiempo_captura:.2f} ms")
            print(f"   Segmentación: {tiempo_segmentacion:.2f} ms")
            print(f"   Total:        {tiempo_total:.2f} ms")
            
            return resultados
            
        except Exception as e:
            print(f"❌ Error en segmentación de piezas: {e}")
            return {"error": str(e)}
    
    def _guardar_por_modulos(self, resultados: Dict):
        """Guarda resultados por módulos en carpetas separadas"""
        try:
            self.contador_resultados += 1
            timestamp_captura = resultados.get("timestamp_captura", "unknown")
            
            # 1. Guardar clasificación (si existe)
            if "clasificacion" in resultados:
                self._guardar_clasificacion_modulo(resultados, timestamp_captura)
            
            # 2. Guardar detección de piezas (si existe)
            if "detecciones_piezas" in resultados:
                self._guardar_deteccion_piezas_modulo(resultados, timestamp_captura)
            
            # 3. Guardar detección de defectos (si existe)
            if "detecciones_defectos" in resultados:
                self._guardar_deteccion_defectos_modulo(resultados, timestamp_captura)
            
            # 4. Guardar segmentación de defectos (si existe)
            if "segmentaciones_defectos" in resultados:
                self._guardar_segmentacion_defectos_modulo(resultados, timestamp_captura)
            
            # 5. Guardar segmentación de piezas (si existe)
            if "segmentaciones_piezas" in resultados:
                self._guardar_segmentacion_piezas_modulo(resultados, timestamp_captura)
            
            print(f"✅ Resultados #{self.contador_resultados} guardados por módulos")
            
        except Exception as e:
            print(f"❌ Error guardando por módulos: {e}")
    
    def _guardar_clasificacion_modulo(self, resultados: Dict, timestamp_captura: str):
        """Guarda resultados de clasificación en su módulo específico"""
        try:
            # Crear imagen anotada
            frame_anotado = self.procesador_clasificacion.agregar_anotaciones_clasificacion(
                resultados["frame"],
                resultados["clasificacion"]["clase"],
                resultados["clasificacion"]["confianza"],
                resultados["tiempos"]["captura_ms"],
                resultados["tiempos"]["clasificacion_ms"]
            )
            
            # Guardar imagen en módulo de clasificación
            nombre_imagen = f"clasificacion_{timestamp_captura}_{self.contador_resultados}.jpg"
            ruta_imagen = os.path.join(self.directorios_salida["clasificacion"], nombre_imagen)
            cv2.imwrite(ruta_imagen, frame_anotado)
            
            # Crear metadatos usando estructura estándar
            metadatos_clasificacion = MetadataStandard.crear_metadatos_completos(
                tipo_analisis="clasificacion",
                archivo_imagen=nombre_imagen,
                resultados=resultados["clasificacion"],
                tiempos=resultados["tiempos"],
                timestamp_captura=timestamp_captura
            )
            
            nombre_json = f"clasificacion_{timestamp_captura}_{self.contador_resultados}.json"
            ruta_json = os.path.join(self.directorios_salida["clasificacion"], nombre_json)
            
            with open(ruta_json, 'w', encoding='utf-8') as f:
                json.dump(metadatos_clasificacion, f, indent=2, ensure_ascii=False)
            
            print(f"   📁 Clasificación guardada en: {self.directorios_salida['clasificacion']}")
            
        except Exception as e:
            print(f"❌ Error guardando clasificación: {e}")
    
    def _guardar_deteccion_piezas_modulo(self, resultados: Dict, timestamp_captura: str):
        """Guarda resultados de detección de piezas en su módulo específico"""
        try:
            # Guardar detección de piezas en módulo específico
            self.procesador_deteccion_piezas.procesar_deteccion_piezas(
                resultados["frame"],
                resultados["detecciones_piezas"],   
                resultados["tiempos"],
                self.directorios_salida["deteccion_piezas"],
                timestamp_captura
            )
            
            print(f"   📁 Detección de piezas guardada en: {self.directorios_salida['deteccion_piezas']}")
            
        except Exception as e:
            print(f"❌ Error guardando detección de piezas: {e}")
    
    def _guardar_deteccion_defectos_modulo(self, resultados: Dict, timestamp_captura: str):
        """Guarda resultados de detección de defectos en su módulo específico"""
        try:
            # Guardar detección de defectos en módulo específico
            self.procesador_deteccion_defectos.procesar_deteccion_defectos(
                resultados["frame"],
                resultados["detecciones_defectos"],
                resultados["tiempos"],
                self.directorios_salida["deteccion_defectos"],
                timestamp_captura
            )
            
            print(f"   📁 Detección de defectos guardada en: {self.directorios_salida['deteccion_defectos']}")
            
        except Exception as e:
            print(f"❌ Error guardando detección de defectos: {e}")
    
    def _guardar_segmentacion_defectos_modulo(self, resultados: Dict, timestamp_captura: str):
        """Guarda resultados de segmentación de defectos en su módulo específico"""
        try:
            # Guardar segmentación de defectos en módulo específico
            self.procesador_segmentacion_defectos.procesar_segmentacion_defectos(
                resultados["frame"],
                resultados["segmentaciones_defectos"],
                resultados["tiempos"],
                self.directorios_salida["segmentacion_defectos"],
                timestamp_captura
            )
            
            print(f"   📁 Segmentación de defectos guardada en: {self.directorios_salida['segmentacion_defectos']}")
            
        except Exception as e:
            print(f"❌ Error guardando segmentación de defectos: {e}")
    
    def _guardar_segmentacion_piezas_modulo(self, resultados: Dict, timestamp_captura: str):
        """Guarda resultados de segmentación de piezas en su módulo específico"""
        try:
            # Guardar segmentación de piezas en módulo específico
            self.procesador_segmentacion_piezas.procesar_segmentaciones(
                resultados["frame"],
                resultados["segmentaciones_piezas"],
                timestamp_captura
            )
            
            print(f"   📁 Segmentación de piezas guardada en: {self.directorios_salida['segmentacion_piezas']}")
            
        except Exception as e:
            print(f"❌ Error guardando segmentación de piezas: {e}")
    
    def obtener_estadisticas(self) -> Dict:
        """Retorna estadísticas del sistema"""
        if not self.inicializado:
            return {"error": "Sistema no inicializado"}
        
        # Determinar tipo de cámara y estadísticas
        if self.usando_webcam and self.webcam_fallback:
            camara_stats = self.webcam_fallback.obtener_estadisticas()
            camara_stats["tipo"] = "Webcam Fallback"
        elif self.camara:
            camara_stats = self.camara.obtener_estadisticas()
            camara_stats["tipo"] = "Cámara GigE"
        else:
            camara_stats = {"tipo": "No disponible"}
        
        stats = {
            "sistema": "Integrado (Clasificación + Detección de Piezas + Detección de Defectos + Segmentación de Defectos + Segmentación de Piezas)",
            "resultados_procesados": self.contador_resultados,
            "camara": camara_stats,
            "clasificador": {"inicializado": True} if self.clasificador else {},
            "detector_piezas": self.detector_piezas.obtener_estadisticas() if self.detector_piezas else {},
            "detector_defectos": self.detector_defectos.obtener_estadisticas() if self.detector_defectos else {},
            "segmentador_defectos": self.segmentador_defectos.obtener_estadisticas() if self.segmentador_defectos else {},
            "segmentador_piezas": self.segmentador_piezas.obtener_estadisticas() if self.segmentador_piezas else {}
        }
        
        return stats
    
    def liberar(self):
        """Libera todos los recursos del sistema"""
        try:
            print("🧹 Liberando recursos del sistema integrado...")
            
            if self.camara:
                self.camara.liberar()
            
            if self.webcam_fallback:
                self.webcam_fallback.liberar_recursos()
            
            if self.clasificador:
                self.clasificador.liberar()
            
            if self.detector_piezas:
                self.detector_piezas.liberar()
            
            if self.detector_defectos:
                self.detector_defectos.liberar()
            
            if self.segmentador_defectos:
                self.segmentador_defectos.liberar()
            
            if self.segmentador_piezas:
                self.segmentador_piezas.liberar()
            
            self.inicializado = False
            print("✅ Recursos del sistema integrado liberados")
            
        except Exception as e:
            print(f"❌ Error liberando recursos: {e}")
    
    def preprocesar_imagen_robusta(self, imagen: np.ndarray) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Preprocesa la imagen con técnicas de robustez ante iluminación
        
        Args:
            imagen (np.ndarray): Imagen de entrada (BGR)
            
        Returns:
            Tuple[np.ndarray, Dict[str, float]]: Imagen preprocesada y métricas de iluminación
        """
        try:
            print("🔧 Aplicando preprocesamiento robusto...")
            
            # Analizar iluminación
            metrics = self.robustez_iluminacion.analizar_iluminacion(imagen)
            print(f"   📊 Brillo: {metrics.get('brightness', 0):.1f}")
            print(f"   📊 Contraste: {metrics.get('contrast', 0):.1f}")
            
            # Obtener recomendaciones
            recommendations = self.robustez_iluminacion.recomendar_ajustes(imagen)
            
            # Aplicar preprocesamiento
            imagen_robusta = self.robustez_iluminacion.preprocesar_imagen_robusta(
                imagen,
                aplicar_clahe=recommendations.get('aplicar_clahe', True),
                aplicar_gamma=recommendations.get('aplicar_gamma', True),
                aplicar_contraste=recommendations.get('aplicar_contraste', True)
            )
            
            print("✅ Preprocesamiento robusto completado")
            return imagen_robusta, metrics
            
        except Exception as e:
            print(f"❌ Error en preprocesamiento robusto: {e}")
            return imagen, {}
    
    def obtener_umbrales_adaptativos(self, metrics: Dict[str, float], 
                                   detecciones_actuales: int = 0) -> Dict[str, float]:
        """
        Obtiene umbrales adaptativos basándose en las condiciones de iluminación
        
        Args:
            metrics (Dict[str, float]): Métricas de iluminación
            detecciones_actuales (int): Número de detecciones actuales
            
        Returns:
            Dict[str, float]: Umbrales adaptativos
        """
        try:
            brightness = metrics.get('brightness', 128.0)
            contrast = metrics.get('contrast', 50.0)
            
            # Obtener umbrales híbridos
            umbrales = self.umbrales_adaptativos.obtener_umbrales_hibridos(
                brightness, contrast, detecciones_actuales
            )
            
            print(f"   🎯 Umbrales adaptativos:")
            print(f"      Confianza: {umbrales['confianza_min']:.3f}")
            print(f"      Área mínima: {umbrales['area_minima']:.0f}")
            print(f"      Cobertura mínima: {umbrales['cobertura_minima']:.3f}")
            
            return umbrales
            
        except Exception as e:
            print(f"❌ Error obteniendo umbrales adaptativos: {e}")
            return {
                'confianza_min': 0.5,
                'area_minima': 500,
                'cobertura_minima': 0.1
            }
    
    def aplicar_configuracion_robustez(self, configuracion: str = "moderada"):
        """
        Aplica una configuración de robustez específica
        
        Args:
            configuracion (str): Tipo de configuración ('original', 'moderada', 'permisiva', 'ultra_permisiva')
        """
        try:
            # Obtener configuración
            if configuracion == "original":
                config = RobustezConfig.UMBRALES_ORIGINAL
            elif configuracion == "moderada":
                config = RobustezConfig.UMBRALES_MODERADA
            elif configuracion == "permisiva":
                config = RobustezConfig.UMBRALES_PERMISIVA
            elif configuracion == "ultra_permisiva":
                config = RobustezConfig.UMBRALES_ULTRA_PERMISIVA
            else:
                print(f"⚠️ Configuración '{configuracion}' no reconocida, usando moderada")
                config = RobustezConfig.UMBRALES_MODERADA
            
            print(f"🔧 Aplicando configuración de robustez: {config['descripcion']}")
            print(f"   Confianza mínima: {config['confianza_min']}")
            print(f"   IoU threshold: {config['iou_threshold']}")
            
            # Aplicar a detectores
            if self.detector_piezas:
                self.detector_piezas.actualizar_umbrales(
                    confianza_min=config['confianza_min'],
                    iou_threshold=config['iou_threshold']
                )
            
            if self.detector_defectos:
                self.detector_defectos.actualizar_umbrales(
                    confianza_min=config['confianza_min'],
                    iou_threshold=config['iou_threshold']
                )
            
            print("✅ Configuración de robustez aplicada correctamente")
            
        except Exception as e:
            print(f"❌ Error aplicando configuración de robustez: {e}")
    
    def configurar_robustez_automatica(self, imagen: np.ndarray = None):
        """
        Configura la robustez automáticamente basándose en las condiciones de iluminación
        
        Args:
            imagen (np.ndarray, optional): Imagen para analizar. Si no se proporciona, captura una nueva.
        """
        try:
            # Capturar imagen si no se proporciona
            if imagen is None:
                print("📸 Capturando imagen para análisis de robustez...")
                imagen = self.camara.capturar_frame()
                if imagen is None:
                    print("❌ Error capturando imagen, usando configuración por defecto")
                    self.aplicar_configuracion_robustez("moderada")
                    return
            
            # Analizar iluminación
            gray = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            contrast = np.std(gray)
            
            print(f"📊 Análisis de iluminación:")
            print(f"   Brillo: {brightness:.1f}")
            print(f"   Contraste: {contrast:.1f}")
            
            # Determinar configuración basándose en condiciones
            if brightness < 60 or contrast < 20:
                configuracion = "ultra_permisiva"
                print("   Condiciones: Muy difíciles")
            elif brightness < 100 or contrast < 30:
                configuracion = "permisiva"
                print("   Condiciones: Difíciles")
            elif brightness < 150:
                configuracion = "moderada"
                print("   Condiciones: Normales")
            else:
                configuracion = "original"
                print("   Condiciones: Buenas")
            
            # Aplicar configuración
            self.aplicar_configuracion_robustez(configuracion)
            
        except Exception as e:
            print(f"❌ Error en configuración automática de robustez: {e}")
            # Fallback a configuración moderada
            self.aplicar_configuracion_robustez("moderada")
