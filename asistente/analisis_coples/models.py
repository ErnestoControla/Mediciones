# analisis_coples/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator


class ConfiguracionSistema(models.Model):
    """Configuración del sistema de análisis de coples"""
    
    nombre = models.CharField(
        _("Nombre de configuración"), 
        max_length=100, 
        unique=True,
        help_text="Nombre descriptivo de la configuración"
    )
    
    # Configuración de cámara
    ip_camara = models.GenericIPAddressField(
        _("IP de la cámara"), 
        default="172.16.1.21",
        help_text="Dirección IP de la cámara GigE"
    )
    
    # Configuración de modelos
    umbral_confianza = models.FloatField(
        _("Umbral de confianza"),
        default=0.55,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Umbral mínimo de confianza para detecciones (0.0 - 1.0)"
    )
    
    umbral_iou = models.FloatField(
        _("Umbral IoU"),
        default=0.35,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Umbral IoU para supresión de no máximos (0.0 - 1.0)"
    )
    
    # Configuración de robustez
    configuracion_robustez = models.CharField(
        _("Configuración de robustez"),
        max_length=20,
        choices=[
            ('original', 'Original - Alta precisión'),
            ('moderada', 'Moderada - Balanceada'),
            ('permisiva', 'Permisiva - Alta sensibilidad'),
            ('ultra_permisiva', 'Ultra Permisiva - Condiciones extremas'),
        ],
        default='original',
        help_text="Configuración de robustez del sistema"
    )
    
    # Metadatos
    activa = models.BooleanField(
        _("Configuración activa"),
        default=False,
        help_text="Indica si esta es la configuración activa del sistema"
    )
    
    creada_por = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Creada por"),
        related_name="configuraciones_creadas"
    )
    
    fecha_creacion = models.DateTimeField(_("Fecha de creación"), auto_now_add=True)
    fecha_modificacion = models.DateTimeField(_("Fecha de modificación"), auto_now=True)
    
    class Meta:
        verbose_name = _("Configuración del Sistema")
        verbose_name_plural = _("Configuraciones del Sistema")
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre} ({'Activa' if self.activa else 'Inactiva'})"
    
    def save(self, *args, **kwargs):
        # Asegurar que solo una configuración esté activa
        if self.activa:
            ConfiguracionSistema.objects.filter(activa=True).update(activa=False)
        super().save(*args, **kwargs)


class AnalisisCople(models.Model):
    """Resultado de un análisis completo de cople"""
    
    ESTADO_CHOICES = [
        ('procesando', 'Procesando'),
        ('completado', 'Completado'),
        ('error', 'Error'),
    ]
    
    TIPO_ANALISIS_CHOICES = [
        ('completo', 'Análisis Completo'),
        ('clasificacion', 'Solo Clasificación'),
        ('deteccion_piezas', 'Solo Detección de Piezas'),
        ('deteccion_defectos', 'Solo Detección de Defectos'),
        ('segmentacion_defectos', 'Solo Segmentación de Defectos'),
        ('segmentacion_piezas', 'Solo Segmentación de Piezas'),
    ]
    
    # Identificación
    id_analisis = models.CharField(
        _("ID de análisis"),
        max_length=50,
        unique=True,
        help_text="Identificador único del análisis"
    )
    
    # Metadatos básicos
    timestamp_captura = models.DateTimeField(
        _("Timestamp de captura"),
        help_text="Momento en que se capturó la imagen"
    )
    
    timestamp_procesamiento = models.DateTimeField(
        _("Timestamp de procesamiento"),
        auto_now_add=True,
        help_text="Momento en que se procesó el análisis"
    )
    
    tipo_analisis = models.CharField(
        _("Tipo de análisis"),
        max_length=30,
        choices=TIPO_ANALISIS_CHOICES,
        default='completo'
    )
    
    estado = models.CharField(
        _("Estado"),
        max_length=20,
        choices=ESTADO_CHOICES,
        default='procesando'
    )
    
    # Configuración utilizada
    configuracion = models.ForeignKey(
        ConfiguracionSistema,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Configuración utilizada"),
        related_name="analisis_realizados"
    )
    
    # Usuario que realizó el análisis
    usuario = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Usuario"),
        related_name="analisis_realizados"
    )
    
    # Archivos generados
    archivo_imagen = models.CharField(
        _("Archivo de imagen"),
        max_length=255,
        help_text="Nombre del archivo de imagen generado"
    )
    
    archivo_json = models.CharField(
        _("Archivo JSON"),
        max_length=255,
        help_text="Nombre del archivo JSON con metadatos"
    )
    
    # Información de la imagen
    resolucion_ancho = models.IntegerField(_("Ancho de imagen"))
    resolucion_alto = models.IntegerField(_("Alto de imagen"))
    resolucion_canales = models.IntegerField(_("Canales de imagen"))
    
    # Tiempos de procesamiento (en milisegundos)
    tiempo_captura_ms = models.FloatField(_("Tiempo de captura (ms)"))
    tiempo_clasificacion_ms = models.FloatField(_("Tiempo de clasificación (ms)"))
    tiempo_deteccion_piezas_ms = models.FloatField(_("Tiempo de detección piezas (ms)"))
    tiempo_deteccion_defectos_ms = models.FloatField(_("Tiempo de detección defectos (ms)"))
    tiempo_segmentacion_defectos_ms = models.FloatField(_("Tiempo de segmentación defectos (ms)"))
    tiempo_segmentacion_piezas_ms = models.FloatField(_("Tiempo de segmentación piezas (ms)"))
    tiempo_total_ms = models.FloatField(_("Tiempo total (ms)"))
    
    # Metadatos JSON completos
    metadatos_json = models.JSONField(
        _("Metadatos JSON"),
        default=dict,
        help_text="Metadatos completos del análisis en formato JSON"
    )
    
    # Mensaje de error (si aplica)
    mensaje_error = models.TextField(
        _("Mensaje de error"),
        blank=True,
        help_text="Mensaje de error si el análisis falló"
    )
    
    class Meta:
        verbose_name = _("Análisis de Cople")
        verbose_name_plural = _("Análisis de Coples")
        ordering = ['-timestamp_procesamiento']
        indexes = [
            models.Index(fields=['timestamp_procesamiento']),
            models.Index(fields=['estado']),
            models.Index(fields=['tipo_analisis']),
            models.Index(fields=['usuario']),
        ]
    
    def __str__(self):
        return f"Análisis {self.id_analisis} - {self.get_estado_display()}"


# Importar modelos de resultados
from .resultados_models import (
    ResultadoClasificacion,
    DeteccionPieza,
    DeteccionDefecto,
    SegmentacionDefecto,
    SegmentacionPieza,
    EstadisticasSistema
)