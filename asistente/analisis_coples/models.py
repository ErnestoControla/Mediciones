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
        default="172.16.1.24",
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
    
    # Configuración de conversión píxeles → milímetros
    distancia_camara_mm = models.FloatField(
        _("Distancia cámara-objeto (mm)"),
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0)],
        help_text="Distancia entre la cámara y el objeto en milímetros"
    )
    
    factor_conversion_px_mm = models.FloatField(
        _("Factor de conversión px → mm"),
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0)],
        help_text="Factor de conversión de píxeles a milímetros (mm/px)"
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
        ('medicion_piezas', 'Medición de Piezas'),
        ('medicion_defectos', 'Medición de Defectos'),
        ('rutina_inspeccion', 'Rutina de Inspección Multi-Ángulo'),
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
        default='medicion_piezas'
    )
    
    # Campos para rutinas de inspección
    es_rutina = models.BooleanField(
        _("Es parte de rutina"),
        default=False,
        help_text="Indica si este análisis es parte de una rutina de inspección"
    )
    
    rutina_padre = models.ForeignKey(
        'RutinaInspeccion',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Rutina padre"),
        related_name="analisis_individuales",
        help_text="Rutina de inspección a la que pertenece este análisis"
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
    tiempo_segmentacion_defectos_ms = models.FloatField(
        _("Tiempo de segmentación defectos (ms)"), 
        null=True, 
        blank=True
    )
    tiempo_segmentacion_piezas_ms = models.FloatField(
        _("Tiempo de segmentación piezas (ms)"), 
        null=True, 
        blank=True
    )
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


class RutinaInspeccion(models.Model):
    """Rutina de inspección multi-ángulo de un cople"""
    
    ESTADO_CHOICES = [
        ('en_progreso', 'En Progreso'),
        ('completado', 'Completado'),
        ('error', 'Error'),
    ]
    
    # Identificación
    id_rutina = models.CharField(
        _("ID de rutina"),
        max_length=50,
        unique=True,
        help_text="Identificador único de la rutina de inspección"
    )
    
    # Timestamps
    timestamp_inicio = models.DateTimeField(
        _("Timestamp de inicio"),
        help_text="Momento en que se inició la rutina"
    )
    
    timestamp_fin = models.DateTimeField(
        _("Timestamp de finalización"),
        null=True,
        blank=True,
        help_text="Momento en que se finalizó la rutina"
    )
    
    # Estado
    estado = models.CharField(
        _("Estado"),
        max_length=20,
        choices=ESTADO_CHOICES,
        default='en_progreso'
    )
    
    # Configuración utilizada
    configuracion = models.ForeignKey(
        ConfiguracionSistema,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Configuración utilizada"),
        related_name="rutinas_realizadas"
    )
    
    # Usuario que realizó la rutina
    usuario = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Usuario"),
        related_name="rutinas_realizadas"
    )
    
    # Información de capturas
    num_imagenes_capturadas = models.IntegerField(
        _("Número de imágenes capturadas"),
        default=0,
        help_text="Debe ser 6 para una rutina completa"
    )
    
    # Archivos generados
    imagen_consolidada = models.CharField(
        _("Imagen consolidada"),
        max_length=255,
        blank=True,
        help_text="Nombre del archivo de imagen consolidada"
    )
    
    # Reporte consolidado
    reporte_json = models.JSONField(
        _("Reporte consolidado"),
        default=dict,
        help_text="Resumen consolidado de las 6 mediciones"
    )
    
    # Mensaje de error (si aplica)
    mensaje_error = models.TextField(
        _("Mensaje de error"),
        blank=True,
        help_text="Mensaje de error si la rutina falló"
    )
    
    class Meta:
        verbose_name = _("Rutina de Inspección")
        verbose_name_plural = _("Rutinas de Inspección")
        ordering = ['-timestamp_inicio']
        indexes = [
            models.Index(fields=['timestamp_inicio']),
            models.Index(fields=['estado']),
            models.Index(fields=['usuario']),
        ]
    
    def __str__(self):
        return f"Rutina {self.id_rutina} - {self.get_estado_display()} ({self.num_imagenes_capturadas}/6)"


class EstadoCamara(models.Model):
    """Estado actual de la cámara GigE (singleton)"""
    
    # Solo debe existir un registro
    singleton_id = models.BooleanField(
        default=True,
        unique=True,
        help_text="Garantiza que solo exista un registro"
    )
    
    # Estado de la cámara
    activa = models.BooleanField(
        _("Cámara activa"),
        default=False,
        help_text="Indica si la cámara está inicializada"
    )
    
    en_preview = models.BooleanField(
        _("En previsualización"),
        default=False,
        help_text="Indica si está transmitiendo preview"
    )
    
    hibernada = models.BooleanField(
        _("Hibernada"),
        default=False,
        help_text="Indica si está en modo hibernación"
    )
    
    # Modelo cargado en memoria
    modelo_cargado = models.CharField(
        _("Modelo cargado"),
        max_length=20,
        choices=[
            ('piezas', 'Modelo de Piezas'),
            ('defectos', 'Modelo de Defectos'),
            ('ninguno', 'Ninguno'),
        ],
        default='ninguno',
        help_text="Modelo ONNX actualmente cargado en memoria"
    )
    
    # Frame rate actual
    frame_rate_actual = models.IntegerField(
        _("Frame rate actual (FPS)"),
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        help_text="Cuadros por segundo del preview"
    )
    
    # Timestamps
    ultimo_uso = models.DateTimeField(
        _("Último uso"),
        auto_now=True,
        help_text="Última vez que se usó la cámara"
    )
    
    ultima_actualizacion = models.DateTimeField(
        _("Última actualización"),
        auto_now=True,
        help_text="Última actualización del estado"
    )
    
    class Meta:
        verbose_name = _("Estado de Cámara")
        verbose_name_plural = _("Estado de Cámara")
    
    def __str__(self):
        estado = "Activa" if self.activa else "Inactiva"
        if self.hibernada:
            estado = "Hibernada"
        elif self.en_preview:
            estado = f"Preview {self.frame_rate_actual} FPS"
        return f"Cámara: {estado} - Modelo: {self.get_modelo_cargado_display()}"
    
    def save(self, *args, **kwargs):
        # Garantizar singleton
        self.singleton_id = True
        super().save(*args, **kwargs)
    
    @classmethod
    def get_estado(cls):
        """Obtener o crear el estado de la cámara (singleton)"""
        estado, created = cls.objects.get_or_create(singleton_id=True)
        return estado


# Importar modelos de resultados de segmentación
from .resultados_models import (
    SegmentacionDefecto,
    SegmentacionPieza,
    EstadisticasSistema
)