# analisis_coples/api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Crear router para las APIs
router = DefaultRouter()
router.register(r'configuraciones', views.ConfiguracionSistemaViewSet)
router.register(r'analisis', views.AnalisisCopleViewSet)
router.register(r'estadisticas', views.EstadisticasSistemaViewSet)
router.register(r'sistema', views.SistemaControlViewSet, basename='sistema')

app_name = 'analisis_coples_api'

urlpatterns = [
    # URLs del router
    path('', include(router.urls)),
]
