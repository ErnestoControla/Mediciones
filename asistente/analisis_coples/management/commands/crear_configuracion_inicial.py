# analisis_coples/management/commands/crear_configuracion_inicial.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from analisis_coples.models import ConfiguracionSistema

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea una configuración inicial para el sistema de análisis de coples'

    def add_arguments(self, parser):
        parser.add_argument(
            '--nombre',
            type=str,
            default='Configuración Inicial',
            help='Nombre de la configuración'
        )
        parser.add_argument(
            '--ip-camara',
            type=str,
            default='172.16.1.21',
            help='IP de la cámara'
        )
        parser.add_argument(
            '--umbral-confianza',
            type=float,
            default=0.55,
            help='Umbral de confianza (0.0 - 1.0)'
        )
        parser.add_argument(
            '--umbral-iou',
            type=float,
            default=0.35,
            help='Umbral IoU (0.0 - 1.0)'
        )
        parser.add_argument(
            '--robustez',
            type=str,
            default='original',
            choices=['original', 'moderada', 'permisiva', 'ultra_permisiva'],
            help='Configuración de robustez'
        )
        parser.add_argument(
            '--activar',
            action='store_true',
            help='Activar esta configuración'
        )

    def handle(self, *args, **options):
        # Obtener o crear un usuario administrador
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(
                self.style.WARNING('No se encontró un usuario administrador. Creando configuración sin usuario.')
            )
            admin_user = None

        # Crear configuración
        configuracion = ConfiguracionSistema.objects.create(
            nombre=options['nombre'],
            ip_camara=options['ip_camara'],
            umbral_confianza=options['umbral_confianza'],
            umbral_iou=options['umbral_iou'],
            configuracion_robustez=options['robustez'],
            activa=options['activar'],
            creada_por=admin_user
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Configuración "{configuracion.nombre}" creada exitosamente con ID: {configuracion.id}'
            )
        )

        if configuracion.activa:
            self.stdout.write(
                self.style.SUCCESS('La configuración ha sido activada automáticamente.')
            )
        else:
            self.stdout.write(
                self.style.WARNING('La configuración no está activa. Use --activar para activarla.')
            )
