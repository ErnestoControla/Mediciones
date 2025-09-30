# core/admin.py

from django.contrib import admin
from .models import Rol

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display  = ('rol_nombre',)
    search_fields = ('rol_nombre',)
