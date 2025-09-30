"""
Procesador de segmentación de piezas de coples
Maneja la visualización y guardado de resultados de segmentación de piezas
"""

import cv2
import numpy as np
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Agregar path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

# Importar configuración
from analisis_coples.expo_config import FileConfig, VisualizationConfig
from modules.postprocessing.mask_fusion import FusionadorMascaras
from modules.metadata_standard import MetadataStandard


class ProcesadorSegmentacionPiezas:
    """
    Procesador para segmentación de piezas de coples.
    
    Características:
    - Visualización de segmentaciones con máscaras
    - Guardado de imágenes y datos JSON
    - Generación de mapas de calor
    - Metadatos con dimensiones de máscaras
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Inicializa el procesador de segmentación de piezas.
        
        Args:
            output_dir (str, optional): Directorio de salida. Si no se proporciona, usa el por defecto.
        """
        self.output_dir = output_dir or os.path.join(FileConfig.OUTPUT_DIR, "Salida_seg_pz")
        self._crear_directorio_salida()
        
        # Colores para visualización
        self.colores = {
            'Cople': (0, 255, 255),  # Amarillo para piezas
            'default': (128, 128, 128)  # Gris por defecto
        }
        
        # Inicializar fusionador de máscaras
        self.fusionador = FusionadorMascaras()
        
        # Contador de archivos
        self.contador_archivos = 0
    
    def _crear_directorio_salida(self):
        """Crea el directorio de salida si no existe."""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            print(f"📁 Directorio de segmentación de piezas: {self.output_dir}")
        except Exception as e:
            print(f"⚠️ Error creando directorio de salida: {e}")
    
    def procesar_segmentaciones(self, imagen: np.ndarray, segmentaciones: List[Dict], 
                               timestamp: Optional[str] = None, tiempos: Optional[Dict] = None) -> Dict:
        """
        Procesa las segmentaciones de piezas y genera visualizaciones.
        
        Args:
            imagen (np.ndarray): Imagen original
            segmentaciones (List[Dict]): Lista de segmentaciones detectadas
            timestamp (str, optional): Timestamp para nombres de archivo
            tiempos (Dict, optional): Diccionario con tiempos de procesamiento
            
        Returns:
            Dict: Información de los archivos generados
        """
        try:
            if timestamp is None:
                timestamp = datetime.now().strftime(FileConfig.TIMESTAMP_FORMAT)
            
            self.contador_archivos += 1
            
            # Debug de segmentaciones recibidas
            print(f"🔍 DEBUG PROCESADOR PIEZAS: Recibidas {len(segmentaciones)} segmentaciones")
            for i, seg in enumerate(segmentaciones):
                mascara_presente = 'mascara' in seg and seg['mascara'] is not None
                print(f"   ✅ Segmentación {i}: Máscara presente: {mascara_presente}, "
                      f"tipo: {type(seg.get('mascara', None))}, elementos: {type(seg.get('mascara', None))}")
            
            # Verificar consistencia de máscaras
            self._verificar_consistencia_mascaras(segmentaciones)
            
            # Aplicar fusión de máscaras para objetos pegados
            print("🔗 Aplicando fusión de máscaras para objetos pegados...")
            segmentaciones_procesadas = self.fusionador.procesar_segmentaciones(segmentaciones)
            
            # Crear visualización con segmentaciones procesadas
            imagen_visualizacion = self._crear_visualizacion(imagen, segmentaciones_procesadas)
            
            # Crear mapa de calor
            mapa_calor = self._crear_mapa_calor(imagen, segmentaciones)
            
            # Generar nombres de archivo
            nombre_base = f"cople_segmentacion_piezas_{timestamp}"
            archivo_imagen = os.path.join(self.output_dir, f"{nombre_base}.jpg")
            archivo_json = os.path.join(self.output_dir, f"{nombre_base}.json")
            archivo_heatmap = os.path.join(self.output_dir, f"{nombre_base}_heatmap.jpg")
            
            # Guardar archivos
            cv2.imwrite(archivo_imagen, imagen_visualizacion)
            self._guardar_json(archivo_json, segmentaciones_procesadas, timestamp, tiempos)
            cv2.imwrite(archivo_heatmap, mapa_calor)
            
            print(f"✅ Imagen guardada: {archivo_imagen}")
            print(f"✅ JSON guardado: {archivo_json}")
            print(f"   📁 Segmentación de piezas guardada en: {self.output_dir}")
            
            return {
                'imagen': archivo_imagen,
                'json': archivo_json,
                'heatmap': archivo_heatmap,
                'timestamp': timestamp,
                'contador': self.contador_archivos
            }
            
        except Exception as e:
            print(f"❌ Error procesando segmentaciones de piezas: {e}")
            return {}
    
    def _verificar_consistencia_mascaras(self, segmentaciones: List[Dict]):
        """
        Verifica la consistencia de las máscaras de segmentación.
        
        Args:
            segmentaciones (List[Dict]): Lista de segmentaciones
        """
        print(f"\n🔍 VERIFICANDO CONSISTENCIA DE MÁSCARAS DE PIEZAS:")
        print("=" * 50)
        
        for i, seg in enumerate(segmentaciones):
            try:
                print(f"\nSegmentación {i}:")
                
                # Verificar campos básicos
                campos_requeridos = ['clase', 'confianza', 'bbox', 'centroide', 'area', 'area_mascara', 'mascara']
                for campo in campos_requeridos:
                    if campo in seg:
                        print(f"   ✅ {campo}: {seg[campo]}")
                    else:
                        print(f"   ❌ {campo}: FALTANTE")
                
                # Verificar máscara
                if 'mascara' in seg and seg['mascara'] is not None:
                    mascara = seg['mascara']
                    if isinstance(mascara, np.ndarray):
                        print(f"   ✅ mascara: numpy array {mascara.shape}")
                        
                        # Verificar consistencia de áreas
                        if 'area' in seg and 'area_mascara' in seg:
                            area_bbox = seg['area']
                            area_mascara = seg['area_mascara']
                            if area_bbox > 0:
                                ratio = area_mascara / area_bbox
                                print(f"   ⚠️  Inconsistencia de áreas: bbox={area_bbox}, mask={area_mascara}, ratio={ratio:.2f}")
                    else:
                        print(f"   ❌ mascara: Tipo incorrecto {type(mascara)}")
                else:
                    print(f"   ❌ mascara: AUSENTE")
                
                # Verificar dimensiones de máscara
                if 'alto_mascara' in seg and 'ancho_mascara' in seg:
                    print(f"   ✅ Dimensiones máscara: {seg['ancho_mascara']}x{seg['alto_mascara']}")
                else:
                    print(f"   ⚠️  Dimensiones máscara: NO DISPONIBLES")
                    
            except Exception as e:
                print(f"   ❌ Error verificando segmentación {i}: {e}")
    
    def _crear_visualizacion(self, imagen: np.ndarray, segmentaciones: List[Dict]) -> np.ndarray:
        """
        Crea la visualización de las segmentaciones de piezas.
        
        Args:
            imagen (np.ndarray): Imagen original
            segmentaciones (List[Dict]): Lista de segmentaciones
            
        Returns:
            np.ndarray: Imagen con visualización
        """
        try:
            # Copiar imagen original
            imagen_vis = imagen.copy()
            
            print(f"🎨 Dibujando {len(segmentaciones)} segmentaciones de piezas...")
            
            for i, seg in enumerate(segmentaciones):
                try:
                    # Obtener información de la segmentación
                    clase = seg.get('clase', 'Cople')
                    confianza = seg.get('confianza', 0.0)
                    bbox = seg.get('bbox', {})
                    mascara = seg.get('mascara')
                    
                    # Obtener color
                    color = self.colores.get(clase, self.colores['default'])
                    
                    # Dibujar bbox
                    if bbox:
                        x1, y1 = bbox.get('x1', 0), bbox.get('y1', 0)
                        x2, y2 = bbox.get('x2', 0), bbox.get('y2', 0)
                        
                        # Dibujar rectángulo
                        cv2.rectangle(imagen_vis, (x1, y1), (x2, y2), color, 2)
                        
                        # Dibujar etiqueta
                        etiqueta = f"{clase} {confianza:.2f}"
                        (text_w, text_h), _ = cv2.getTextSize(etiqueta, VisualizationConfig.FONT, 
                                                             VisualizationConfig.FONT_SCALE, 
                                                             VisualizationConfig.FONT_THICKNESS)
                        
                        # Fondo para el texto
                        cv2.rectangle(imagen_vis, (x1, y1 - text_h - 10), 
                                    (x1 + text_w, y1), color, -1)
                        
                        # Texto
                        cv2.putText(imagen_vis, etiqueta, (x1, y1 - 5), 
                                  VisualizationConfig.FONT, VisualizationConfig.FONT_SCALE, 
                                  VisualizationConfig.TEXT_COLOR, VisualizationConfig.FONT_THICKNESS)
                        
                        print(f"🎨 Dibujando segmentación {i+1}: {clase} en ({x1},{y1}) a ({x2},{y2})")
                    
                    # Dibujar máscara si está disponible
                    if mascara is not None and isinstance(mascara, np.ndarray):
                        self._dibujar_mascara(imagen_vis, mascara, color, alpha=0.3)
                    
                except Exception as e:
                    print(f"⚠️ Error dibujando segmentación {i}: {e}")
                    continue
            
            return imagen_vis
            
        except Exception as e:
            print(f"❌ Error creando visualización: {e}")
            return imagen
    
    def _dibujar_mascara(self, imagen: np.ndarray, mascara: np.ndarray, color: Tuple[int, int, int], alpha: float = 0.3):
        """
        Dibuja una máscara sobre la imagen con transparencia.
        
        Args:
            imagen (np.ndarray): Imagen sobre la que dibujar
            mascara (np.ndarray): Máscara a dibujar
            color (Tuple[int, int, int]): Color en formato BGR
            alpha (float): Transparencia (0.0 a 1.0)
        """
        try:
            # Crear máscara binaria
            mascara_binaria = (mascara > 0.5).astype(np.uint8)
            
            # Crear overlay de color
            overlay = imagen.copy()
            overlay[mascara_binaria > 0] = color
            
            # Combinar con transparencia
            cv2.addWeighted(overlay, alpha, imagen, 1 - alpha, 0, imagen)
            
        except Exception as e:
            print(f"⚠️ Error dibujando máscara: {e}")
    
    def _crear_mapa_calor(self, imagen: np.ndarray, segmentaciones: List[Dict]) -> np.ndarray:
        """
        Crea un mapa de calor combinando todas las máscaras.
        
        Args:
            imagen (np.ndarray): Imagen original
            segmentaciones (List[Dict]): Lista de segmentaciones
            
        Returns:
            np.ndarray: Mapa de calor
        """
        try:
            # Crear mapa de calor base
            mapa_calor = np.zeros(imagen.shape[:2], dtype=np.float32)
            
            print(f"🎨 Dibujando {len(segmentaciones)} máscaras...")
            
            for i, seg in enumerate(segmentaciones):
                try:
                    mascara = seg.get('mascara')
                    if mascara is not None and isinstance(mascara, np.ndarray):
                        print(f"   📐 Máscara {i}: {mascara.shape}, rango: [{np.min(mascara):.3f}, {np.max(mascara):.3f}]")
                        
                        # Agregar máscara al mapa de calor
                        mascara_binaria = (mascara > 0.5).astype(np.float32)
                        mapa_calor += mascara_binaria
                        
                        pixels_activos = np.sum(mascara_binaria)
                        print(f"   ✅ Máscara {i}: {pixels_activos} píxeles activos")
                    else:
                        print(f"   ⚠️ Máscara {i}: No disponible")
                        
                except Exception as e:
                    print(f"⚠️ Error procesando máscara {i}: {e}")
                    continue
            
            # Normalizar mapa de calor
            if np.max(mapa_calor) > 0:
                mapa_calor = mapa_calor / np.max(mapa_calor)
            
            # Convertir a imagen de color
            mapa_calor_color = cv2.applyColorMap((mapa_calor * 255).astype(np.uint8), cv2.COLORMAP_JET)
            
            # Combinar con imagen original
            resultado = cv2.addWeighted(imagen, 0.6, mapa_calor_color, 0.4, 0)
            
            print(f"   💾 Mapa de calor guardado: {len(segmentaciones)} segmentaciones combinadas")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Error creando mapa de calor: {e}")
            return imagen
    
    def _guardar_json(self, archivo_json: str, segmentaciones: List[Dict], timestamp: str, tiempos: Optional[Dict] = None):
        """
        Guarda las segmentaciones en formato JSON con metadatos usando estructura estándar.
        
        Args:
            archivo_json (str): Ruta del archivo JSON
            segmentaciones (List[Dict]): Lista de segmentaciones
            timestamp (str): Timestamp de la captura
            tiempos (Dict, optional): Diccionario con tiempos de procesamiento
        """
        try:
            # Crear metadatos usando estructura estándar
            metadatos = MetadataStandard.crear_metadatos_completos(
                tipo_analisis="segmentacion_piezas",
                archivo_imagen=os.path.basename(archivo_json).replace('.json', '.jpg'),
                resultados=segmentaciones,
                tiempos=tiempos or {},  # Usar tiempos proporcionados o diccionario vacío
                timestamp_captura=timestamp
            )
            
            # Guardar archivo JSON usando el método estándar
            MetadataStandard.guardar_metadatos(metadatos, archivo_json)
            
        except Exception as e:
            print(f"❌ Error guardando JSON: {e}")
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene las estadísticas del procesador.
        
        Returns:
            Dict: Estadísticas del procesador
        """
        return {
            'archivos_procesados': self.contador_archivos,
            'directorio_salida': self.output_dir
        }
