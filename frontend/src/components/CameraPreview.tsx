/**
 * Componente de preview de cámara GigE
 * 
 * Funcionalidades:
 * - Preview en tiempo real a 5 FPS (polling cada 200ms)
 * - Control de inicialización/liberación de cámara
 * - Control de preview (iniciar/detener)
 * - Detección y reactivación desde hibernación
 * - Indicadores visuales de estado
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Button,
  Typography,
  Alert,
  Chip,
  Stack,
  CircularProgress,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Videocam,
  VideocamOff,
  PlayArrow,
  Pause,
  Refresh,
  PowerSettingsNew,
  CameraAlt,
  HourglassEmpty
} from '@mui/icons-material';

import {
  inicializarCamara,
  liberarCamara,
  obtenerEstadoCamara,
  iniciarPreview,
  detenerPreview,
  reactivarPreview,
  getPreviewFrameUrl,
  EstadoCamaraResponse
} from '../api/camara';
import Swal from '../utils/swal';

const CameraPreview: React.FC = () => {
  const [estado, setEstado] = useState<EstadoCamaraResponse | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [frameTimestamp, setFrameTimestamp] = useState<number>(0);
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  /**
   * Obtiene el estado de la cámara
   */
  const cargarEstado = useCallback(async () => {
    try {
      const data = await obtenerEstadoCamara();
      setEstado(data);
      setError(null);
    } catch (err: any) {
      console.error('Error cargando estado:', err);
      setError(err.response?.data?.error || 'Error cargando estado');
    }
  }, []);

  /**
   * Inicializa la cámara
   */
  const handleInicializar = async () => {
    setCargando(true);
    try {
      const result = await inicializarCamara({ ip_camara: '172.16.1.24' });
      
      if (result.success) {
        await Swal.fire({
          title: '¡Cámara Inicializada!',
          text: result.message,
          icon: 'success',
          timer: 2000
        });
        await cargarEstado();
      } else {
        throw new Error(result.error);
      }
    } catch (err: any) {
      await Swal.fire({
        title: 'Error',
        text: err.response?.data?.error || err.message || 'Error inicializando cámara',
        icon: 'error'
      });
    } finally {
      setCargando(false);
    }
  };

  /**
   * Libera la cámara
   */
  const handleLiberar = async () => {
    const confirmar = await Swal.fire({
      title: '¿Liberar cámara?',
      text: 'Se detendrá el preview y se liberarán los recursos',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Sí, liberar',
      cancelButtonText: 'Cancelar'
    });

    if (!confirmar.isConfirmed) return;

    setCargando(true);
    try {
      const result = await liberarCamara();
      
      if (result.success) {
        await Swal.fire({
          title: 'Cámara Liberada',
          text: result.message,
          icon: 'success',
          timer: 2000
        });
        await cargarEstado();
        detenerPolling();
      } else {
        throw new Error(result.error);
      }
    } catch (err: any) {
      await Swal.fire({
        title: 'Error',
        text: err.response?.data?.error || err.message || 'Error liberando cámara',
        icon: 'error'
      });
    } finally {
      setCargando(false);
    }
  };

  /**
   * Inicia el preview
   */
  const handleIniciarPreview = async () => {
    setCargando(true);
    try {
      const result = await iniciarPreview({ fps: 5 });
      
      if (result.success) {
        await cargarEstado();
        iniciarPolling();
        
        await Swal.fire({
          title: 'Preview Iniciado',
          text: `Preview activo a ${result.fps} FPS`,
          icon: 'success',
          timer: 2000
        });
      } else {
        throw new Error(result.error);
      }
    } catch (err: any) {
      await Swal.fire({
        title: 'Error',
        text: err.response?.data?.error || err.message || 'Error iniciando preview',
        icon: 'error'
      });
    } finally {
      setCargando(false);
    }
  };

  /**
   * Detiene el preview
   */
  const handleDetenerPreview = async () => {
    setCargando(true);
    try {
      const result = await detenerPreview();
      
      if (result.success) {
        await cargarEstado();
        detenerPolling();
        
        await Swal.fire({
          title: 'Preview Detenido',
          text: result.message,
          icon: 'info',
          timer: 2000
        });
      } else {
        throw new Error(result.error);
      }
    } catch (err: any) {
      await Swal.fire({
        title: 'Error',
        text: err.response?.data?.error || err.message || 'Error deteniendo preview',
        icon: 'error'
      });
    } finally {
      setCargando(false);
    }
  };

  /**
   * Reactiva desde hibernación
   */
  const handleReactivar = async () => {
    setCargando(true);
    try {
      const result = await reactivarPreview({ fps: 5 });
      
      if (result.success) {
        await cargarEstado();
        iniciarPolling();
        
        await Swal.fire({
          title: 'Preview Reactivado',
          text: 'Cámara reactivada desde hibernación',
          icon: 'success',
          timer: 2000
        });
      } else {
        throw new Error(result.error);
      }
    } catch (err: any) {
      await Swal.fire({
        title: 'Error',
        text: err.response?.data?.error || err.message || 'Error reactivando preview',
        icon: 'error'
      });
    } finally {
      setCargando(false);
    }
  };

  /**
   * Inicia el polling de frames
   */
  const iniciarPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    // Polling cada 200ms (5 FPS)
    intervalRef.current = setInterval(() => {
      setFrameTimestamp(Date.now());
    }, 200);
  };

  /**
   * Detiene el polling de frames
   */
  const detenerPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setPreviewUrl('');
  };

  /**
   * Actualiza la URL del frame con timestamp para evitar cache
   */
  useEffect(() => {
    if (estado?.estado_bd.en_preview && !estado?.estado_bd.hibernada) {
      const baseUrl = getPreviewFrameUrl();
      const token = localStorage.getItem('access_token');
      setPreviewUrl(`${baseUrl}?t=${frameTimestamp}&token=${token}`);
    }
  }, [frameTimestamp, estado]);

  /**
   * Carga el estado inicial y configura polling si está en preview
   */
  useEffect(() => {
    cargarEstado();

    // Polling del estado cada 5 segundos
    const estadoInterval = setInterval(cargarEstado, 5000);

    return () => {
      clearInterval(estadoInterval);
      detenerPolling();
    };
  }, [cargarEstado]);

  /**
   * Controla el polling según el estado
   */
  useEffect(() => {
    if (estado?.estado_bd.en_preview && !estado?.estado_bd.hibernada) {
      iniciarPolling();
    } else {
      detenerPolling();
    }
  }, [estado?.estado_bd.en_preview, estado?.estado_bd.hibernada]);

  /**
   * Renderiza el chip de estado
   */
  const renderEstadoChip = () => {
    if (!estado) return null;

    const { activa, en_preview, hibernada, modelo_cargado } = estado.estado_bd;

    if (hibernada) {
      return (
        <Chip
          icon={<HourglassEmpty />}
          label="Hibernada"
          color="warning"
          size="small"
        />
      );
    }

    if (en_preview) {
      return (
        <Chip
          icon={<Videocam />}
          label={`Preview ${estado.estado_bd.frame_rate_actual} FPS`}
          color="success"
          size="small"
        />
      );
    }

    if (activa) {
      return (
        <Chip
          icon={<CameraAlt />}
          label="Activa"
          color="primary"
          size="small"
        />
      );
    }

    return (
      <Chip
        icon={<VideocamOff />}
        label="Inactiva"
        color="default"
        size="small"
      />
    );
  };

  return (
    <Card>
      <CardHeader
        title="Control de Cámara GigE"
        subheader="Preview en tiempo real y control de hibernación"
        action={
          <Stack direction="row" spacing={1} alignItems="center">
            {renderEstadoChip()}
            {estado?.estado_servicio.usando_webcam && (
              <Chip label="Webcam Fallback" size="small" color="info" />
            )}
            {estado && (
              <Typography variant="caption" color="text.secondary">
                Modelo: {estado.estado_bd.modelo_cargado_display}
              </Typography>
            )}
          </Stack>
        }
      />
      
      <CardContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Área de preview */}
        <Box
          sx={{
            width: '100%',
            height: 480,
            backgroundColor: '#000',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 1,
            mb: 2,
            position: 'relative'
          }}
        >
          {estado?.estado_bd.en_preview && !estado?.estado_bd.hibernada ? (
            <img
              ref={imgRef}
              src={previewUrl}
              alt="Camera Preview"
              style={{
                maxWidth: '100%',
                maxHeight: '100%',
                objectFit: 'contain'
              }}
              onError={() => {
                // Silenciosamente continuar si hay error de carga
              }}
            />
          ) : estado?.estado_bd.hibernada ? (
            <Box textAlign="center">
              <HourglassEmpty sx={{ fontSize: 80, color: 'warning.main', mb: 2 }} />
              <Typography variant="h6" color="warning.main">
                Cámara Hibernada
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Inactiva por más de 1 minuto
              </Typography>
            </Box>
          ) : estado?.estado_bd.activa ? (
            <Box textAlign="center">
              <VideocamOff sx={{ fontSize: 80, color: 'text.disabled', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                Preview Detenido
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Inicia el preview para ver la cámara
              </Typography>
            </Box>
          ) : (
            <Box textAlign="center">
              <CameraAlt sx={{ fontSize: 80, color: 'text.disabled', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                Cámara No Inicializada
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Conecta la cámara para comenzar
              </Typography>
            </Box>
          )}
        </Box>

        {/* Controles */}
        <Stack spacing={2}>
          {/* Controles de cámara */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Control de Cámara
            </Typography>
            <Stack direction="row" spacing={1}>
              <Button
                variant="contained"
                color="primary"
                startIcon={<PowerSettingsNew />}
                onClick={handleInicializar}
                disabled={cargando || estado?.estado_bd.activa}
              >
                Inicializar Cámara
              </Button>
              
              <Button
                variant="outlined"
                color="error"
                startIcon={<PowerSettingsNew />}
                onClick={handleLiberar}
                disabled={cargando || !estado?.estado_bd.activa}
              >
                Liberar Cámara
              </Button>
            </Stack>
          </Box>

          {/* Controles de preview */}
          {estado?.estado_bd.activa && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Control de Preview
              </Typography>
              <Stack direction="row" spacing={1}>
                {estado.estado_bd.hibernada ? (
                  <Button
                    variant="contained"
                    color="warning"
                    startIcon={<Refresh />}
                    onClick={handleReactivar}
                    disabled={cargando}
                  >
                    Reactivar desde Hibernación
                  </Button>
                ) : estado.estado_bd.en_preview ? (
                  <Button
                    variant="outlined"
                    color="secondary"
                    startIcon={<Pause />}
                    onClick={handleDetenerPreview}
                    disabled={cargando}
                  >
                    Detener Preview
                  </Button>
                ) : (
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<PlayArrow />}
                    onClick={handleIniciarPreview}
                    disabled={cargando}
                  >
                    Iniciar Preview (5 FPS)
                  </Button>
                )}
                
                <Tooltip title="Recargar estado">
                  <IconButton onClick={cargarEstado} disabled={cargando}>
                    <Refresh />
                  </IconButton>
                </Tooltip>
              </Stack>
            </Box>
          )}

          {/* Información de estado */}
          {estado && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Información
              </Typography>
              <Stack spacing={0.5}>
                <Typography variant="body2">
                  <strong>Estado:</strong>{' '}
                  {estado.estado_bd.hibernada
                    ? 'Hibernada'
                    : estado.estado_bd.en_preview
                    ? `Preview activo (${estado.estado_bd.frame_rate_actual} FPS)`
                    : estado.estado_bd.activa
                    ? 'Activa (sin preview)'
                    : 'Inactiva'}
                </Typography>
                <Typography variant="body2">
                  <strong>Tipo:</strong>{' '}
                  {estado.estado_servicio.usando_webcam ? 'Webcam (Fallback)' : 'Cámara GigE'}
                </Typography>
                <Typography variant="body2">
                  <strong>Modelo cargado:</strong> {estado.estado_bd.modelo_cargado_display}
                </Typography>
                <Typography variant="body2">
                  <strong>Último uso:</strong> {estado.estado_bd.tiempo_desde_ultimo_uso}
                </Typography>
              </Stack>
            </Box>
          )}

          {/* Alerta de hibernación automática */}
          {estado?.estado_bd.en_preview && !estado?.estado_bd.hibernada && (
            <Alert severity="info" icon={<HourglassEmpty />}>
              El preview se hibernará automáticamente después de 1 minuto de inactividad.
              Cualquier interacción con la cámara resetea el timer.
            </Alert>
          )}
        </Stack>

        {cargando && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
            <CircularProgress />
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default CameraPreview;

