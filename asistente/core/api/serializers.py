# core/api/serializers.py

from rest_framework import serializers
from core.models import Rol

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Rol
        fields = ("id", "rol_nombre", "rol_descripcion")
