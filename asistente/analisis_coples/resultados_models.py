# analisis_coples/resultados_models.py
"""
Modelos para almacenar resultados de segmentación de coples.
Solo maneja segmentación de defectos y piezas.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import AnalisisCople


class SegmentacionDefecto(models.Model):
    """Segmentación individual de un defecto"""
    
    analisis = models.ForeignKey(
        AnalisisCople,
        on_delete=models.CASCADE,
        related_name="segmentaciones_defectos",
        verbose_name=_("Análisis")
    )
    
    clase = models.CharField(
        _("Clase"),
        max_length=50,
        help_text="Clase del defecto segmentado"
    )
    
    confianza = models.FloatField(
        _("Confianza"),
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confianza de la segmentación (0.0 - 1.0)"
    )
    
    # Coordenadas del bounding box
    bbox_x1 = models.IntegerField(_("BBox X1"))
    bbox_y1 = models.IntegerField(_("BBox Y1"))
    bbox_x2 = models.IntegerField(_("BBox X2"))
    bbox_y2 = models.IntegerField(_("BBox Y2"))
    
    # Centroide
    centroide_x = models.IntegerField(_("Centroide X"))
    centroide_y = models.IntegerField(_("Centroide Y"))
    
    # Área de la máscara
    area_mascara = models.IntegerField(_("Área de máscara"), help_text="Área en píxeles")
    
    # Coeficientes de la máscara (serializados como JSON)
    coeficientes_mascara = models.JSONField(
        _("Coeficientes de máscara"),
        help_text="Coeficientes de la máscara de segmentación"
    )
    
    class Meta:
        verbose_name = _("Segmentación de Defecto")
        verbose_name_plural = _("Segmentaciones de Defectos")
        ordering = ['-confianza']
    
    def __str__(self):
        return f"{self.clase} ({self.confianza:.2%})"


class SegmentacionPieza(models.Model):
    """Segmentación individual de una pieza"""
    
    analisis = models.ForeignKey(
        AnalisisCople,
        on_delete=models.CASCADE,
        related_name="segmentaciones_piezas",
        verbose_name=_("Análisis")
    )
    
    clase = models.CharField(
        _("Clase"),
        max_length=50,
        help_text="Clase de la pieza segmentada"
    )
    
    confianza = models.FloatField(
        _("Confianza"),
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confianza de la segmentación (0.0 - 1.0)"
    )
    
    # Coordenadas del bounding box
    bbox_x1 = models.IntegerField(_("BBox X1"))
    bbox_y1 = models.IntegerField(_("BBox Y1"))
    bbox_x2 = models.IntegerField(_("BBox X2"))
    bbox_y2 = models.IntegerField(_("BBox Y2"))
    
    # Centroide
    centroide_x = models.IntegerField(_("Centroide X"))
    centroide_y = models.IntegerField(_("Centroide Y"))
    
    # Área de la máscara
    area_mascara = models.IntegerField(_("Área de máscara"), help_text="Área en píxeles")
    
    # Dimensiones de la máscara
    ancho_mascara = models.IntegerField(_("Ancho de máscara"))
    alto_mascara = models.IntegerField(_("Alto de máscara"))
    
    # Coeficientes de la máscara (serializados como JSON)
    coeficientes_mascara = models.JSONField(
        _("Coeficientes de máscara"),
        help_text="Coeficientes de la máscara de segmentación"
    )
    
    class Meta:
        verbose_name = _("Segmentación de Pieza")
        verbose_name_plural = _("Segmentaciones de Piezas")
        ordering = ['-confianza']
    
    def __str__(self):
        return f"{self.clase} ({self.confianza:.2%})"


class EstadisticasSistema(models.Model):
    """Estadísticas del sistema de análisis"""
    
    fecha = models.DateField(
        _("Fecha"),
        unique=True,
        help_text="Fecha de las estadísticas"
    )
    
    # Estadísticas de análisis
    total_analisis = models.IntegerField(
        _("Total de análisis"),
        default=0,
        help_text="Número total de análisis realizados"
    )
    
    analisis_exitosos = models.IntegerField(
        _("Análisis exitosos"),
        default=0,
        help_text="Número de análisis completados exitosamente"
    )
    
    analisis_con_error = models.IntegerField(
        _("Análisis con error"),
        default=0,
        help_text="Número de análisis que fallaron"
    )
    
    # Estadísticas de segmentación
    total_defectos_detectados = models.IntegerField(
        _("Total defectos detectados"),
        default=0,
        help_text="Número total de defectos segmentados"
    )
    
    total_piezas_detectadas = models.IntegerField(
        _("Total piezas detectadas"),
        default=0,
        help_text="Número total de piezas segmentadas"
    )
    
    # Tiempos promedio (en milisegundos)
    tiempo_promedio_captura_ms = models.FloatField(
        _("Tiempo promedio captura (ms)"),
        default=0.0
    )
    
    tiempo_promedio_segmentacion_ms = models.FloatField(
        _("Tiempo promedio segmentación (ms)"),
        default=0.0
    )
    
    tiempo_promedio_total_ms = models.FloatField(
        _("Tiempo promedio total (ms)"),
        default=0.0
    )
    
    # Confianza promedio
    confianza_promedio = models.FloatField(
        _("Confianza promedio"),
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    class Meta:
        verbose_name = _("Estadísticas del Sistema")
        verbose_name_plural = _("Estadísticas del Sistema")
        ordering = ['-fecha']
    
    def __str__(self):
        return f"Estadísticas {self.fecha} - {self.total_analisis} análisis"
    
    @property
    def tasa_exito(self):
        """Calcula la tasa de éxito de los análisis"""
        if self.total_analisis == 0:
            return 0.0
        return (self.analisis_exitosos / self.total_analisis) * 100
    
    @property
    def promedio_defectos_por_analisis(self):
        """Calcula el promedio de defectos por análisis"""
        if self.analisis_exitosos == 0:
            return 0.0
        return self.total_defectos_detectados / self.analisis_exitosos
    
    @property
    def promedio_piezas_por_analisis(self):
        """Calcula el promedio de piezas por análisis"""
        if self.analisis_exitosos == 0:
            return 0.0
        return self.total_piezas_detectadas / self.analisis_exitosos
