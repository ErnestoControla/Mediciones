# analisis_coples/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ConfiguracionSistema, AnalisisCople, RutinaInspeccion, EstadoCamara
from .resultados_models import (
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


class SegmentacionDefectoInline(admin.TabularInline):
    """Inline para SegmentacionDefecto"""
    model = SegmentacionDefecto
    extra = 0
    readonly_fields = ['clase', 'confianza', 'ancho_bbox_px', 'alto_bbox_px', 'area_mascara_px', 'perimetro_mascara_px']


class SegmentacionPiezaInline(admin.TabularInline):
    """Inline para SegmentacionPieza"""
    model = SegmentacionPieza
    extra = 0
    readonly_fields = ['clase', 'confianza', 'ancho_bbox_px', 'alto_bbox_px', 'area_mascara_px', 'perimetro_mascara_px']


@admin.register(AnalisisCople)
class AnalisisCopleAdmin(admin.ModelAdmin):
    """Admin para AnalisisCople"""
    
    list_display = [
        'id_analisis', 'tipo_analisis', 'estado', 'usuario', 'configuracion',
        'timestamp_captura', 'tiempo_total_ms', 'num_defectos', 'num_piezas'
    ]
    
    list_filter = [
        'estado', 'tipo_analisis', 'usuario', 'configuracion', 'timestamp_captura'
    ]
    
    search_fields = ['id_analisis', 'usuario__username', 'configuracion__nombre']
    
    readonly_fields = [
        'id_analisis', 'timestamp_captura', 'timestamp_procesamiento',
        'archivo_imagen', 'archivo_json', 'resolucion_ancho', 'resolucion_alto',
        'resolucion_canales', 'tiempo_captura_ms', 
        'tiempo_segmentacion_defectos_ms', 'tiempo_segmentacion_piezas_ms',
        'tiempo_total_ms', 'metadatos_json', 'mensaje_error'
    ]
    
    inlines = [
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
                'tiempo_captura_ms', 'tiempo_segmentacion_defectos_ms',
                'tiempo_segmentacion_piezas_ms', 'tiempo_total_ms'
            )
        }),
        ('Metadatos y Errores', {
            'fields': ('metadatos_json', 'mensaje_error'),
            'classes': ('collapse',)
        })
    )
    
    def num_defectos(self, obj):
        """Mostrar número de defectos segmentados"""
        return obj.segmentaciones_defectos.count()
    num_defectos.short_description = 'Defectos'
    
    def num_piezas(self, obj):
        """Mostrar número de piezas segmentadas"""
        return obj.segmentaciones_piezas.count()
    num_piezas.short_description = 'Piezas'


@admin.register(SegmentacionDefecto)
class SegmentacionDefectoAdmin(admin.ModelAdmin):
    """Admin para SegmentacionDefecto"""
    
    list_display = ['analisis', 'clase', 'confianza', 'area_mascara_px', 'bbox_display', 'mediciones_display']
    list_filter = ['clase', 'analisis__tipo_analisis', 'analisis__timestamp_captura']
    search_fields = ['analisis__id_analisis', 'clase']
    readonly_fields = [
        'analisis', 'clase', 'confianza', 
        'bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2',
        'ancho_bbox_px', 'alto_bbox_px',
        'centroide_x', 'centroide_y',
        'area_mascara_px', 'ancho_mascara_px', 'alto_mascara_px', 'perimetro_mascara_px',
        'excentricidad', 'orientacion_grados',
        'ancho_bbox_mm', 'alto_bbox_mm', 'ancho_mascara_mm', 'alto_mascara_mm',
        'perimetro_mascara_mm', 'area_mascara_mm',
        'coeficientes_mascara'
    ]
    
    def bbox_display(self, obj):
        """Mostrar bbox en formato legible"""
        return f"({obj.bbox_x1}, {obj.bbox_y1}) - ({obj.bbox_x2}, {obj.bbox_y2})"
    bbox_display.short_description = 'BBox'
    
    def mediciones_display(self, obj):
        """Mostrar mediciones principales"""
        return f"{obj.ancho_mascara_px:.1f}×{obj.alto_mascara_px:.1f} px"
    mediciones_display.short_description = 'Dimensiones'


@admin.register(SegmentacionPieza)
class SegmentacionPiezaAdmin(admin.ModelAdmin):
    """Admin para SegmentacionPieza"""
    
    list_display = ['analisis', 'clase', 'confianza', 'area_mascara_px', 'dimensiones_mascara', 'bbox_display']
    list_filter = ['clase', 'analisis__tipo_analisis', 'analisis__timestamp_captura']
    search_fields = ['analisis__id_analisis', 'clase']
    readonly_fields = [
        'analisis', 'clase', 'confianza', 
        'bbox_x1', 'bbox_y1', 'bbox_x2', 'bbox_y2',
        'ancho_bbox_px', 'alto_bbox_px',
        'centroide_x', 'centroide_y',
        'area_mascara_px', 'ancho_mascara_px', 'alto_mascara_px', 'perimetro_mascara_px',
        'excentricidad', 'orientacion_grados',
        'ancho_bbox_mm', 'alto_bbox_mm', 'ancho_mascara_mm', 'alto_mascara_mm',
        'perimetro_mascara_mm', 'area_mascara_mm',
        'coeficientes_mascara'
    ]
    
    def bbox_display(self, obj):
        """Mostrar bbox en formato legible"""
        return f"({obj.bbox_x1}, {obj.bbox_y1}) - ({obj.bbox_x2}, {obj.bbox_y2})"
    bbox_display.short_description = 'BBox'
    
    def dimensiones_mascara(self, obj):
        """Mostrar dimensiones de la máscara"""
        return f"{obj.ancho_mascara_px:.1f}×{obj.alto_mascara_px:.1f} px"
    dimensiones_mascara.short_description = 'Dimensiones'


