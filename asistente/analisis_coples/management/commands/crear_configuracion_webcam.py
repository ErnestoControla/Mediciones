from django.core.management.base import BaseCommand
from analisis_coples.models import ConfiguracionSistema


class Command(BaseCommand):
    help = 'Crea una configuración específica para webcam USB'

    def add_arguments(self, parser):
        parser.add_argument(
            '--activar',
            action='store_true',
            help='Activar la configuración después de crearla',
        )

    def handle(self, *args, **options):
        # Crear configuración para webcam USB
        configuracion = ConfiguracionSistema.objects.create(
            nombre="Webcam USB - Configuración Local",
            ip_camara="127.0.0.1",  # Localhost para webcam USB
            umbral_confianza=0.5,  # 50% como especificado en las memorias
            configuracion_robustez="moderada",  # Balanceada para webcam
            activa=options['activar']
        )

        if options['activar']:
            # Desactivar otras configuraciones
            ConfiguracionSistema.objects.exclude(id=configuracion.id).update(activa=False)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Configuración "Webcam USB - Configuración Local" creada y activada exitosamente con ID: {configuracion.id}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Configuración "Webcam USB - Configuración Local" creada exitosamente con ID: {configuracion.id}'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    'La configuración no está activa. Use --activar para activarla.'
                )
            )
