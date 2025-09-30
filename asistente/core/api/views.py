# core/api/views.py

from rest_framework import viewsets, permissions
from core.models import Rol
from .serializers import RolSerializer

class RolViewSet(viewsets.ModelViewSet):
    """
    CRUD completo para Roles:
      - list/retrieve (GET)
      - create       (POST)
      - update       (PUT/PATCH)
      - destroy      (DELETE)
    """
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [permissions.IsAuthenticated]  # o IsAdminUser si solo admin crea roles
