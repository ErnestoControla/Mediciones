# core/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _

class Rol(models.Model):
    rol_nombre      = models.CharField(_("Nombre del rol"), max_length=100, unique=True)
    rol_descripcion = models.TextField(_("Descripción"), blank=True)

    class Meta:
        verbose_name = _("Rol")
        verbose_name_plural = _("Roles")
        ordering = ['rol_nombre']

    def __str__(self):
        return self.rol_nombre
