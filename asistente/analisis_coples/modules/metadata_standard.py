#!/usr/bin/env python3
"""
Módulo para estandarizar la estructura de metadatos JSON
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np

class MetadataStandard:
    """
    Clase para crear metadatos estandarizados para todos los tipos de análisis
    """
    
    # Configuración de modelos
    MODELOS = {
        'clasificacion': 'CopleClasDef2C1V.onnx',
        'deteccion_piezas': 'CopleDetPz1C1V.onnx', 
        'deteccion_defectos': 'CopleDetDef1C2V.onnx',
        'segmentacion_defectos': 'CopleSegDef1C8V.onnx',
        'segmentacion_piezas': 'CopleSegPZ1C1V.onnx'
    }
    
    # Configuración de clases por modelo
    CLASES_MODELO = {
        'clasificacion': ['Aceptado', 'Rechazado'],
        'deteccion_piezas': ['Cople'],
        'deteccion_defectos': ['Defecto'],
        'segmentacion_defectos': ['Defecto'],
        'segmentacion_piezas': ['Cople']
    }
    
    @staticmethod
    def crear_metadatos_base(tipo_analisis: str, archivo_imagen: str, 
                           timestamp_captura: str = None) -> Dict[str, Any]:
        """
        Crea la estructura base de metadatos común a todos los análisis
        
        Args:
            tipo_analisis: Tipo de análisis (clasificacion, deteccion_piezas, etc.)
            archivo_imagen: Nombre del archivo de imagen
            timestamp_captura: Timestamp de captura (opcional)
            
        Returns:
            Diccionario con metadatos base
        """
        timestamp_actual = datetime.now().isoformat()
        
        metadatos = {
            # Información del archivo
            "archivo_imagen": archivo_imagen,
            "timestamp_procesamiento": timestamp_actual,
            "timestamp_captura": timestamp_captura or timestamp_actual,
            
            # Información del análisis
            "tipo_analisis": tipo_analisis,
            "version_metadatos": "1.0",
            
            # Información del modelo
            "modelo": {
                "nombre": MetadataStandard.MODELOS.get(tipo_analisis, "Desconocido"),
                "tipo": tipo_analisis,
                "clases_disponibles": MetadataStandard.CLASES_MODELO.get(tipo_analisis, [])
            },
            
            # Información de la imagen
            "imagen": {
                "resolucion": {
                    "ancho": 640,
                    "alto": 640,
                    "canales": 3
                },
                "formato": "RGB",
                "tipo": "uint8"
            },
            
            # Información del sistema
            "sistema": {
                "version": "1.0",
                "plataforma": "Linux",
                "framework": "ONNX Runtime"
            }
        }
        
        return metadatos
    
    @staticmethod
    def agregar_resultados_clasificacion(metadatos: Dict, clasificacion: Dict, 
                                       tiempos: Dict) -> Dict:
        """
        Agrega resultados de clasificación a los metadatos
        
        Args:
            metadatos: Metadatos base
            clasificacion: Resultado de clasificación
            tiempos: Tiempos de procesamiento
            
        Returns:
            Metadatos actualizados
        """
        metadatos["resultados"] = {
            "clasificacion": {
                "clase": clasificacion.get("clase", "Desconocido"),
                "confianza": float(clasificacion.get("confianza", 0.0)),
                "tiempo_inferencia_ms": float(clasificacion.get("tiempo_inferencia", 0.0))
            }
        }
        
        metadatos["tiempos"] = {
            "captura_ms": float(tiempos.get("captura_ms", 0.0)),
            "clasificacion_ms": float(tiempos.get("clasificacion_ms", 0.0)),
            "total_ms": float(tiempos.get("total_ms", 0.0))
        }
        
        metadatos["estadisticas"] = {
            "total_clasificaciones": 1,
            "confianza_promedio": float(clasificacion.get("confianza", 0.0)),
            "confianza_maxima": float(clasificacion.get("confianza", 0.0)),
            "confianza_minima": float(clasificacion.get("confianza", 0.0))
        }
        
        return metadatos
    
    @staticmethod
    def agregar_resultados_deteccion(metadatos: Dict, detecciones: List[Dict], 
                                   tiempos: Dict, tipo_deteccion: str) -> Dict:
        """
        Agrega resultados de detección a los metadatos
        
        Args:
            metadatos: Metadatos base
            detecciones: Lista de detecciones
            tiempos: Tiempos de procesamiento
            tipo_deteccion: Tipo de detección (piezas o defectos)
            
        Returns:
            Metadatos actualizados
        """
        # Serializar detecciones
        detecciones_serializables = []
        for deteccion in detecciones:
            deteccion_serializable = {
                "id": len(detecciones_serializables) + 1,
                "clase": deteccion.get("clase", "Desconocido"),
                "confianza": float(deteccion.get("confianza", 0.0)),
                "bbox": {
                    "x1": int(deteccion.get("bbox", {}).get("x1", 0)),
                    "y1": int(deteccion.get("bbox", {}).get("y1", 0)),
                    "x2": int(deteccion.get("bbox", {}).get("x2", 0)),
                    "y2": int(deteccion.get("bbox", {}).get("y2", 0))
                },
                "centroide": {
                    "x": int(deteccion.get("centroide", {}).get("x", 0)),
                    "y": int(deteccion.get("centroide", {}).get("y", 0))
                },
                "area": int(deteccion.get("area", 0))
            }
            detecciones_serializables.append(deteccion_serializable)
        
        metadatos["resultados"] = {
            f"{tipo_deteccion}_detectadas": detecciones_serializables
        }
        
        metadatos["tiempos"] = {
            "captura_ms": float(tiempos.get("captura_ms", 0.0)),
            f"deteccion_{tipo_deteccion}_ms": float(tiempos.get(f"deteccion_{tipo_deteccion}_ms", 0.0)),
            "total_ms": float(tiempos.get("total_ms", 0.0))
        }
        
        # Estadísticas
        if detecciones:
            confianzas = [d.get("confianza", 0.0) for d in detecciones]
            areas = [d.get("area", 0) for d in detecciones]
            
            metadatos["estadisticas"] = {
                f"total_{tipo_deteccion}": len(detecciones),
                "confianza_promedio": float(np.mean(confianzas)),
                "confianza_maxima": float(np.max(confianzas)),
                "confianza_minima": float(np.min(confianzas)),
                "area_total": int(np.sum(areas)),
                "area_promedio": float(np.mean(areas))
            }
        else:
            metadatos["estadisticas"] = {
                f"total_{tipo_deteccion}": 0,
                "confianza_promedio": 0.0,
                "confianza_maxima": 0.0,
                "confianza_minima": 0.0,
                "area_total": 0,
                "area_promedio": 0.0
            }
        
        return metadatos
    
    @staticmethod
    def agregar_resultados_segmentacion(metadatos: Dict, segmentaciones: List[Dict], 
                                      tiempos: Dict, tipo_segmentacion: str) -> Dict:
        """
        Agrega resultados de segmentación a los metadatos
        
        Args:
            metadatos: Metadatos base
            segmentaciones: Lista de segmentaciones
            tiempos: Tiempos de procesamiento
            tipo_segmentacion: Tipo de segmentación (defectos o piezas)
            
        Returns:
            Metadatos actualizados
        """
        # Serializar segmentaciones
        segmentaciones_serializables = []
        for i, segmentacion in enumerate(segmentaciones):
            try:
                entrada = {
                    "id": i + 1,
                    "clase": segmentacion.get("clase", "Desconocido"),
                    "confianza": float(segmentacion.get("confianza", 0.0)),
                    "bbox": {
                        "x1": int(segmentacion.get("bbox", {}).get("x1", 0)),
                        "y1": int(segmentacion.get("bbox", {}).get("y1", 0)),
                        "x2": int(segmentacion.get("bbox", {}).get("x2", 0)),
                        "y2": int(segmentacion.get("bbox", {}).get("y2", 0))
                    },
                    "centroide": {
                        "x": int(segmentacion.get("centroide", {}).get("x", 0)),
                        "y": int(segmentacion.get("centroide", {}).get("y", 0))
                    },
                    "area_bbox": int(segmentacion.get("area", 0)),
                    "area_mascara": int(segmentacion.get("area_mascara", 0)),
                    "dimensiones_mascara": {
                        "ancho": int(segmentacion.get("ancho_mascara", 0)),
                        "alto": int(segmentacion.get("alto_mascara", 0))
                    },
                    "tiene_mascara": segmentacion.get("mascara") is not None
                }
                
                # Información adicional de fusión si está disponible
                if segmentacion.get("fusionada", False):
                    entrada["fusionada"] = True
                    entrada["objetos_fusionados"] = segmentacion.get("objetos_fusionados", 1)
                
                # Información de la máscara si está disponible
                if "mascara" in segmentacion and segmentacion["mascara"] is not None:
                    mascara = segmentacion["mascara"]
                    if isinstance(mascara, np.ndarray):
                        entrada["info_mascara"] = {
                            "shape": list(mascara.shape),
                            "tipo": str(mascara.dtype),
                            "rango": [float(np.min(mascara)), float(np.max(mascara))],
                            "pixels_activos": int(np.sum(mascara > 0.5))
                        }
                
                # Coeficientes de máscara (solo primeros 5 para estabilidad)
                if "coeficientes_mascara" in segmentacion:
                    coeffs = segmentacion["coeficientes_mascara"]
                    if isinstance(coeffs, list) and len(coeffs) > 0:
                        entrada["coeficientes_mascara"] = coeffs[:5]
                    else:
                        entrada["coeficientes_mascara"] = []
                
                segmentaciones_serializables.append(entrada)
                
            except Exception as e:
                print(f"⚠️ Error serializando segmentación {i}: {e}")
                continue
        
        metadatos["resultados"] = {
            f"{tipo_segmentacion}_segmentadas": segmentaciones_serializables
        }
        
        metadatos["tiempos"] = {
            "captura_ms": float(tiempos.get("captura_ms", 0.0)),
            f"segmentacion_{tipo_segmentacion}_ms": float(tiempos.get(f"segmentacion_{tipo_segmentacion}_ms", 0.0)),
            "total_ms": float(tiempos.get("total_ms", 0.0))
        }
        
        # Estadísticas
        if segmentaciones:
            confianzas = [s.get("confianza", 0.0) for s in segmentaciones]
            areas_mascara = [s.get("area_mascara", 0) for s in segmentaciones]
            fusionadas = sum(1 for s in segmentaciones if s.get("fusionada", False))
            total_objetos_originales = sum(s.get("objetos_fusionados", 1) for s in segmentaciones)
            
            metadatos["estadisticas"] = {
                f"total_{tipo_segmentacion}": len(segmentaciones),
                "confianza_promedio": float(np.mean(confianzas)),
                "confianza_maxima": float(np.max(confianzas)),
                "confianza_minima": float(np.min(confianzas)),
                "area_total_mascaras": int(np.sum(areas_mascara)),
                "area_promedio_mascaras": float(np.mean(areas_mascara)),
                "fusionadas": fusionadas,
                "total_objetos_originales": total_objetos_originales
            }
        else:
            metadatos["estadisticas"] = {
                f"total_{tipo_segmentacion}": 0,
                "confianza_promedio": 0.0,
                "confianza_maxima": 0.0,
                "confianza_minima": 0.0,
                "area_total_mascaras": 0,
                "area_promedio_mascaras": 0.0,
                "fusionadas": 0,
                "total_objetos_originales": 0
            }
        
        return metadatos
    
    @staticmethod
    def guardar_metadatos(metadatos: Dict, ruta_archivo: str) -> bool:
        """
        Guarda los metadatos en un archivo JSON
        
        Args:
            metadatos: Metadatos a guardar
            ruta_archivo: Ruta del archivo JSON
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        try:
            # Crear directorio si no existe
            directorio = os.path.dirname(ruta_archivo)
            if directorio and not os.path.exists(directorio):
                os.makedirs(directorio)
            
            # Guardar archivo JSON
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                json.dump(metadatos, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"❌ Error guardando metadatos: {e}")
            return False
    
    @staticmethod
    def crear_metadatos_completos(tipo_analisis: str, archivo_imagen: str, 
                                resultados: Any, tiempos: Dict,
                                timestamp_captura: str = None) -> Dict:
        """
        Crea metadatos completos según el tipo de análisis
        
        Args:
            tipo_analisis: Tipo de análisis
            archivo_imagen: Nombre del archivo de imagen
            resultados: Resultados del análisis
            tiempos: Tiempos de procesamiento
            timestamp_captura: Timestamp de captura
            
        Returns:
            Metadatos completos
        """
        # Crear metadatos base
        metadatos = MetadataStandard.crear_metadatos_base(
            tipo_analisis, archivo_imagen, timestamp_captura
        )
        
        # Agregar resultados según el tipo de análisis
        if tipo_analisis == "clasificacion":
            metadatos = MetadataStandard.agregar_resultados_clasificacion(
                metadatos, resultados, tiempos
            )
        elif tipo_analisis == "deteccion_piezas":
            metadatos = MetadataStandard.agregar_resultados_deteccion(
                metadatos, resultados, tiempos, "piezas"
            )
        elif tipo_analisis == "deteccion_defectos":
            metadatos = MetadataStandard.agregar_resultados_deteccion(
                metadatos, resultados, tiempos, "defectos"
            )
        elif tipo_analisis == "segmentacion_defectos":
            metadatos = MetadataStandard.agregar_resultados_segmentacion(
                metadatos, resultados, tiempos, "defectos"
            )
        elif tipo_analisis == "segmentacion_piezas":
            metadatos = MetadataStandard.agregar_resultados_segmentacion(
                metadatos, resultados, tiempos, "piezas"
            )
        
        return metadatos
