# analisis_coples/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ConfiguracionSistema, AnalisisCople
from .resultados_models import (
    ResultadoClasificacion,
    DeteccionPieza,
    DeteccionDefecto,
    SegmentacionDefecto,
    SegmentacionPieza,
    EstadisticasSistema
)


@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    """Admin para ConfiguracionSistema"""
    
    list_display = [
        'nombre', 'ip_camara', 'umbral_confianza', 'umbral_iou',
        'configuracion_robustez', 'activa', 'creada_por', 'fecha_creacion'
    ]
    
    list_filter = [
        'activa', 'configuracion_robustez', 'creada_por', 'fecha_creacion'
    ]
    
    search_fields = ['nombre', 'ip_camara']
    
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'activa', 'creada_por')
        }),
        ('Configuración de Cámara', {
            'fields': ('ip_camara',)
        }),
        ('Configuración de Modelos', {
            'fields': ('umbral_confianza', 'umbral_iou')
        }),
        ('Configuración de Robustez', {
            'fields': ('configuracion_robustez',)
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        """Asegurar que solo una configuración esté activa"""
        if obj.activa:
            ConfiguracionSistema.objects.filter(activa=True).update(activa=False)
        super().save_model(request, obj, form, change)


class ResultadoClasificacionInline(admin.TabularInline):
    """Inline para ResultadoClasificacion"""
    model = ResultadoClasificacion
    extra = 0
    readonly_fields = ['clase_predicha', 'confianza', 'tiempo_inferencia_ms']


class DeteccionPiezaInline(admin.TabularInline):
    """Inline para DeteccionPieza"""
    model = DeteccionPieza
    extra = 0
    readonly_fields = ['clase', 'confianza', 'bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2', 'centroide_x', 'centroide_y', 'area']


class DeteccionDefectoInline(admin.TabularInline):
    """Inline para DeteccionDefecto"""
    model = DeteccionDefecto
    extra = 0
    readonly_fields = ['clase', 'confianza', 'bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2', 'centroide_x', 'centroide_y', 'area']


class SegmentacionDefectoInline(admin.TabularInline):
    """Inline para SegmentacionDefecto"""
    model = SegmentacionDefecto
    extra = 0
    readonly_fields = ['clase', 'confianza', 'bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2', 'centroide_x', 'centroide_y', 'area_mascara']


class SegmentacionPiezaInline(admin.TabularInline):
    """Inline para SegmentacionPieza"""
    model = SegmentacionPieza
    extra = 0
    readonly_fields = ['clase', 'confianza', 'bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2', 'centroide_x', 'centroide_y', 'area_mascara', 'ancho_mascara', 'alto_mascara']


@admin.register(AnalisisCople)
class AnalisisCopleAdmin(admin.ModelAdmin):
    """Admin para AnalisisCople"""
    
    list_display = [
        'id_analisis', 'tipo_analisis', 'estado', 'usuario', 'configuracion',
        'timestamp_captura', 'tiempo_total_ms', 'clase_predicha', 'confianza'
    ]
    
    list_filter = [
        'estado', 'tipo_analisis', 'usuario', 'configuracion', 'timestamp_captura'
    ]
    
    search_fields = ['id_analisis', 'usuario__username', 'configuracion__nombre']
    
    readonly_fields = [
        'id_analisis', 'timestamp_captura', 'timestamp_procesamiento',
        'archivo_imagen', 'archivo_json', 'resolucion_ancho', 'resolucion_alto',
        'resolucion_canales', 'tiempo_captura_ms', 'tiempo_clasificacion_ms',
        'tiempo_deteccion_piezas_ms', 'tiempo_deteccion_defectos_ms',
        'tiempo_segmentacion_defectos_ms', 'tiempo_segmentacion_piezas_ms',
        'tiempo_total_ms', 'metadatos_json', 'mensaje_error'
    ]
    
    inlines = [
        ResultadoClasificacionInline,
        DeteccionPiezaInline,
        DeteccionDefectoInline,
        SegmentacionDefectoInline,
        SegmentacionPiezaInline
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('id_analisis', 'tipo_analisis', 'estado', 'usuario', 'configuracion')
        }),
        ('Timestamps', {
            'fields': ('timestamp_captura', 'timestamp_procesamiento')
        }),
        ('Archivos', {
            'fields': ('archivo_imagen', 'archivo_json')
        }),
        ('Información de Imagen', {
            'fields': ('resolucion_ancho', 'resolucion_alto', 'resolucion_canales')
        }),
        ('Tiempos de Procesamiento', {
            'fields': (
                'tiempo_captura_ms', 'tiempo_clasificacion_ms', 'tiempo_deteccion_piezas_ms',
                'tiempo_deteccion_defectos_ms', 'tiempo_segmentacion_defectos_ms',
                'tiempo_segmentacion_piezas_ms', 'tiempo_total_ms'
            )
        }),
        ('Metadatos y Errores', {
            'fields': ('metadatos_json', 'mensaje_error'),
            'classes': ('collapse',)
        })
    )
    
    def clase_predicha(self, obj):
        """Mostrar clase predicha en la lista"""
        try:
            return obj.resultado_clasificacion.clase_predicha
        except:
            return '-'
    clase_predicha.short_description = 'Clase Predicha'
    
    def confianza(self, obj):
        """Mostrar confianza en la lista"""
        try:
            return f"{obj.resultado_clasificacion.confianza:.2%}"
        except:
            return '-'
    confianza.short_description = 'Confianza'


