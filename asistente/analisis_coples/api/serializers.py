# analisis_coples/api/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import ConfiguracionSistema, AnalisisCople
from ..resultados_models import (
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
    
    # Resultados relacionados (solo segmentación)
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
            'segmentacion_defectos_ms': obj.tiempo_segmentacion_defectos_ms,
            'segmentacion_piezas_ms': obj.tiempo_segmentacion_piezas_ms,
            'total_ms': obj.tiempo_total_ms
        }


class AnalisisCopleListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de análisis"""
    
    usuario_nombre = serializers.CharField(source='usuario.name', read_only=True)
    configuracion_nombre = serializers.CharField(source='configuracion.nombre', read_only=True)
    num_defectos = serializers.SerializerMethodField()
    num_piezas = serializers.SerializerMethodField()
    
    class Meta:
        model = AnalisisCople
        fields = [
            'id', 'id_analisis', 'timestamp_captura', 'timestamp_procesamiento',
            'tipo_analisis', 'estado', 'usuario_nombre', 'configuracion_nombre',
            'num_defectos', 'num_piezas', 'tiempo_total_ms', 'mensaje_error'
        ]
    
    def get_num_defectos(self, obj):
        return obj.segmentaciones_defectos.count()
    
    def get_num_piezas(self, obj):
        return obj.segmentaciones_piezas.count()


class EstadisticasSistemaSerializer(serializers.ModelSerializer):
    """Serializer para EstadisticasSistema"""
    
    tasa_exito = serializers.ReadOnlyField()
    promedio_defectos_por_analisis = serializers.ReadOnlyField()
    promedio_piezas_por_analisis = serializers.ReadOnlyField()
    
    class Meta:
        model = EstadisticasSistema
        fields = [
            'id', 'fecha', 'total_analisis', 'analisis_exitosos', 'analisis_con_error',
            'total_defectos_detectados', 'total_piezas_detectadas', 
            'tiempo_promedio_captura_ms', 'tiempo_promedio_segmentacion_ms', 
            'tiempo_promedio_total_ms', 'confianza_promedio', 'tasa_exito',
            'promedio_defectos_por_analisis', 'promedio_piezas_por_analisis'
        ]


class AnalisisRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de análisis (solo segmentación)"""
    
    tipo_analisis = serializers.ChoiceField(
        choices=[
            ('segmentacion_completa', 'Segmentación Completa (Defectos + Piezas)'),
            ('segmentacion_defectos', 'Solo Segmentación de Defectos'),
            ('segmentacion_piezas', 'Solo Segmentación de Piezas'),
        ],
        default='segmentacion_completa'
    )
    
    configuracion_id = serializers.IntegerField(required=False, allow_null=True)


class ConfiguracionRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de configuración"""
    
    configuracion_id = serializers.IntegerField(required=True)
    activar = serializers.BooleanField(default=True)
