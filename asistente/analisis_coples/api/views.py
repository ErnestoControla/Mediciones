# analisis_coples/api/views.py

from rest_framework import status, generics, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from ..models import ConfiguracionSistema, AnalisisCople
from ..resultados_models import EstadisticasSistema
from ..services_real import servicio_analisis_real as servicio_analisis
from .serializers import (
    ConfiguracionSistemaSerializer,
    AnalisisCopleSerializer,
    AnalisisCopleListSerializer,
    EstadisticasSistemaSerializer,
    AnalisisRequestSerializer,
    ConfiguracionRequestSerializer
)

logger = logging.getLogger(__name__)


class ConfiguracionSistemaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar configuraciones del sistema"""
    
    queryset = ConfiguracionSistema.objects.all()
    serializer_class = ConfiguracionSistemaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar configuraciones por usuario si es necesario"""
        queryset = super().get_queryset()
        # Aquí podrías agregar filtros por usuario si es necesario
        return queryset.order_by('-fecha_creacion')
    
    def perform_create(self, serializer):
        """Asignar el usuario actual al crear la configuración"""
        serializer.save(creada_por=self.request.user)
    
    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        """Activar una configuración específica"""
        configuracion = self.get_object()
        
        # Desactivar todas las configuraciones
        ConfiguracionSistema.objects.filter(activa=True).update(activa=False)
        
        # Activar la configuración seleccionada
        configuracion.activa = True
        configuracion.save()
        
        # Reinicializar el sistema con la nueva configuración
        try:
            if servicio_analisis.inicializar_sistema(configuracion.id):
                return Response({
                    'message': f'Configuración "{configuracion.nombre}" activada correctamente',
                    'configuracion': ConfiguracionSistemaSerializer(configuracion).data
                })
            else:
                return Response({
                    'error': 'Error inicializando el sistema con la nueva configuración'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Error activando configuración: {e}")
            return Response({
                'error': f'Error activando configuración: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def activa(self, request):
        """Obtener la configuración activa"""
        configuracion = ConfiguracionSistema.objects.filter(activa=True).first()
        if configuracion:
            serializer = self.get_serializer(configuracion)
            return Response(serializer.data)
        else:
            return Response({
                'error': 'No hay configuración activa'
            }, status=status.HTTP_404_NOT_FOUND)


class AnalisisCopleViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar análisis de coples"""
    
    queryset = AnalisisCople.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Usar serializer detallado para retrieve, simplificado para list"""
        if self.action == 'retrieve':
            return AnalisisCopleSerializer
        elif self.action == 'create':
            return AnalisisRequestSerializer
        return AnalisisCopleListSerializer
    
    def get_queryset(self):
        """Filtrar análisis por usuario y otros criterios"""
        queryset = super().get_queryset()
        
        # Filtrar por usuario si no es superusuario
        if not self.request.user.is_superuser:
            queryset = queryset.filter(usuario=self.request.user)
        
        # Filtrar por tipo de análisis
        tipo_analisis = self.request.query_params.get('tipo_analisis')
        if tipo_analisis:
            queryset = queryset.filter(tipo_analisis=tipo_analisis)
        
        # Filtrar por estado
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Filtrar por fecha
        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        
        if fecha_desde:
            try:
                fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp_procesamiento__date__gte=fecha_desde)
            except ValueError:
                pass
        
        if fecha_hasta:
            try:
                fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp_procesamiento__date__lte=fecha_hasta)
            except ValueError:
                pass
        
        return queryset.order_by('-timestamp_procesamiento')
    
    def create(self, request):
        """
        Crea un nuevo análisis ejecutando segmentación y mediciones.
        
        Body params:
            tipo_analisis: 'medicion_piezas' o 'medicion_defectos'
            configuracion_id (opcional): ID de configuración a usar
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        tipo_analisis = serializer.validated_data['tipo_analisis']
        configuracion_id = serializer.validated_data.get('configuracion_id')
        
        try:
            # Inicializar sistema si es necesario
            if not servicio_analisis.inicializado:
                if not servicio_analisis.inicializar_sistema(configuracion_id):
                    return Response({
                        'error': 'Error inicializando el sistema de análisis'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Ejecutar análisis según el tipo
            if tipo_analisis == 'medicion_piezas':
                resultado = servicio_analisis.realizar_analisis_completo(request.user)
            elif tipo_analisis == 'medicion_defectos':
                resultado = servicio_analisis.realizar_analisis_completo(request.user)
            else:
                resultado = servicio_analisis.realizar_analisis_completo(request.user)
            
            if 'error' in resultado:
                return Response({
                    'error': resultado['error']
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Obtener el análisis creado
            analisis = AnalisisCople.objects.get(id_analisis=resultado['id_analisis'])
            serializer_response = AnalisisCopleSerializer(analisis)
            
            return Response(serializer_response.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creando análisis: {e}")
            return Response({
                'error': f'Error ejecutando análisis: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def realizar_analisis(self, request):
        """Realizar un nuevo análisis"""
        serializer = AnalisisRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        tipo_analisis = serializer.validated_data['tipo_analisis']
        configuracion_id = serializer.validated_data.get('configuracion_id')
        
        try:
            # Inicializar sistema si es necesario
            if not servicio_analisis.inicializado:
                if not servicio_analisis.inicializar_sistema(configuracion_id):
                    return Response({
                        'error': 'Error inicializando el sistema de análisis'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Realizar análisis según el tipo
            if tipo_analisis == 'completo':
                resultado = servicio_analisis.realizar_analisis_completo(request.user)
            elif tipo_analisis == 'clasificacion':
                resultado = servicio_analisis.realizar_analisis_clasificacion(request.user)
            else:
                # Para otros tipos de análisis, usar análisis completo por ahora
                resultado = servicio_analisis.realizar_analisis_completo(request.user)
            
            if 'error' in resultado:
                return Response(resultado, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Obtener el análisis creado
            analisis = AnalisisCople.objects.get(id_analisis=resultado['id_analisis'])
            serializer_response = AnalisisCopleSerializer(analisis)
            
            return Response({
                'message': 'Análisis completado exitosamente',
                'analisis': serializer_response.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error realizando análisis: {e}")
            return Response({
                'error': f'Error realizando análisis: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtener estadísticas de análisis"""
        try:
            # Estadísticas del sistema
            stats_sistema = servicio_analisis.obtener_estadisticas_sistema()
            
            # Estadísticas de la base de datos
            total_analisis = self.get_queryset().count()
            analisis_exitosos = self.get_queryset().filter(estado='completado').count()
            analisis_con_error = self.get_queryset().filter(estado='error').count()
            
            # Estadísticas por tipo
            stats_por_tipo = {}
            for tipo, _ in AnalisisCople.TIPO_ANALISIS_CHOICES:
                count = self.get_queryset().filter(tipo_analisis=tipo).count()
                stats_por_tipo[tipo] = count
            
            # Estadísticas de segmentación
            total_defectos = 0
            total_piezas = 0
            confianza_promedio = 0.0
            
            analisis_completados = self.get_queryset().filter(estado='completado')
            
            if analisis_completados.exists():
                # Contar defectos y piezas
                from ..resultados_models import SegmentacionDefecto, SegmentacionPieza
                
                total_defectos = SegmentacionDefecto.objects.filter(
                    analisis__in=analisis_completados
                ).count()
                
                total_piezas = SegmentacionPieza.objects.filter(
                    analisis__in=analisis_completados
                ).count()
                
                # Calcular confianza promedio de segmentaciones
                confianzas_defectos = SegmentacionDefecto.objects.filter(
                    analisis__in=analisis_completados
                ).values_list('confianza', flat=True)
                
                confianzas_piezas = SegmentacionPieza.objects.filter(
                    analisis__in=analisis_completados
                ).values_list('confianza', flat=True)
                
                todas_confianzas = list(confianzas_defectos) + list(confianzas_piezas)
                if todas_confianzas:
                    confianza_promedio = sum(todas_confianzas) / len(todas_confianzas)
            
            return Response({
                'sistema': stats_sistema,
                'base_datos': {
                    'total_analisis': total_analisis,
                    'analisis_exitosos': analisis_exitosos,
                    'analisis_con_error': analisis_con_error,
                    'tasa_exito': (analisis_exitosos / total_analisis * 100) if total_analisis > 0 else 0
                },
                'por_tipo': stats_por_tipo,
                'segmentacion': {
                    'total_defectos': total_defectos,
                    'total_piezas': total_piezas,
                    'confianza_promedio': confianza_promedio,
                    'promedio_por_analisis': {
                        'defectos': (total_defectos / analisis_exitosos) if analisis_exitosos > 0 else 0,
                        'piezas': (total_piezas / analisis_exitosos) if analisis_exitosos > 0 else 0
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return Response({
                'error': f'Error obteniendo estadísticas: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def recientes(self, request):
        """Obtener análisis recientes"""
        limite = int(request.query_params.get('limite', 10))
        queryset = self.get_queryset()[:limite]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class EstadisticasSistemaViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para estadísticas del sistema"""
    
    queryset = EstadisticasSistema.objects.all()
    serializer_class = EstadisticasSistemaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar estadísticas por rango de fechas"""
        queryset = super().get_queryset()
        
        # Filtrar por fecha
        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        
        if fecha_desde:
            try:
                fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha__gte=fecha_desde)
            except ValueError:
                pass
        
        if fecha_hasta:
            try:
                fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha__lte=fecha_hasta)
            except ValueError:
                pass
        
        return queryset.order_by('-fecha')
    
    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """Obtener resumen de estadísticas"""
        try:
            # Estadísticas del último mes
            fecha_limite = timezone.now().date() - timedelta(days=30)
            stats_recientes = self.get_queryset().filter(fecha__gte=fecha_limite)
            
            if stats_recientes.exists():
                # Calcular promedios
                total_analisis = sum(s.total_analisis for s in stats_recientes)
                analisis_exitosos = sum(s.analisis_exitosos for s in stats_recientes)
                total_aceptados = sum(s.total_aceptados for s in stats_recientes)
                total_rechazados = sum(s.total_rechazados for s in stats_recientes)
                
                return Response({
                    'periodo': 'Últimos 30 días',
                    'total_analisis': total_analisis,
                    'analisis_exitosos': analisis_exitosos,
                    'tasa_exito': (analisis_exitosos / total_analisis * 100) if total_analisis > 0 else 0,
                    'total_aceptados': total_aceptados,
                    'total_rechazados': total_rechazados,
                    'tasa_aceptacion': (total_aceptados / (total_aceptados + total_rechazados) * 100) 
                                      if (total_aceptados + total_rechazados) > 0 else 0
                })
            else:
                return Response({
                    'message': 'No hay estadísticas disponibles para el período seleccionado'
                })
                
        except Exception as e:
            logger.error(f"Error obteniendo resumen de estadísticas: {e}")
            return Response({
                'error': f'Error obteniendo resumen: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SistemaControlViewSet(viewsets.ViewSet):
    """ViewSet para control del sistema de análisis"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def estado(self, request):
        """Obtener estado del sistema"""
        try:
            estado = {
                'inicializado': servicio_analisis.inicializado,
                'configuracion_activa': None,
                'estadisticas': None
            }
            
            if servicio_analisis.configuracion_activa:
                estado['configuracion_activa'] = {
                    'id': servicio_analisis.configuracion_activa.id,
                    'nombre': servicio_analisis.configuracion_activa.nombre,
                    'umbral_confianza': servicio_analisis.configuracion_activa.umbral_confianza,
                    'configuracion_robustez': servicio_analisis.configuracion_activa.configuracion_robustez
                }
            
            if servicio_analisis.inicializado:
                estado['estadisticas'] = servicio_analisis.obtener_estadisticas_sistema()
            
            return Response(estado)
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del sistema: {e}")
            return Response({
                'error': f'Error obteniendo estado: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def inicializar(self, request):
        """Inicializar el sistema de análisis"""
        serializer = ConfiguracionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        configuracion_id = serializer.validated_data['configuracion_id']
        
        try:
            if servicio_analisis.inicializar_sistema(configuracion_id):
                return Response({
                    'message': 'Sistema inicializado correctamente',
                    'configuracion_id': configuracion_id
                })
            else:
                return Response({
                    'error': 'Error inicializando el sistema'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error inicializando sistema: {e}")
            return Response({
                'error': f'Error inicializando sistema: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def liberar(self, request):
        """Liberar recursos del sistema"""
        try:
            servicio_analisis.liberar_sistema()
            return Response({
                'message': 'Sistema liberado correctamente'
            })
        except Exception as e:
            logger.error(f"Error liberando sistema: {e}")
            return Response({
                'error': f'Error liberando sistema: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def capturar(self, request):
        """
        Captura una imagen desde la cámara activa.
        
        Returns:
            URL de la imagen capturada y ruta en servidor
        """
        try:
            from ..services.camera_service import get_camera_service
            import cv2
            import os
            from django.conf import settings
            from datetime import datetime
            
            camera_service = get_camera_service()
            
            # Verificar que hay cámara activa
            estado = camera_service.obtener_estado()
            if not estado['activa']:
                return Response({
                    'exito': False,
                    'error': 'No hay cámara inicializada. Inicializa la cámara primero.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Capturar imagen
            exito, imagen = camera_service.capturar_imagen()
            
            if not exito or imagen is None:
                return Response({
                    'exito': False,
                    'error': 'Error capturando imagen de la cámara'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Guardar imagen en media
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"captura_{timestamp}.jpg"
            
            # Crear directorio si no existe
            capturas_dir = os.path.join(settings.MEDIA_ROOT, 'capturas')
            os.makedirs(capturas_dir, exist_ok=True)
            
            # Guardar imagen
            filepath = os.path.join(capturas_dir, filename)
            cv2.imwrite(filepath, imagen)
            
            # URL relativa para el frontend
            imagen_url = f"/media/capturas/{filename}"
            
            logger.info(f"📸 Imagen capturada: {filename}")
            
            return Response({
                'exito': True,
                'imagen_url': imagen_url,
                'imagen_path': filepath,
                'timestamp': timestamp,
                'message': 'Imagen capturada correctamente'
            })
            
        except Exception as e:
            logger.error(f"Error capturando imagen: {e}")
            return Response({
                'exito': False,
                'error': f'Error capturando imagen: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
