# asistente/users/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from core.models import Rol  # importamos el modelo Rol

class User(AbstractUser):
    """
    Custom user model for Asistente Controla.
    Ahora enlaza con core.Rol y permite null/blank para la migración inicial.
    """

    name = models.CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None   # type: ignore[assignment]

    rol = models.ForeignKey(
        Rol,
        on_delete=models.PROTECT,
        verbose_name=_("Rol"),
        related_name="users",
        null=True,    # permitir NULL para no romper la migración
        blank=True,   # permitir vacío en formularios admin
    )

    def get_absolute_url(self) -> str:
        return reverse("users:detail", kwargs={"username": self.username})
