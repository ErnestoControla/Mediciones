# analisis_coples/api/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import ConfiguracionSistema, AnalisisCople
from ..resultados_models import (
    ResultadoClasificacion,
    DeteccionPieza,
    DeteccionDefecto,
    SegmentacionDefecto,
    SegmentacionPieza,
    EstadisticasSistema
)

User = get_user_model()


class ConfiguracionSistemaSerializer(serializers.ModelSerializer):
    """Serializer para ConfiguracionSistema"""
    
    creada_por_nombre = serializers.CharField(source='creada_por.name', read_only=True)
    
    class Meta:
        model = ConfiguracionSistema
        fields = [
            'id', 'nombre', 'ip_camara', 'umbral_confianza', 'umbral_iou',
            'configuracion_robustez', 'activa', 'creada_por', 'creada_por_nombre',
            'fecha_creacion', 'fecha_modificacion'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_modificacion']


class ResultadoClasificacionSerializer(serializers.ModelSerializer):
    """Serializer para ResultadoClasificacion"""
    
    class Meta:
        model = ResultadoClasificacion
        fields = ['clase_predicha', 'confianza', 'tiempo_inferencia_ms']


class DeteccionPiezaSerializer(serializers.ModelSerializer):
    """Serializer para DeteccionPieza"""
    
    bbox = serializers.SerializerMethodField()
    centroide = serializers.SerializerMethodField()
    
    class Meta:
        model = DeteccionPieza
        fields = [
            'clase', 'confianza', 'bbox', 'centroide', 'area'
        ]
    
    def get_bbox(self, obj):
        return {
            'x1': obj.bbox_x1,
            'y1': obj.bbox_y1,
            'x2': obj.bbox_x2,
            'y2': obj.bbox_y2
        }
    
    def get_centroide(self, obj):
        return {
            'x': obj.centroide_x,
            'y': obj.centroide_y
        }


class DeteccionDefectoSerializer(serializers.ModelSerializer):
    """Serializer para DeteccionDefecto"""
    
    bbox = serializers.SerializerMethodField()
    centroide = serializers.SerializerMethodField()
    
    class Meta:
        model = DeteccionDefecto
        fields = [
            'clase', 'confianza', 'bbox', 'centroide', 'area'
        ]
    
    def get_bbox(self, obj):
        return {
            'x1': obj.bbox_x1,
            'y1': obj.bbox_y1,
            'x2': obj.bbox_x2,
            'y2': obj.bbox_y2
        }
    
    def get_centroide(self, obj):
        return {
            'x': obj.centroide_x,
            'y': obj.centroide_y
        }


class SegmentacionDefectoSerializer(serializers.ModelSerializer):
    """Serializer para SegmentacionDefecto"""
    
    bbox = serializers.SerializerMethodField()
    centroide = serializers.SerializerMethodField()
    
    class Meta:
        model = SegmentacionDefecto
        fields = [
            'clase', 'confianza', 'bbox', 'centroide', 
            'area_mascara', 'coeficientes_mascara'
        ]
    
    def get_bbox(self, obj):
        return {
            'x1': obj.bbox_x1,
            'y1': obj.bbox_y1,
            'x2': obj.bbox_x2,
            'y2': obj.bbox_y2
        }
    
    def get_centroide(self, obj):
        return {
            'x': obj.centroide_x,
            'y': obj.centroide_y
        }


class SegmentacionPiezaSerializer(serializers.ModelSerializer):
    """Serializer para SegmentacionPieza"""
    
    bbox = serializers.SerializerMethodField()
    centroide = serializers.SerializerMethodField()
    
    class Meta:
        model = SegmentacionPieza
        fields = [
            'clase', 'confianza', 'bbox', 'centroide', 
            'area_mascara', 'ancho_mascara', 'alto_mascara', 'coeficientes_mascara'
        ]
    
    def get_bbox(self, obj):
        return {
            'x1': obj.bbox_x1,
            'y1': obj.bbox_y1,
            'x2': obj.bbox_x2,
            'y2': obj.bbox_y2
        }
    
    def get_centroide(self, obj):
        return {
            'x': obj.centroide_x,
            'y': obj.centroide_y
        }


class AnalisisCopleSerializer(serializers.ModelSerializer):
    """Serializer para AnalisisCople con resultados relacionados"""
    
    usuario_nombre = serializers.CharField(source='usuario.name', read_only=True)
    configuracion_nombre = serializers.CharField(source='configuracion.nombre', read_only=True)
    
    # Resultados relacionados
    resultado_clasificacion = ResultadoClasificacionSerializer(read_only=True)
    detecciones_piezas = DeteccionPiezaSerializer(many=True, read_only=True)
    detecciones_defectos = DeteccionDefectoSerializer(many=True, read_only=True)
    segmentaciones_defectos = SegmentacionDefectoSerializer(many=True, read_only=True)
    segmentaciones_piezas = SegmentacionPiezaSerializer(many=True, read_only=True)
    
    # Tiempos de procesamiento
    tiempos = serializers.SerializerMethodField()
    
    class Meta:
        model = AnalisisCople
        fields = [
            'id', 'id_analisis', 'timestamp_captura', 'timestamp_procesamiento',
            'tipo_analisis', 'estado', 'usuario', 'usuario_nombre', 'configuracion',
            'configuracion_nombre', 'archivo_imagen', 'archivo_json',
            'resolucion_ancho', 'resolucion_alto', 'resolucion_canales',
            'tiempos', 'metadatos_json', 'mensaje_error',
            'resultado_clasificacion', 'detecciones_piezas', 'detecciones_defectos',
            'segmentaciones_defectos', 'segmentaciones_piezas'
        ]
        read_only_fields = [
            'id', 'timestamp_procesamiento', 'archivo_imagen', 'archivo_json',
            'resolucion_ancho', 'resolucion_alto', 'resolucion_canales',
            'tiempos', 'metadatos_json', 'mensaje_error'
        ]
    
    def get_tiempos(self, obj):
        return {
            'captura_ms': obj.tiempo_captura_ms,
            'clasificacion_ms': obj.tiempo_clasificacion_ms,
            'deteccion_piezas_ms': obj.tiempo_deteccion_piezas_ms,
            'deteccion_defectos_ms': obj.tiempo_deteccion_defectos_ms,
            'segmentacion_defectos_ms': obj.tiempo_segmentacion_defectos_ms,
            'segmentacion_piezas_ms': obj.tiempo_segmentacion_piezas_ms,
            'total_ms': obj.tiempo_total_ms
        }


class AnalisisCopleListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de análisis"""
    
    usuario_nombre = serializers.CharField(source='usuario.name', read_only=True)
    configuracion_nombre = serializers.CharField(source='configuracion.nombre', read_only=True)
    clase_predicha = serializers.CharField(source='resultado_clasificacion.clase_predicha', read_only=True)
    confianza = serializers.FloatField(source='resultado_clasificacion.confianza', read_only=True)
    
    class Meta:
        model = AnalisisCople
        fields = [
            'id', 'id_analisis', 'timestamp_captura', 'timestamp_procesamiento',
            'tipo_analisis', 'estado', 'usuario_nombre', 'configuracion_nombre',
            'clase_predicha', 'confianza', 'tiempo_total_ms', 'mensaje_error'
        ]


class EstadisticasSistemaSerializer(serializers.ModelSerializer):
    """Serializer para EstadisticasSistema"""
    
    tasa_exito = serializers.ReadOnlyField()
    tasa_aceptacion = serializers.ReadOnlyField()
    
    class Meta:
        model = EstadisticasSistema
        fields = [
            'id', 'fecha', 'total_analisis', 'analisis_exitosos', 'analisis_con_error',
            'total_aceptados', 'total_rechazados', 'tiempo_promedio_captura_ms',
            'tiempo_promedio_clasificacion_ms', 'tiempo_promedio_total_ms',
            'confianza_promedio', 'tasa_exito', 'tasa_aceptacion'
        ]


class AnalisisRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de análisis"""
    
    tipo_analisis = serializers.ChoiceField(
        choices=[
            ('completo', 'Análisis Completo'),
            ('clasificacion', 'Solo Clasificación'),
            ('deteccion_piezas', 'Solo Detección de Piezas'),
            ('deteccion_defectos', 'Solo Detección de Defectos'),
            ('segmentacion_defectos', 'Solo Segmentación de Defectos'),
            ('segmentacion_piezas', 'Solo Segmentación de Piezas'),
        ],
        default='completo'
    )
    
    configuracion_id = serializers.IntegerField(required=False, allow_null=True)


class ConfiguracionRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de configuración"""
    
    configuracion_id = serializers.IntegerField(required=True)
    activar = serializers.BooleanField(default=True)