@admin.register(ResultadoClasificacion)
class ResultadoClasificacionAdmin(admin.ModelAdmin):
    """Admin para ResultadoClasificacion"""
    
    list_display = ['analisis', 'clase_predicha', 'confianza', 'tiempo_inferencia_ms']
    list_filter = ['clase_predicha', 'analisis__tipo_analisis', 'analisis__timestamp_captura']
    search_fields = ['analisis__id_analisis', 'clase_predicha']
    readonly_fields = ['analisis', 'clase_predicha', 'confianza', 'tiempo_inferencia_ms']


@admin.register(DeteccionPieza)
class DeteccionPiezaAdmin(admin.ModelAdmin):
    """Admin para DeteccionPieza"""
    
    list_display = ['analisis', 'clase', 'confianza', 'area', 'bbox_display']
    list_filter = ['clase', 'analisis__tipo_analisis', 'analisis__timestamp_captura']
    search_fields = ['analisis__id_analisis', 'clase']
    readonly_fields = ['analisis', 'clase', 'confianza', 'bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2', 'centroide_x', 'centroide_y', 'area']
    
    def bbox_display(self, obj):
        """Mostrar bbox en formato legible"""
        return f"({obj.bbox_x1}, {obj.bbox_y1}) - ({obj.bbox_x2}, {obj.bbox_y2})"
    bbox_display.short_description = 'BBox'


@admin.register(DeteccionDefecto)
class DeteccionDefectoAdmin(admin.ModelAdmin):
    """Admin para DeteccionDefecto"""
    
    list_display = ['analisis', 'clase', 'confianza', 'area', 'bbox_display']
    list_filter = ['clase', 'analisis__tipo_analisis', 'analisis__timestamp_captura']
    search_fields = ['analisis__id_analisis', 'clase']
    readonly_fields = ['analisis', 'clase', 'confianza', 'bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2', 'centroide_x', 'centroide_y', 'area']
    
    def bbox_display(self, obj):
        """Mostrar bbox en formato legible"""
        return f"({obj.bbox_x1}, {obj.bbox_y1}) - ({obj.bbox_x2}, {obj.bbox_y2})"
    bbox_display.short_description = 'BBox'


@admin.register(SegmentacionDefecto)
class SegmentacionDefectoAdmin(admin.ModelAdmin):
    """Admin para SegmentacionDefecto"""
    
    list_display = ['analisis', 'clase', 'confianza', 'area_mascara', 'bbox_display']
    list_filter = ['clase', 'analisis__tipo_analisis', 'analisis__timestamp_captura']
    search_fields = ['analisis__id_analisis', 'clase']
    readonly_fields = ['analisis', 'clase', 'confianza', 'bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2', 'centroide_x', 'centroide_y', 'area_mascara', 'coeficientes_mascara']
    
    def bbox_display(self, obj):
        """Mostrar bbox en formato legible"""
        return f"({obj.bbox_x1}, {obj.bbox_y1}) - ({obj.bbox_x2}, {obj.bbox_y2})"
    bbox_display.short_description = 'BBox'


@admin.register(SegmentacionPieza)
class SegmentacionPiezaAdmin(admin.ModelAdmin):
    """Admin para SegmentacionPieza"""
    
    list_display = ['analisis', 'clase', 'confianza', 'area_mascara', 'dimensiones_mascara', 'bbox_display']
    list_filter = ['clase', 'analisis__tipo_analisis', 'analisis__timestamp_captura']
    search_fields = ['analisis__id_analisis', 'clase']
    readonly_fields = ['analisis', 'clase', 'confianza', 'bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2', 'centroide_x', 'centroide_y', 'area_mascara', 'ancho_mascara', 'alto_mascara', 'coeficientes_mascara']
    
    def bbox_display(self, obj):
        """Mostrar bbox en formato legible"""
        return f"({obj.bbox_x1}, {obj.bbox_y1}) - ({obj.bbox_x2}, {obj.bbox_y2})"
    bbox_display.short_description = 'BBox'
    
    def dimensiones_mascara(self, obj):
        """Mostrar dimensiones de la máscara"""
        return f"{obj.ancho_mascara}x{obj.alto_mascara}"
    dimensiones_mascara.short_description = 'Dimensiones Máscara'


@admin.register(EstadisticasSistema)
class EstadisticasSistemaAdmin(admin.ModelAdmin):
    """Admin para EstadisticasSistema"""
    
    list_display = [
        'fecha', 'total_analisis', 'analisis_exitosos', 'analisis_con_error',
        'tasa_exito', 'total_aceptados', 'total_rechazados', 'tasa_aceptacion'
    ]
    
    list_filter = ['fecha']
    
    search_fields = ['fecha']
    
    readonly_fields = [
        'fecha', 'total_analisis', 'analisis_exitosos', 'analisis_con_error',
        'total_aceptados', 'total_rechazados', 'tiempo_promedio_captura_ms',
        'tiempo_promedio_clasificacion_ms', 'tiempo_promedio_total_ms',
        'confianza_promedio', 'tasa_exito', 'tasa_aceptacion'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('fecha',)
        }),
        ('Estadísticas de Análisis', {
            'fields': ('total_analisis', 'analisis_exitosos', 'analisis_con_error', 'tasa_exito')
        }),
        ('Estadísticas de Clasificación', {
            'fields': ('total_aceptados', 'total_rechazados', 'tasa_aceptacion', 'confianza_promedio')
        }),
        ('Tiempos Promedio', {
            'fields': ('tiempo_promedio_captura_ms', 'tiempo_promedio_clasificacion_ms', 'tiempo_promedio_total_ms')
        })
    )
    
    def has_add_permission(self, request):
        """No permitir agregar estadísticas manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """No permitir modificar estadísticas"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar estadísticas"""
        return False