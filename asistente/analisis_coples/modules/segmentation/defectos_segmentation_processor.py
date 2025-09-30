"""
Procesador de Segmentación de Defectos
Maneja la visualización y análisis de segmentaciones de defectos
"""

import numpy as np
import cv2
from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime
import os
import sys

# Agregar path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from modules.metadata_standard import MetadataStandard
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap


class ProcesadorSegmentacionDefectos:
    """
    Procesador para segmentaciones de defectos de coples.
    
    Características:
    - Visualización de máscaras de segmentación
    - Dibujo de contornos y bounding boxes
    - Anotación de información de confianza
    - Guardado de resultados en JPG y JSON
    """
    
    def __init__(self):
        """Inicializa el procesador de segmentación de defectos."""
        # Colores para diferentes clases de defectos
        self.colores_defectos = {
            "Defecto_Seg_1": (0, 0, 255),      # Rojo
            "Defecto_Seg_2": (0, 255, 255),    # Amarillo
            "Defecto_Seg_3": (255, 0, 255),    # Magenta
            "Defecto_Seg_4": (0, 255, 0),      # Verde
            "Defecto_Seg_5": (255, 165, 0),    # Naranja
            "Defecto_Seg_6": (128, 0, 128),    # Púrpura
            "Defecto_Seg_7": (255, 192, 203),  # Rosa
            "Defecto_Seg_8": (0, 128, 128),    # Verde azulado
            "default": (255, 0, 0)             # Azul por defecto
        }
        
        # Configuración de visualización
        self.grosor_linea = 2
        self.tamano_fuente = 0.6
        self.espesor_fuente = 1
        self.margen_texto = 5
        self.alpha_overlay = 0.3  # Transparencia del overlay de segmentación
        
        # Visualizador avanzado de máscaras
        self.mask_visualizer = MaskVisualizer()
    
    def dibujar_segmentaciones(self, imagen: np.ndarray, segmentaciones: List[Dict]) -> np.ndarray:
        """
        Dibuja las segmentaciones en la imagen
        
        Args:
            imagen: Imagen original
            segmentaciones: Lista de segmentaciones detectadas
            
        Returns:
            Imagen con segmentaciones dibujadas
        """
        imagen_anotada = imagen.copy()
        print(f"🎨 Dibujando {len(segmentaciones)} segmentaciones...")
        
        for i, segmentacion in enumerate(segmentaciones):
            try:
                bbox = segmentacion["bbox"]
                clase = segmentacion["clase"]
                confianza = segmentacion["confianza"]
                centroide = segmentacion["centroide"]
                
                # Validar que exista el campo contorno
                if "contorno" not in segmentacion:
                    print(f"⚠️ Segmentación {i} no tiene campo contorno, usando bbox")
                    # Crear contorno simple desde bbox
                    x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
                    contorno = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]], dtype=np.int32)
                else:
                    contorno = np.array(segmentacion["contorno"], dtype=np.int32)
                
                x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
                
                # Validar coordenadas
                if x1 >= x2 or y1 >= y2:
                    print(f"⚠️ Bounding box inválido para segmentación {i}: ({x1},{y1}) a ({x2},{y2})")
                    continue
                    
                if x1 < 0 or y1 < 0 or x2 > imagen.shape[1] or y2 > imagen.shape[0]:
                    print(f"⚠️ Bounding box fuera de imagen para segmentación {i}: ({x1},{y1}) a ({x2},{y2})")
                    continue
                
                print(f"🎨 Dibujando segmentación {i+1}: {clase} en ({x1},{y1}) a ({x2},{y2})")
                
                # Obtener color para la clase
                color = self.colores_defectos.get(clase, self.colores_defectos["default"])
                
                # Dibujar contorno de segmentación (DESHABILITADO temporalmente para evitar crash)
                # try:
                #     if len(contorno) > 0 and contorno.shape[0] >= 3:
                #         # Solo dibujar contorno si es válido
                #         cv2.drawContours(imagen_anotada, [contorno], -1, color, self.grosor_linea)
                # except Exception as e:
                #     print(f"⚠️ Error dibujando contorno para segmentación {i}: {e}")
                #     # Continuar sin contorno
                pass  # Contornos deshabilitados temporalmente
                
                # Dibujar bounding box
                cv2.rectangle(imagen_anotada, (x1, y1), (x2, y2), color, self.grosor_linea)
                
                # Dibujar centroide
                cx, cy = int(centroide["x"]), int(centroide["y"])
                cv2.circle(imagen_anotada, (cx, cy), 3, color, -1)
                
                # Dibujar etiqueta de clase y confianza
                confianza_porcentaje = min(confianza, 1.0) * 100
                texto_etiqueta = f"{clase}: {confianza_porcentaje:.1f}%"
                
                (texto_ancho, texto_alto), _ = cv2.getTextSize(
                    texto_etiqueta, cv2.FONT_HERSHEY_SIMPLEX, self.tamano_fuente, self.espesor_fuente
                )
                
                texto_x = x1
                texto_y = y1 - self.margen_texto
                
                if texto_y < texto_alto + self.margen_texto:
                    texto_y = y2 + texto_alto + self.margen_texto
                
                # Fondo para el texto
                cv2.rectangle(
                    imagen_anotada,
                    (texto_x - 2, texto_y - texto_alto - 2),
                    (texto_x + texto_ancho + 2, texto_y + 2),
                    color, -1
                )
                
                # Texto
                cv2.putText(
                    imagen_anotada, texto_etiqueta, (texto_x, texto_y),
                    cv2.FONT_HERSHEY_SIMPLEX, self.tamano_fuente, (255, 255, 255), self.espesor_fuente
                )
                
            except Exception as e:
                print(f"⚠️ Error procesando segmentación {i}: {e}")
                continue
        
        return imagen_anotada
    
    def crear_overlay_segmentacion(self, imagen: np.ndarray, segmentaciones: List[Dict]) -> np.ndarray:
        """
        Crea un overlay de segmentación con máscaras semitransparentes
        
        Args:
            imagen: Imagen original
            segmentaciones: Lista de segmentaciones detectadas
            
        Returns:
            Imagen con overlay de segmentación
        """
        imagen_overlay = imagen.copy()
        
        for segmentacion in segmentaciones:
            clase = segmentacion["clase"]
            contorno = np.array(segmentacion["contorno"])
            color = self.colores_defectos.get(clase, self.colores_defectos["default"])
            
            if len(contorno) > 0:
                # Crear máscara para esta segmentación
                mascara = np.zeros(imagen.shape[:2], dtype=np.uint8)
                cv2.fillPoly(mascara, [contorno], 255)
                
                # Aplicar overlay semitransparente
                overlay = np.zeros_like(imagen)
                overlay[mascara > 0] = color
                
                # Combinar con transparencia
                cv2.addWeighted(imagen_overlay, 1.0, overlay, self.alpha_overlay, 0, imagen_overlay)
        
        return imagen_overlay
    
    def agregar_informacion_tiempo(self, imagen: np.ndarray, tiempos: Dict) -> np.ndarray:
        """
        Agrega información de tiempos a la imagen
        
        Args:
            imagen: Imagen a anotar
            tiempos: Diccionario con tiempos de procesamiento
            
        Returns:
            Imagen con información de tiempos
        """
        imagen_anotada = imagen.copy()
        
        info_tiempos = [
            f"Captura: {tiempos.get('captura_ms', 0):.2f} ms",
            f"Segmentación: {tiempos.get('segmentacion_ms', 0):.2f} ms",
            f"Total: {tiempos.get('total_ms', 0):.2f} ms"
        ]
        
        pos_x = imagen.shape[1] - 200
        pos_y = 30
        
        for i, info in enumerate(info_tiempos):
            # Fondo para el texto
            cv2.rectangle(
                imagen_anotada,
                (pos_x - 5, pos_y + i * 20 - 15),
                (pos_x + 190, pos_y + i * 20 + 5),
                (0, 0, 0), -1
            )
            
            # Texto
            cv2.putText(
                imagen_anotada, info, (pos_x, pos_y + i * 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
            )
        
        return imagen_anotada
    
    def crear_metadatos_segmentacion(self, segmentaciones: List[Dict], tiempos: Dict, 
                                   nombre_archivo: str, modelo: str) -> Dict:
        """
        Crea metadatos para la segmentación usando estructura estándar
        
        Args:
            segmentaciones: Lista de segmentaciones detectadas
            tiempos: Diccionario con tiempos de procesamiento
            nombre_archivo: Nombre del archivo de imagen
            modelo: Nombre del modelo utilizado
            
        Returns:
            Diccionario con metadatos de segmentación
        """
        # Usar estructura estándar de metadatos
        metadatos = MetadataStandard.crear_metadatos_completos(
            tipo_analisis="segmentacion_defectos",
            archivo_imagen=nombre_archivo,
            resultados=segmentaciones,
            tiempos=tiempos
        )
        
        return metadatos
    
    def guardar_resultado_segmentacion(self, imagen: np.ndarray, segmentaciones: List[Dict], 
                                     tiempos: Dict, directorio_salida: str, 
                                     prefijo: str = "cople_segmentacion_defectos",
                                     timestamp_captura: str = None) -> Tuple[str, str]:
        """
        Guarda el resultado de la segmentación
        
        Args:
            imagen: Imagen con segmentaciones dibujadas
            segmentaciones: Lista de segmentaciones detectadas
            tiempos: Diccionario con tiempos de procesamiento
            directorio_salida: Directorio donde guardar los resultados
            prefijo: Prefijo para los nombres de archivo
            timestamp_captura: Timestamp de la captura (opcional)
            
        Returns:
            Tupla con rutas de imagen y JSON guardados
        """
        try:
            # Crear nombre base del archivo
            if timestamp_captura:
                nombre_base = f"{prefijo}_{timestamp_captura}"
            else:
                nombre_base = f"{prefijo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Validar imagen antes de guardar
            if imagen is None or imagen.size == 0:
                print("⚠️ Imagen inválida, creando imagen de fallback")
                imagen = np.zeros((640, 640, 3), dtype=np.uint8)
            
            # Verificar tipo de imagen
            if imagen.dtype != np.uint8:
                try:
                    imagen = (imagen * 255).astype(np.uint8)
                except Exception as e:
                    print(f"⚠️ Error convirtiendo imagen a uint8: {e}")
                    imagen = np.zeros((640, 640, 3), dtype=np.uint8)
            
            # Guardar imagen con manejo de errores
            nombre_imagen = f"{nombre_base}.jpg"
            ruta_imagen = os.path.join(directorio_salida, nombre_imagen)
            
            try:
                # Crear directorio si no existe
                os.makedirs(directorio_salida, exist_ok=True)
                
                # Guardar imagen
                resultado_imagen = cv2.imwrite(ruta_imagen, imagen)
                if not resultado_imagen:
                    print("⚠️ Error en cv2.imwrite, usando método alternativo")
                    # Fallback: convertir a PIL y guardar
                    from PIL import Image
                    imagen_pil = Image.fromarray(imagen)
                    imagen_pil.save(ruta_imagen, "JPEG", quality=95)
                
                print(f"✅ Imagen guardada: {ruta_imagen}")
                
            except Exception as e:
                print(f"⚠️ Error guardando imagen: {e}")
                # Crear imagen de fallback
                imagen_fallback = np.zeros((640, 640, 3), dtype=np.uint8)
                cv2.putText(imagen_fallback, "Error en imagen", (200, 320), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.imwrite(ruta_imagen, imagen_fallback)
            
            # Crear y guardar metadatos
            try:
                metadatos = self.crear_metadatos_segmentacion(
                    segmentaciones, tiempos, nombre_imagen, "CopleSegDef1C8V.onnx"
                )
                
                nombre_json = f"{nombre_base}.json"
                ruta_json = os.path.join(directorio_salida, nombre_json)
                
                with open(ruta_json, 'w', encoding='utf-8') as f:
                    json.dump(metadatos, f, indent=2, ensure_ascii=False)
                
                print(f"✅ JSON guardado: {ruta_json}")
                
            except Exception as e:
                print(f"⚠️ Error guardando JSON: {e}")
                # Crear JSON de fallback
                metadatos_fallback = {
                    "archivo_imagen": nombre_imagen,
                    "error": "Error creando metadatos",
                    "timestamp": datetime.now().isoformat()
                }
                nombre_json = f"{nombre_base}_error.json"
                ruta_json = os.path.join(directorio_salida, nombre_json)
                with open(ruta_json, 'w', encoding='utf-8') as f:
                    json.dump(metadatos_fallback, f, indent=2, ensure_ascii=False)
            
            return ruta_imagen, ruta_json
            
        except Exception as e:
            print(f"❌ Error crítico guardando resultado de segmentación: {e}")
            return "", ""
    
    def procesar_segmentacion_defectos(self, imagen: np.ndarray, segmentaciones: List[Dict], 
                                     tiempos: Dict, directorio_salida: str, 
                                     timestamp_captura: str = None) -> Tuple[str, str]:
        """
        Procesa completamente la segmentación de defectos
        
        Args:
            imagen: Imagen original
            segmentaciones: Lista de segmentaciones detectadas
            tiempos: Diccionario con tiempos de procesamiento
            directorio_salida: Directorio donde guardar los resultados
            timestamp_captura: Timestamp de la captura (opcional)
            
        Returns:
            Tupla con rutas de imagen y JSON guardados
        """
        # Debug detallado de máscaras
        print(f"\n🔍 DEBUG PROCESADOR: Recibidas {len(segmentaciones)} segmentaciones")
        for i, seg in enumerate(segmentaciones):
            if 'mascara' in seg and seg['mascara'] is not None:
                print(f"   ✅ Segmentación {i}: Máscara presente, tipo: {type(seg['mascara'])}, elementos: {len(seg['mascara']) if isinstance(seg['mascara'], list) else 'numpy array'}")
            else:
                print(f"   ❌ Segmentación {i}: Máscara ausente o None")
        
        # NUEVO: Verificar consistencia antes del procesamiento (sin timeout)
        try:
            self.mask_visualizer.verificar_consistencia_mascaras(segmentaciones)
        except Exception as e:
            print(f"   ⚠️ Error en verificación de consistencia: {e}")
        
        try:
            self.mask_visualizer.debug_mask_info(segmentaciones)
        except Exception as e:
            print(f"   ⚠️ Error en debug de máscaras: {e}")
        
        # Visualización avanzada de máscaras (sin timeout)
        try:
            imagen_con_mascaras = self.mask_visualizer.visualizar_mascaras_completo(
                imagen, segmentaciones, mostrar=False
            )
        except Exception as e:
            print(f"   ⚠️ Error en visualización de máscaras: {e}")
            imagen_con_mascaras = None
        
        # Si no hay máscaras válidas, usar visualización básica
        if imagen_con_mascaras is None or np.array_equal(imagen_con_mascaras, imagen):
            print("   ⚠️  Usando visualización básica (sin máscaras)")
            imagen_anotada = self.dibujar_segmentaciones(imagen, segmentaciones)
        else:
            imagen_anotada = imagen_con_mascaras
        
        # Agregar información de tiempos
        imagen_anotada = self.agregar_informacion_tiempo(imagen_anotada, tiempos)
        
        # Crear mapa de calor si hay máscaras válidas (sin timeout)
        try:
            mapa_calor = self.mask_visualizer.crear_mapa_calor_masks(segmentaciones, imagen.shape[:2])
            imagen_heatmap = self.mask_visualizer.visualizar_mapa_calor(imagen, mapa_calor)
            
            # Guardar mapa de calor
            if timestamp_captura:
                nombre_heatmap = f"cople_segmentacion_defectos_heatmap_{timestamp_captura}.jpg"
            else:
                nombre_heatmap = f"cople_segmentacion_defectos_heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            
            ruta_heatmap = os.path.join(directorio_salida, nombre_heatmap)
            cv2.imwrite(ruta_heatmap, imagen_heatmap)
            print(f"   💾 Mapa de calor guardado: {ruta_heatmap}")
            
        except Exception as e:
            print(f"   ⚠️  Error creando mapa de calor: {e}")
        
        # Guardar resultado principal
        return self.guardar_resultado_segmentacion(
            imagen_anotada, segmentaciones, tiempos, directorio_salida,
            "cople_segmentacion_defectos", timestamp_captura
        )


class MaskVisualizer:
    def __init__(self):
        self.colors = [
            (255, 0, 0),    # Rojo
            (0, 255, 0),    # Verde  
            (0, 0, 255),    # Azul
            (255, 255, 0),  # Amarillo
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cian
            (128, 0, 128),  # Púrpura
            (255, 165, 0),  # Naranja
        ]
    
    def visualizar_mascaras_completo(self, imagen: np.ndarray, segmentaciones: List[Dict], 
                                   save_path: str = None, mostrar: bool = False) -> np.ndarray:
        """
        Visualización completa de máscaras con múltiples opciones
        """
        if not segmentaciones:
            print("   ⚠️  No hay segmentaciones para visualizar")
            return imagen.copy()
        
        resultado = imagen.copy()
        
        print(f"🎨 Dibujando {len(segmentaciones)} máscaras...")
        
        for i, seg in enumerate(segmentaciones):
            color = self.colors[i % len(self.colors)]
            
            # 1. VERIFICAR DATOS DE LA MÁSCARA (CORREGIDO)
            mask_data = seg.get('mascara')  # ← CAMBIO: 'mask' por 'mascara'
            if mask_data is None:
                print(f"   ⚠️  Segmentación {i}: Sin datos de máscara")
                continue
            
            # 2. CONVERTIR MÁSCARA A NUMPY
            if isinstance(mask_data, list):
                mask = np.array(mask_data, dtype=np.float32)
            else:
                mask = mask_data.astype(np.float32)
            
            # 3. VERIFICAR DIMENSIONES
            print(f"   📐 Máscara {i}: {mask.shape}, rango: [{mask.min():.3f}, {mask.max():.3f}]")
            
            if len(mask.shape) != 2:
                print(f"   ❌ Máscara {i}: Dimensiones incorrectas {mask.shape}")
                continue
            
            # 4. REDIMENSIONAR SI ES NECESARIO
            if mask.shape != imagen.shape[:2]:
                print(f"   🔄 Redimensionando máscara de {mask.shape} a {imagen.shape[:2]}")
                mask = cv2.resize(mask, (imagen.shape[1], imagen.shape[0]))
            
            # 5. BINARIZAR MÁSCARA
            mask_binary = (mask > 0.5).astype(np.uint8)
            
            # 6. VERIFICAR SI LA MÁSCARA TIENE CONTENIDO
            pixels_activos = np.sum(mask_binary)
            if pixels_activos == 0:
                print(f"   ⚠️  Máscara {i}: Sin píxeles activos después de binarizar")
                continue
            
            print(f"   ✅ Máscara {i}: {pixels_activos} píxeles activos")
            
            # 7. APLICAR MÚLTIPLES TÉCNICAS DE VISUALIZACIÓN
            resultado = self._aplicar_overlay(resultado, mask_binary, color, seg, i)
        
        # 8. GUARDAR RESULTADO
        if save_path:
            cv2.imwrite(save_path, resultado)
            print(f"   💾 Imagen con máscaras guardada: {save_path}")
        
        # 9. MOSTRAR SI SE REQUIERE
        if mostrar:
            self._mostrar_resultado(imagen, resultado, segmentaciones)
        
        return resultado
    
    def _aplicar_overlay(self, imagen: np.ndarray, mask_binary: np.ndarray, 
                        color: Tuple[int, int, int], seg: Dict, index: int) -> np.ndarray:
        """
        Aplica overlay de máscara con múltiples técnicas
        """
        resultado = imagen.copy()
        
        # TÉCNICA 1: Overlay semitransparente
        overlay = resultado.copy()
        overlay[mask_binary > 0] = color
        resultado = cv2.addWeighted(resultado, 0.7, overlay, 0.3, 0)
        
        # TÉCNICA 2: Contornos de la máscara
        contornos, _ = cv2.findContours(mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(resultado, contornos, -1, color, 2)
        
        # TÉCNICA 3: Bounding box
        bbox = seg.get('bbox', {})
        if bbox:
            x1, y1, x2, y2 = bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']
            cv2.rectangle(resultado, (x1, y1), (x2, y2), color, 2)
            
            # TÉCNICA 4: Etiquetas con información
            label = f"{seg.get('clase', 'Unknown')} {seg.get('confianza', 0):.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            cv2.rectangle(resultado, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            cv2.putText(resultado, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # TÉCNICA 5: Centroide
        centroide = seg.get('centroide', {})
        if centroide:
            cx, cy = centroide['x'], centroide['y']
            cv2.circle(resultado, (cx, cy), 5, color, -1)
            cv2.circle(resultado, (cx, cy), 8, (255, 255, 255), 2)
        
        return resultado
    
    def _mostrar_resultado(self, original: np.ndarray, resultado: np.ndarray, segmentaciones: List[Dict]):
        """
        Muestra comparativa con matplotlib
        """
        try:
            fig, axes = plt.subplots(1, 2, figsize=(15, 7))
            
            # Imagen original
            axes[0].imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
            axes[0].set_title('Imagen Original')
            axes[0].axis('off')
            
            # Imagen con máscaras
            axes[1].imshow(cv2.cvtColor(resultado, cv2.COLOR_BGR2RGB))
            axes[1].set_title(f'Con Máscaras ({len(segmentaciones)} detectadas)')
            axes[1].axis('off')
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            print(f"   ⚠️  Error mostrando con matplotlib: {e}")
    
    def debug_mask_info(self, segmentaciones: List[Dict]) -> None:
        """
        Debug detallado de la información de máscaras
        """
        print(f"\n🔍 DEBUGGING {len(segmentaciones)} MÁSCARAS:")
        print("=" * 60)
        
        for i, seg in enumerate(segmentaciones):
            print(f"\n📊 MÁSCARA {i}:")
            print(f"   Clase: {seg.get('clase', 'N/A')}")
            print(f"   Confianza: {seg.get('confianza', 0):.3f}")
            
            # Info de bbox
            bbox = seg.get('bbox', {})
            if bbox:
                w = bbox.get('x2', 0) - bbox.get('x1', 0)
                h = bbox.get('y2', 0) - bbox.get('y1', 0)
                print(f"   BBox: ({bbox.get('x1', 0)}, {bbox.get('y1', 0)}) -> ({bbox.get('x2', 0)}, {bbox.get('y2', 0)})")
                print(f"   Tamaño BBox: {w} x {h} = {w*h} píxeles")
            
            # Info de áreas
            area_bbox = seg.get('area', 0)
            area_mask = seg.get('area_mascara', 0)
            print(f"   Área BBox: {area_bbox}")
            print(f"   Área Máscara: {area_mask}")
            
            if area_bbox > 0:
                cobertura = (area_mask / area_bbox) * 100
                print(f"   Cobertura: {cobertura:.1f}%")
            
            # Info de máscara (CORREGIDO)
            mask_data = seg.get('mascara')  # ← CAMBIO: 'mask' por 'mascara'
            if mask_data is not None:
                if isinstance(mask_data, list):
                    mask = np.array(mask_data)
                else:
                    mask = mask_data
                
                print(f"   Máscara shape: {mask.shape}")
                print(f"   Máscara rango: [{mask.min():.3f}, {mask.max():.3f}]")
                print(f"   Píxeles únicos: {len(np.unique(mask))}")
                
                if len(mask.shape) == 2:
                    pixels_positivos = np.sum(mask > 0.5)
                    total_pixels = mask.shape[0] * mask.shape[1]
                    print(f"   Píxeles activos: {pixels_positivos}/{total_pixels} ({pixels_positivos/total_pixels*100:.1f}%)")
            else:
                print("   ❌ Sin datos de máscara")
    
    def crear_mapa_calor_masks(self, segmentaciones: List[Dict], shape: Tuple[int, int]) -> np.ndarray:
        """
        Crea un mapa de calor combinando todas las máscaras
        """
        mapa_calor = np.zeros(shape, dtype=np.float32)
        
        for seg in segmentaciones:
            mask_data = seg.get('mascara')  # ← CAMBIO: 'mask' por 'mascara'
            if mask_data is not None:
                if isinstance(mask_data, list):
                    mask = np.array(mask_data, dtype=np.float32)
                else:
                    mask = mask_data.astype(np.float32)
                
                if mask.shape == shape:
                    confianza = seg.get('confianza', 1.0)
                    mapa_calor += mask * confianza
        
        # Normalizar
        if mapa_calor.max() > 0:
            mapa_calor = mapa_calor / mapa_calor.max()
        
        return mapa_calor
    
    def visualizar_mapa_calor(self, imagen: np.ndarray, mapa_calor: np.ndarray, 
                             save_path: str = None) -> np.ndarray:
        """
        Visualiza mapa de calor sobre la imagen
        """
        # Convertir mapa de calor a color
        heatmap_color = cv2.applyColorMap((mapa_calor * 255).astype(np.uint8), cv2.COLORMAP_JET)
        
        # Combinar con imagen original
        resultado = cv2.addWeighted(imagen, 0.6, heatmap_color, 0.4, 0)
        
        if save_path:
            cv2.imwrite(save_path, resultado)
        
        return resultado

    def verificar_consistencia_mascaras(self, segmentaciones: List[Dict]) -> None:
        """
        Función de diagnóstico para verificar la consistencia de las máscaras
        """
        print("\n🔍 VERIFICANDO CONSISTENCIA DE MÁSCARAS:")
        print("=" * 50)
        
        for i, seg in enumerate(segmentaciones):
            print(f"\nSegmentación {i}:")
            
            # Verificar campos esperados
            campos_esperados = ['clase', 'confianza', 'bbox', 'centroide', 'area', 'area_mascara', 'mascara']
            for campo in campos_esperados:
                if campo in seg:
                    if campo == 'mascara':
                        mask_data = seg[campo]
                        if mask_data is not None:
                            if isinstance(mask_data, np.ndarray):
                                print(f"   ✅ {campo}: numpy array {mask_data.shape}")
                            elif isinstance(mask_data, list):
                                print(f"   ✅ {campo}: lista con {len(mask_data)} elementos")
                            else:
                                print(f"   ⚠️  {campo}: tipo inesperado {type(mask_data)}")
                        else:
                            print(f"   ❌ {campo}: None")
                    else:
                        print(f"   ✅ {campo}: {seg[campo]}")
                else:
                    print(f"   ❌ {campo}: faltante")
            
            # Verificar coherencia entre áreas
            if 'area' in seg and 'area_mascara' in seg:
                area_ratio = seg['area_mascara'] / seg['area'] if seg['area'] > 0 else 0
                if area_ratio > 1.2 or area_ratio < 0.8:
                    print(f"   ⚠️  Inconsistencia de áreas: bbox={seg['area']}, mask={seg['area_mascara']}, ratio={area_ratio:.2f}")