@admin.register(EstadisticasSistema)
class EstadisticasSistemaAdmin(admin.ModelAdmin):
    """Admin para EstadisticasSistema"""
    
    list_display = [
        'fecha', 'total_analisis', 'analisis_exitosos', 'analisis_con_error',
        'tasa_exito', 'total_defectos_detectados', 'total_piezas_detectadas'
    ]
    
    list_filter = ['fecha']
    
    search_fields = ['fecha']
    
    readonly_fields = [
        'fecha', 'total_analisis', 'analisis_exitosos', 'analisis_con_error',
        'total_defectos_detectados', 'total_piezas_detectadas', 
        'tiempo_promedio_captura_ms', 'tiempo_promedio_segmentacion_ms', 
        'tiempo_promedio_total_ms', 'confianza_promedio', 'tasa_exito',
        'promedio_defectos_por_analisis', 'promedio_piezas_por_analisis'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('fecha',)
        }),
        ('Estadísticas de Análisis', {
            'fields': ('total_analisis', 'analisis_exitosos', 'analisis_con_error', 'tasa_exito')
        }),
        ('Estadísticas de Segmentación', {
            'fields': (
                'total_defectos_detectados', 'total_piezas_detectadas', 
                'promedio_defectos_por_analisis', 'promedio_piezas_por_analisis',
                'confianza_promedio'
            )
        }),
        ('Tiempos Promedio', {
            'fields': ('tiempo_promedio_captura_ms', 'tiempo_promedio_segmentacion_ms', 'tiempo_promedio_total_ms')
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


@admin.register(RutinaInspeccion)
class RutinaInspeccionAdmin(admin.ModelAdmin):
    """Admin para RutinaInspeccion"""
    
    list_display = [
        'id_rutina', 'estado', 'usuario', 'configuracion',
        'num_imagenes_capturadas', 'timestamp_inicio', 'duracion'
    ]
    
    list_filter = ['estado', 'usuario', 'configuracion', 'timestamp_inicio']
    
    search_fields = ['id_rutina', 'usuario__username', 'configuracion__nombre']
    
    readonly_fields = [
        'id_rutina', 'timestamp_inicio', 'timestamp_fin', 'num_imagenes_capturadas',
        'imagen_consolidada', 'reporte_json', 'mensaje_error', 'duracion'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('id_rutina', 'estado', 'usuario', 'configuracion')
        }),
        ('Capturas', {
            'fields': ('num_imagenes_capturadas', 'imagen_consolidada')
        }),
        ('Timestamps', {
            'fields': ('timestamp_inicio', 'timestamp_fin', 'duracion')
        }),
        ('Reporte y Errores', {
            'fields': ('reporte_json', 'mensaje_error'),
            'classes': ('collapse',)
        })
    )
    
    def duracion(self, obj):
        """Mostrar duración de la rutina"""
        if obj.timestamp_fin and obj.timestamp_inicio:
            delta = obj.timestamp_fin - obj.timestamp_inicio
            minutos = delta.total_seconds() / 60
            return f"{minutos:.2f} min"
        return '-'
    duracion.short_description = 'Duración'


@admin.register(EstadoCamara)
class EstadoCamaraAdmin(admin.ModelAdmin):
    """Admin para EstadoCamara"""
    
    list_display = [
        'estado_display', 'modelo_cargado', 'frame_rate_actual',
        'ultimo_uso', 'tiempo_inactivo'
    ]
    
    readonly_fields = [
        'singleton_id', 'ultimo_uso', 'ultima_actualizacion', 'tiempo_inactivo'
    ]
    
    fieldsets = (
        ('Estado Actual', {
            'fields': ('activa', 'en_preview', 'hibernada')
        }),
        ('Modelo Cargado', {
            'fields': ('modelo_cargado',)
        }),
        ('Configuración', {
            'fields': ('frame_rate_actual',)
        }),
        ('Timestamps', {
            'fields': ('ultimo_uso', 'ultima_actualizacion', 'tiempo_inactivo'),
            'classes': ('collapse',)
        }),
        ('Sistema', {
            'fields': ('singleton_id',),
            'classes': ('collapse',)
        })
    )
    
    def estado_display(self, obj):
        """Mostrar estado actual de la cámara"""
        if obj.hibernada:
            return format_html('<span style="color: orange;">⏸ Hibernada</span>')
        elif obj.en_preview:
            return format_html('<span style="color: green;">▶ Preview {} FPS</span>', obj.frame_rate_actual)
        elif obj.activa:
            return format_html('<span style="color: blue;">● Activa</span>')
        else:
            return format_html('<span style="color: gray;">○ Inactiva</span>')
    estado_display.short_description = 'Estado'
    
    def tiempo_inactivo(self, obj):
        """Mostrar tiempo desde el último uso"""
        from django.utils import timezone
        delta = timezone.now() - obj.ultimo_uso
        segundos = int(delta.total_seconds())
        if segundos < 60:
            return f"{segundos}s"
        elif segundos < 3600:
            return f"{segundos // 60}m"
        else:
            return f"{segundos // 3600}h"
    tiempo_inactivo.short_description = 'Inactivo desde'
    
    def has_add_permission(self, request):
        """Solo permitir un registro (singleton)"""
        return EstadoCamara.objects.count() == 0
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar el estado"""
        return False