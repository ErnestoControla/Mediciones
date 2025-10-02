# analisis_coples/api/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import ConfiguracionSistema, AnalisisCople, RutinaInspeccion, EstadoCamara
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
            'configuracion_robustez', 'distancia_camara_mm', 'factor_conversion_px_mm',
            'activa', 'creada_por', 'creada_por_nombre',
            'fecha_creacion', 'fecha_modificacion'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_modificacion']


class SegmentacionDefectoSerializer(serializers.ModelSerializer):
    """Serializer para SegmentacionDefecto con mediciones dimensionales"""
    
    bbox = serializers.SerializerMethodField()
    centroide = serializers.SerializerMethodField()
    mediciones_px = serializers.SerializerMethodField()
    mediciones_mm = serializers.SerializerMethodField()
    geometria = serializers.SerializerMethodField()
    
    class Meta:
        model = SegmentacionDefecto
        fields = [
            'id', 'clase', 'confianza', 'bbox', 'centroide', 
            'mediciones_px', 'mediciones_mm', 'geometria',
            'coeficientes_mascara'
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
    
    def get_mediciones_px(self, obj):
        return {
            'ancho_bbox': obj.ancho_bbox_px,
            'alto_bbox': obj.alto_bbox_px,
            'ancho_mascara': obj.ancho_mascara_px,
            'alto_mascara': obj.alto_mascara_px,
            'perimetro': obj.perimetro_mascara_px,
            'area': obj.area_mascara_px
        }
    
    def get_mediciones_mm(self, obj):
        if obj.ancho_bbox_mm is not None:
            return {
                'ancho_bbox': obj.ancho_bbox_mm,
                'alto_bbox': obj.alto_bbox_mm,
                'ancho_mascara': obj.ancho_mascara_mm,
                'alto_mascara': obj.alto_mascara_mm,
                'perimetro': obj.perimetro_mascara_mm,
                'area': obj.area_mascara_mm
            }
        return None
    
    def get_geometria(self, obj):
        return {
            'excentricidad': obj.excentricidad,
            'orientacion_grados': obj.orientacion_grados
        }


class SegmentacionPiezaSerializer(serializers.ModelSerializer):
    """Serializer para SegmentacionPieza con mediciones dimensionales"""
    
    bbox = serializers.SerializerMethodField()
    centroide = serializers.SerializerMethodField()
    mediciones_px = serializers.SerializerMethodField()
    mediciones_mm = serializers.SerializerMethodField()
    geometria = serializers.SerializerMethodField()
    
    class Meta:
        model = SegmentacionPieza
        fields = [
            'id', 'clase', 'confianza', 'bbox', 'centroide', 
            'mediciones_px', 'mediciones_mm', 'geometria',
            'coeficientes_mascara'
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
    
    def get_mediciones_px(self, obj):
        return {
            'ancho_bbox': obj.ancho_bbox_px,
            'alto_bbox': obj.alto_bbox_px,
            'ancho_mascara': obj.ancho_mascara_px,
            'alto_mascara': obj.alto_mascara_px,
            'perimetro': obj.perimetro_mascara_px,
            'area': obj.area_mascara_px
        }
    
    def get_mediciones_mm(self, obj):
        if obj.ancho_bbox_mm is not None:
            return {
                'ancho_bbox': obj.ancho_bbox_mm,
                'alto_bbox': obj.alto_bbox_mm,
                'ancho_mascara': obj.ancho_mascara_mm,
                'alto_mascara': obj.alto_mascara_mm,
                'perimetro': obj.perimetro_mascara_mm,
                'area': obj.area_mascara_mm
            }
        return None
    
    def get_geometria(self, obj):
        return {
            'excentricidad': obj.excentricidad,
            'orientacion_grados': obj.orientacion_grados
        }


class AnalisisCopleSerializer(serializers.ModelSerializer):
    """Serializer para AnalisisCople con resultados relacionados"""
    
    usuario_nombre = serializers.CharField(source='usuario.name', read_only=True)
    configuracion_nombre = serializers.CharField(source='configuracion.nombre', read_only=True)
    
    # Resultados relacionados (solo segmentación)
    segmentaciones_defectos = SegmentacionDefectoSerializer(many=True, read_only=True)
    segmentaciones_piezas = SegmentacionPiezaSerializer(many=True, read_only=True)
    
    # Tiempos de procesamiento (objeto y campos directos para compatibilidad)
    tiempos = serializers.SerializerMethodField()
    tiempo_total_ms = serializers.FloatField(read_only=True)
    
    # Campos adicionales para frontend
    tipo_analisis_display = serializers.CharField(source='get_tipo_analisis_display', read_only=True)
    imagen_procesada_url = serializers.SerializerMethodField()
    
    class Meta:
        model = AnalisisCople
        fields = [
            'id', 'id_analisis', 'timestamp_captura', 'timestamp_procesamiento',
            'tipo_analisis', 'tipo_analisis_display', 'estado', 'usuario', 'usuario_nombre', 
            'configuracion', 'configuracion_nombre', 'archivo_imagen', 'archivo_json',
            'resolucion_ancho', 'resolucion_alto', 'resolucion_canales',
            'tiempos', 'tiempo_total_ms', 'imagen_procesada_url', 'metadatos_json', 'mensaje_error',
            'segmentaciones_defectos', 'segmentaciones_piezas'
        ]
        read_only_fields = [
            'id', 'timestamp_procesamiento', 'archivo_imagen', 'archivo_json',
            'resolucion_ancho', 'resolucion_alto', 'resolucion_canales',
            'tiempos', 'tiempo_total_ms', 'imagen_procesada_url', 'metadatos_json', 'mensaje_error'
        ]
    
    def get_tiempos(self, obj):
        return {
            'captura_ms': obj.tiempo_captura_ms,
            'segmentacion_defectos_ms': obj.tiempo_segmentacion_defectos_ms,
            'segmentacion_piezas_ms': obj.tiempo_segmentacion_piezas_ms,
            'total_ms': obj.tiempo_total_ms
        }
    
    def get_imagen_procesada_url(self, obj):
        """Retorna la URL de la imagen procesada si existe"""
        if obj.archivo_imagen:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.archivo_imagen.url)
            return obj.archivo_imagen.url
        return None


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
    """Serializer para solicitudes de análisis con medición dimensional"""
    
    tipo_analisis = serializers.ChoiceField(
        choices=[
            ('medicion_piezas', 'Medición de Piezas'),
            ('medicion_defectos', 'Medición de Defectos'),
            ('rutina_inspeccion', 'Rutina de Inspección Multi-Ángulo'),
        ],
        default='medicion_piezas'
    )
    
    configuracion_id = serializers.IntegerField(required=False, allow_null=True)


class ConfiguracionRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de configuración"""
    
    configuracion_id = serializers.IntegerField(required=True)
    activar = serializers.BooleanField(default=True)


class RutinaInspeccionSerializer(serializers.ModelSerializer):
    """Serializer para RutinaInspeccion"""
    
    usuario_nombre = serializers.CharField(source='usuario.name', read_only=True)
    configuracion_nombre = serializers.CharField(source='configuracion.nombre', read_only=True)
    analisis_individuales = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    duracion_minutos = serializers.SerializerMethodField()
    
    class Meta:
        model = RutinaInspeccion
        fields = [
            'id', 'id_rutina', 'timestamp_inicio', 'timestamp_fin', 'estado',
            'configuracion', 'configuracion_nombre', 'usuario', 'usuario_nombre',
            'num_imagenes_capturadas', 'imagen_consolidada', 'reporte_json',
            'mensaje_error', 'analisis_individuales', 'duracion_minutos'
        ]
        read_only_fields = [
            'id', 'timestamp_inicio', 'timestamp_fin', 'imagen_consolidada',
            'reporte_json', 'mensaje_error', 'duracion_minutos'
        ]
    
    def get_duracion_minutos(self, obj):
        if obj.timestamp_fin and obj.timestamp_inicio:
            delta = obj.timestamp_fin - obj.timestamp_inicio
            return round(delta.total_seconds() / 60, 2)
        return None


class EstadoCamaraSerializer(serializers.ModelSerializer):
    """Serializer para EstadoCamara"""
    
    modelo_cargado_display = serializers.CharField(
        source='get_modelo_cargado_display', 
        read_only=True
    )
    tiempo_desde_ultimo_uso = serializers.SerializerMethodField()
    
    class Meta:
        model = EstadoCamara
        fields = [
            'id', 'activa', 'en_preview', 'hibernada', 'modelo_cargado',
            'modelo_cargado_display', 'frame_rate_actual', 'ultimo_uso',
            'ultima_actualizacion', 'tiempo_desde_ultimo_uso'
        ]
        read_only_fields = ['id', 'ultimo_uso', 'ultima_actualizacion']
    
    def get_tiempo_desde_ultimo_uso(self, obj):
        from django.utils import timezone
        delta = timezone.now() - obj.ultimo_uso
        segundos = int(delta.total_seconds())
        if segundos < 60:
            return f"{segundos}s"
        elif segundos < 3600:
            return f"{segundos // 60}m"
        else:
            return f"{segundos // 3600}h"
