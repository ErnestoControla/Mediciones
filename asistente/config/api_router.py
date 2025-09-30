# config/api_router.py

from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from asistente.users.api.views import (
    UserViewSet,
    UserRegistrationView,
    UserProfileView,
)
from core.api.views import RolViewSet
from analisis_coples.api.views import (
    ConfiguracionSistemaViewSet,
    AnalisisCopleViewSet,
    EstadisticasSistemaViewSet,
    SistemaControlViewSet
)
from analisis_coples.api import image_views

# Seleccionamos DefaultRouter en DEBUG para endpoint raiz y SimpleRouter en producción
router = DefaultRouter() if settings.DEBUG else SimpleRouter()

# Registramos los ViewSets
router.register(r"users", UserViewSet)
router.register(r"roles", RolViewSet, basename="role")

# APIs del sistema de análisis de coples
router.register(r"analisis/configuraciones", ConfiguracionSistemaViewSet, basename="configuraciones")
router.register(r"analisis/resultados", AnalisisCopleViewSet, basename="analisis")
router.register(r"analisis/estadisticas", EstadisticasSistemaViewSet, basename="estadisticas")
router.register(r"analisis/sistema", SistemaControlViewSet, basename="sistema")

app_name = "api"
urlpatterns = [
    # Endpoints de autenticación y perfil
    path("users/register/", UserRegistrationView.as_view(), name="users-register"),  # POST /api/users/register/
    path("users/me/",       UserProfileView.as_view(),    name="users-me"),        # GET  /api/users/me/

    # Endpoints CRUD para Users y Roles
    *router.urls,
    
    # URLs para imágenes procesadas del sistema de análisis
    path("analisis/imagenes/procesada/<int:analisis_id>/", image_views.get_processed_image, name="imagen-procesada"),
    path("analisis/imagenes/miniatura/<int:analisis_id>/", image_views.get_analysis_thumbnail, name="imagen-miniatura"),
    path("analisis/imagenes/test/", image_views.test_image, name="imagen-test"),
]
