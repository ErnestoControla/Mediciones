/**
 * Componente de preview de cámara GigE - VERSION SIMPLIFICADA PARA DEBUG
 */

import React, { useState, useEffect } from 'react';
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
  CircularProgress
} from '@mui/material';
import {
  PowerSettingsNew,
  PlayArrow,
  Pause,
  Refresh,
  Videocam,
  VideocamOff
} from '@mui/icons-material';

import {
  inicializarCamara,
  liberarCamara,
  obtenerEstadoCamara,
  iniciarPreview,
  detenerPreview,
  reactivarPreview,
  getPreviewFrameUrl
} from '../api/camara';
import type { EstadoCamaraResponse } from '../api/camara';
import Swal from 'sweetalert2';

const CameraPreview: React.FC = () => {
  const [estado, setEstado] = useState<EstadoCamaraResponse | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [frameKey, setFrameKey] = useState(0);

  // Cargar estado inicial
  useEffect(() => {
    cargarEstado();
    const interval = setInterval(cargarEstado, 5000);
    return () => clearInterval(interval);
  }, []);

  // Actualizar frames cuando preview está activo
  useEffect(() => {
    if (estado?.estado_bd.en_preview) {
      const interval = setInterval(() => {
        setFrameKey(prev => prev + 1);
      }, 200); // 5 FPS = 200ms
      return () => clearInterval(interval);
    }
  }, [estado?.estado_bd.en_preview]);

  const cargarEstado = async () => {
    try {
      const data = await obtenerEstadoCamara();
      setEstado(data);
      setError(null);
    } catch (err: any) {
      console.error('Error cargando estado:', err);
      setError(err.response?.data?.error || 'Error cargando estado');
    }
  };

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

  const handleLiberar = async () => {
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
      }
    } catch (err: any) {
      await Swal.fire({
        title: 'Error',
        text: err.response?.data?.error || err.message,
        icon: 'error'
      });
    } finally {
      setCargando(false);
    }
  };

  const handleIniciarPreview = async () => {
    setCargando(true);
    try {
      const result = await iniciarPreview({ fps: 5 });
      
      if (result.success) {
        await cargarEstado();
        await Swal.fire({
          title: 'Preview Iniciado',
          text: `Preview activo a ${result.fps} FPS`,
          icon: 'success',
          timer: 2000
        });
      }
    } catch (err: any) {
      await Swal.fire({
        title: 'Error',
        text: err.response?.data?.error || err.message,
        icon: 'error'
      });
    } finally {
      setCargando(false);
    }
  };

  const handleDetenerPreview = async () => {
    setCargando(true);
    try {
      const result = await detenerPreview();
      
      if (result.success) {
        await cargarEstado();
        await Swal.fire({
          title: 'Preview Detenido',
          text: result.message,
          icon: 'info',
          timer: 2000
        });
      }
    } catch (err: any) {
      await Swal.fire({
        title: 'Error',
        text: err.response?.data?.error || err.message,
        icon: 'error'
      });
    } finally {
      setCargando(false);
    }
  };

  const handleReactivar = async () => {
    setCargando(true);
    try {
      const result = await reactivarPreview({ fps: 5 });
      
      if (result.success) {
        await cargarEstado();
        await Swal.fire({
          title: 'Preview Reactivado',
          text: `Preview reactivado a ${result.fps} FPS`,
          icon: 'success',
          timer: 2000
        });
      }
    } catch (err: any) {
      await Swal.fire({
        title: 'Error',
        text: err.response?.data?.error || err.message,
        icon: 'error'
      });
    } finally {
      setCargando(false);
    }
  };

  return (
    <Card>
      <CardHeader
        title="Control de Cámara GigE"
        subheader="Preview en tiempo real"
        action={
          estado && (
            <Chip
              icon={estado.estado_bd.en_preview ? <Videocam /> : <VideocamOff />}
              label={
                estado.estado_bd.hibernada ? 'Hibernada' :
                estado.estado_bd.activa ? 'Activa' : 
                'Inactiva'
              }
              color={
                estado.estado_bd.hibernada ? 'warning' :
                estado.estado_bd.activa ? 'success' : 
                'default'
              }
              size="small"
            />
          )
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
            backgroundColor: '#1a1a1a',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 1,
            mb: 2,
            border: '2px solid #333',
            overflow: 'hidden',
            position: 'relative'
          }}
        >
          {estado?.estado_bd.en_preview ? (
            <img
              src={`${getPreviewFrameUrl()}?t=${frameKey}`}
              alt="Camera Preview"
              style={{
                maxWidth: '100%',
                maxHeight: '100%',
                objectFit: 'contain'
              }}
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
              }}
            />
          ) : (
            <Box sx={{ textAlign: 'center' }}>
              <VideocamOff sx={{ fontSize: 64, color: '#666', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                {estado?.estado_bd.activa 
                  ? 'Presiona "Iniciar Preview" para ver la cámara' 
                  : 'Inicializa la cámara para continuar'}
              </Typography>
            </Box>
          )}
        </Box>

        {/* Controles */}
        <Stack spacing={2}>
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
                
                <Button
                  variant="text"
                  startIcon={<Refresh />}
                  onClick={cargarEstado}
                  disabled={cargando}
                  size="small"
                >
                  Actualizar Estado
                </Button>
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
                  {estado.estado_bd.hibernada ? '😴 Hibernada' : 
                   estado.estado_bd.activa ? '✅ Activa' : '❌ Inactiva'}
                </Typography>
                <Typography variant="body2">
                  <strong>Preview:</strong>{' '}
                  {estado.estado_bd.en_preview ? `🎬 Activo (${estado.estado_bd.frame_rate_actual} FPS)` : '⏸️ Detenido'}
                </Typography>
                <Typography variant="body2">
                  <strong>Tipo:</strong>{' '}
                  {estado.estado_servicio.usando_webcam ? '💻 Webcam (Fallback)' : '📹 Cámara GigE'}
                </Typography>
                {estado.estado_bd.hibernada && (
                  <Typography variant="body2" color="warning.main">
                    ⏰ Hibernada automáticamente por inactividad
                  </Typography>
                )}
              </Stack>
            </Box>
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
