# asistente/users/api/views.py

from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import generics

from asistente.users.api.serializers import UserSerializer, UserRegistrationSerializer

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """
    POST /api/users/register/
    Registra un nuevo usuario.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    authentication_classes = []  # si usas JWT, puedes dejarlo vacío


class UserProfileView(APIView):
    """
    GET /api/users/me/
    Recupera los datos del usuario autenticado.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD completo de usuarios (GET, POST, PUT, PATCH, DELETE)
    - list:   GET    /api/users/
    - retrieve: GET  /api/users/{id}/
    - create:  POST  /api/users/
    - update:  PUT   /api/users/{id}/
    - partial_update: PATCH /api/users/{id}/
    - destroy: DELETE /api/users/{id}/
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]  # o IsAdminUser, según lo que necesites

    def get_queryset(self):
        # si sólo quieres exponer todos los usuarios a admins, retira este filtro
        return User.objects.all()
