# core/management/commands/crear_datos_iniciales.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from core.models import (
    Rol,
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea datos iniciales para el sistema'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Creando datos iniciales...')

        # 1) ROLES
        roles = [
            ('Administrador',
             'Encargado de la gestión operativa diaria. Supervisa procesos internos, coordina recursos y asegura que los procedimientos se cumplan correctamente.'),
            ('Administrador de Sistemas',
             'Especialista en infraestructura tecnológica. Instala, configura y mantiene servidores, redes y aplicativos. Gestiona accesos, monitorea rendimiento y garantiza la seguridad y disponibilidad de los sistemas informáticos.'),
            ('Director',
             'Responsable de la dirección estratégica de la compañía. Define la visión, objetivos a largo plazo y supervisa el cumplimiento de las metas corporativas. Toma decisiones clave sobre inversiones, alianzas y expansión de negocio.'),
            ('Gerente de ventas',
             'Lidera el equipo de ventas y diseña las estrategias comerciales para alcanzar los objetivos de facturación. Establece metas de captación de clientes, analiza indicadores de ventas y coordina acciones de marketing para impulsar el crecimiento de los ingresos.'),
            ('Super Administrador',
             'Usuario con privilegios absolutos sobre la plataforma. Puede gestionar configuraciones de sistema, crear/editar/eliminar cualquier recurso y acceder a todos los informes y logs.'),
        ]
        for nombre, descripcion in roles:
            obj, created = Rol.objects.get_or_create(
                rol_nombre=nombre,
                defaults={'rol_descripcion': descripcion}
            )
            if created:
                self.stdout.write(f'  ✔ Rol: {nombre}')


        # 3) SUPERUSUARIO
        try:
            if not User.objects.filter(username='controla').exists():
                User.objects.create_superuser(
                    username='controla',
                    email='controla@controla.com',
                    password='Controla2025$',
                    rol=Rol.objects.get(rol_nombre='Super Administrador'),
                    name='Tecnologías Controla',
                )
                self.stdout.write('  🛡️ Superusuario controla creado')
        except IntegrityError as e:
            self.stderr.write(f'  ❗ No se pudo crear superusuario: {e}')

        # 4) USUARIOS ADICIONALES
        password_comun = 'asistente123'
        perfiles = [
            ('usuario1', 'u1@example.com'),
            ('usuario2', 'u2@example.com'),
            ('usuario3', 'u3@example.com'),
            ('usuario4', 'u4@example.com'),
            ('usuario5', 'u5@example.com'),
        ]
        rol_admin     = Rol.objects.get(rol_nombre='Administrador')

        for uname, email in perfiles:
            if User.objects.filter(username=uname).exists():
                continue
            User.objects.create_user(
                username      = uname,
                email         = email,
                password      = password_comun,
                rol           = rol_admin,
                name          = uname.capitalize(),
            )
            self.stdout.write(f'  👤 Usuario creado: {uname} / {email}')



        self.stdout.write(self.style.SUCCESS('✔ Datos iniciales creados exitosamente.'))
