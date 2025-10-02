"""
API REST para control de cámara GigE y preview.

Endpoints:
- POST /api/camara/inicializar/      - Inicializar cámara
- POST /api/camara/liberar/          - Liberar cámara
- POST /api/camara/preview/iniciar/  - Iniciar preview
- POST /api/camara/preview/detener/  - Detener preview
- POST /api/camara/preview/reactivar/- Reactivar desde hibernación
- GET  /api/camara/preview/frame/    - Obtener frame actual
- GET  /api/camara/estado/           - Obtener estado actual
"""

import logging
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import HttpResponse

from ..services.camera_service import get_camera_service
from ..models import EstadoCamara
from .serializers import EstadoCamaraSerializer

logger = logging.getLogger(__name__)


class CamaraControlViewSet(viewsets.ViewSet):
    """
    ViewSet para control de la cámara GigE y preview.
    """
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.camera_service = get_camera_service()
    
    @action(detail=False, methods=['post'])
    def inicializar(self, request):
        """
        Inicializa la cámara GigE.
        
        Body params:
            ip_camara (str, optional): IP de la cámara (default: 172.16.1.24)
        """
        try:
            ip_camara = request.data.get('ip_camara', '172.16.1.24')
            
            resultado = self.camera_service.inicializar_camara(ip_camara)
            
            if resultado['success']:
                return Response(resultado, status=status.HTTP_200_OK)
            else:
                return Response(resultado, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error en endpoint inicializar: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def liberar(self, request):
        """Libera la cámara y detiene preview"""
        try:
            resultado = self.camera_service.liberar_camara()
            
            if resultado['success']:
                return Response(resultado, status=status.HTTP_200_OK)
            else:
                return Response(resultado, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error en endpoint liberar: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def estado(self, request):
        """Obtiene el estado actual de la cámara"""
        try:
            estado_info = self.camera_service.obtener_estado()
            
            # Obtener también el modelo de BD
            estado_bd = EstadoCamara.get_estado()
            serializer = EstadoCamaraSerializer(estado_bd)
            
            return Response({
                'estado_servicio': estado_info,
                'estado_bd': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error en endpoint estado: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='preview/iniciar')
    def preview_iniciar(self, request):
        """
        Inicia el preview de la cámara.
        
        Body params:
            fps (int, optional): FPS del preview (default: 5)
        """
        try:
            fps = int(request.data.get('fps', 5))
            
            if fps < 1 or fps > 30:
                return Response({
                    'error': 'FPS debe estar entre 1 y 30'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            resultado = self.camera_service.iniciar_preview(fps)
            
            if resultado['success']:
                return Response(resultado, status=status.HTTP_200_OK)
            else:
                return Response(resultado, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error en endpoint preview_iniciar: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='preview/detener')
    def preview_detener(self, request):
        """Detiene el preview de la cámara"""
        try:
            resultado = self.camera_service.detener_preview()
            
            if resultado['success']:
                return Response(resultado, status=status.HTTP_200_OK)
            else:
                return Response(resultado, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error en endpoint preview_detener: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='preview/reactivar')
    def preview_reactivar(self, request):
        """
        Reactiva el preview desde hibernación.
        
        Body params:
            fps (int, optional): FPS del preview (default: 5)
        """
        try:
            fps = int(request.data.get('fps', 5))
            
            # Resetear timer de hibernación
            self.camera_service.resetear_timer_hibernacion()
            
            resultado = self.camera_service.reactivar_preview(fps)
            
            if resultado['success']:
                return Response(resultado, status=status.HTTP_200_OK)
            else:
                return Response(resultado, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error en endpoint preview_reactivar: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='preview/frame', permission_classes=[AllowAny])
    def preview_frame(self, request):
        """
        Obtiene el frame actual del preview como imagen JPEG.
        
        Endpoint público (no requiere autenticación) para permitir carga desde <img> tag.
        
        Returns:
            HttpResponse con imagen JPEG
        """
        try:
            # NO resetear timer aquí - la solicitud automática de frames
            # no cuenta como interacción del usuario para hibernación
            
            frame_bytes = self.camera_service.obtener_frame_preview()
            
            if frame_bytes:
                return HttpResponse(
                    frame_bytes,
                    content_type='image/jpeg',
                    headers={
                        'Cache-Control': 'no-cache, no-store, must-revalidate',
                        'Pragma': 'no-cache',
                        'Expires': '0'
                    }
                )
            else:
                return Response({
                    'error': 'No hay frame disponible'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Error en endpoint preview_frame: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

