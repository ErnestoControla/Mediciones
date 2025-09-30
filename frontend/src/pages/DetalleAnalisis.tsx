// src/pages/DetalleAnalisis.tsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Button,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Divider,
} from '@mui/material';
import {
  ArrowBack,
  Download,
  Image,
  Assessment,
  Schedule,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { analisisAPI } from '../api/analisis';
import type { AnalisisCople } from '../api/analisis';
import dayjs from 'dayjs';
import ImagenProcesada from '../components/ImagenProcesada';

const DetalleAnalisis: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [analisis, setAnalisis] = useState<AnalisisCople | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      cargarAnalisis(parseInt(id));
    }
  }, [id]);

  const cargarAnalisis = async (analisisId: number) => {
    try {
      setLoading(true);
      const data = await analisisAPI.getAnalisisById(analisisId);
      setAnalisis(data);
    } catch (error) {
      console.error('Error cargando análisis:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTiempo = (ms: number) => {
    if (ms < 1000) {
      return `${ms.toFixed(0)}ms`;
    }
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getEstadoColor = (estado: string) => {
    switch (estado) {
      case 'completado':
        return 'success';
      case 'error':
        return 'error';
      case 'procesando':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getTipoAnalisisLabel = (tipo: string) => {
    const labels: { [key: string]: string } = {
      completo: 'Análisis Completo',
      clasificacion: 'Solo Clasificación',
      deteccion_piezas: 'Detección de Piezas',
      deteccion_defectos: 'Detección de Defectos',
      segmentacion_defectos: 'Segmentación de Defectos',
      segmentacion_piezas: 'Segmentación de Piezas',
    };
    return labels[tipo] || tipo;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (!analisis) {
    return (
      <Box>
        <Alert severity="error">Análisis no encontrado</Alert>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/analisis')}
          sx={{ mt: 2 }}
        >
          Volver
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/analisis')}
        >
          Volver
        </Button>
        <Typography variant="h4" component="h1">
          Detalle del Análisis
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Información General */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardHeader
              title={analisis.id_analisis}
              subheader={
                <Box display="flex" gap={1} alignItems="center">
                  <Chip
                    label={analisis.estado}
                    color={getEstadoColor(analisis.estado) as any}
                    size="small"
                  />
                  <Chip
                    label={getTipoAnalisisLabel(analisis.tipo_analisis)}
                    variant="outlined"
                    size="small"
                  />
                </Box>
              }
              action={
                <Button
                  startIcon={<Download />}
                  variant="outlined"
                  size="small"
                >
                  Descargar
                </Button>
              }
            />
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Fecha de Captura:
                  </Typography>
                  <Typography variant="body1">
                    {dayjs(analisis.timestamp_captura).format('DD/MM/YYYY HH:mm:ss')}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Fecha de Procesamiento:
                  </Typography>
                  <Typography variant="body1">
                    {dayjs(analisis.timestamp_procesamiento).format('DD/MM/YYYY HH:mm:ss')}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Usuario:
                  </Typography>
                  <Typography variant="body1">
                    {analisis.usuario_nombre}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Configuración:
                  </Typography>
                  <Typography variant="body1">
                    {analisis.configuracion_nombre}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Resolución:
                  </Typography>
                  <Typography variant="body1">
                    {analisis.resolucion_ancho} x {analisis.resolucion_alto} ({analisis.resolucion_canales} canales)
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Tiempo Total:
                  </Typography>
                  <Typography variant="body1">
                    {formatTiempo(analisis.tiempo_total_ms)}
                  </Typography>
                </Grid>
              </Grid>

              {analisis.mensaje_error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {analisis.mensaje_error}
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Resultado de Clasificación */}
          {analisis.resultado_clasificacion && (
            <Card sx={{ mt: 2 }}>
              <CardHeader
                title="Resultado de Clasificación"
                avatar={<Assessment />}
              />
              <CardContent>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={4}>
                    <Typography variant="body2" color="text.secondary">
                      Clase Predicha:
                    </Typography>
                    <Chip
                      label={analisis.resultado_clasificacion.clase_predicha}
                      color={analisis.resultado_clasificacion.clase_predicha === 'Aceptado' ? 'success' : 'error'}
                      sx={{ mt: 1 }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <Typography variant="body2" color="text.secondary">
                      Confianza:
                    </Typography>
                    <Typography variant="h6" sx={{ mt: 1 }}>
                      {Math.round(analisis.resultado_clasificacion.confianza * 100)}%
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <Typography variant="body2" color="text.secondary">
                      Tiempo de Inferencia:
                    </Typography>
                    <Typography variant="body1" sx={{ mt: 1 }}>
                      {formatTiempo(analisis.resultado_clasificacion.tiempo_inferencia_ms)}
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}

          {/* Detecciones de Piezas */}
          {analisis.detecciones_piezas.length > 0 && (
            <Card sx={{ mt: 2 }}>
              <CardHeader title="Detecciones de Piezas" />
              <CardContent>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Clase</TableCell>
                        <TableCell>Confianza</TableCell>
                        <TableCell>Centroide</TableCell>
                        <TableCell>Área</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {analisis.detecciones_piezas.map((pieza, index) => (
                        <TableRow key={index}>
                          <TableCell>{pieza.clase}</TableCell>
                          <TableCell>
                            {Math.round(pieza.confianza * 100)}%
                          </TableCell>
                          <TableCell>
                            ({pieza.centroide.x}, {pieza.centroide.y})
                          </TableCell>
                          <TableCell>{pieza.area}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          )}

          {/* Detecciones de Defectos */}
          {analisis.detecciones_defectos.length > 0 && (
            <Card sx={{ mt: 2 }}>
              <CardHeader title="Detecciones de Defectos" />
              <CardContent>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Clase</TableCell>
                        <TableCell>Confianza</TableCell>
                        <TableCell>Centroide</TableCell>
                        <TableCell>Área</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {analisis.detecciones_defectos.map((defecto, index) => (
                        <TableRow key={index}>
                          <TableCell>{defecto.clase}</TableCell>
                          <TableCell>
                            {Math.round(defecto.confianza * 100)}%
                          </TableCell>
                          <TableCell>
                            ({defecto.centroide.x}, {defecto.centroide.y})
                          </TableCell>
                          <TableCell>{defecto.area}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          )}
        </Grid>

        {/* Panel Lateral */}
        <Grid item xs={12} md={4}>
          {/* Tiempos de Procesamiento */}
          <Card>
            <CardHeader
              title="Tiempos de Procesamiento"
              avatar={<Schedule />}
            />
            <CardContent>
              <Box display="flex" flexDirection="column" gap={1}>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">Captura:</Typography>
                  <Typography variant="body2">
                    {formatTiempo(analisis.tiempos.captura_ms)}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">Clasificación:</Typography>
                  <Typography variant="body2">
                    {formatTiempo(analisis.tiempos.clasificacion_ms)}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">Detección Piezas:</Typography>
                  <Typography variant="body2">
                    {formatTiempo(analisis.tiempos.deteccion_piezas_ms)}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">Detección Defectos:</Typography>
                  <Typography variant="body2">
                    {formatTiempo(analisis.tiempos.deteccion_defectos_ms)}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">Segmentación Defectos:</Typography>
                  <Typography variant="body2">
                    {formatTiempo(analisis.tiempos.segmentacion_defectos_ms)}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">Segmentación Piezas:</Typography>
                  <Typography variant="body2">
                    {formatTiempo(analisis.tiempos.segmentacion_piezas_ms)}
                  </Typography>
                </Box>
                <Divider sx={{ my: 1 }} />
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body1" fontWeight="bold">Total:</Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {formatTiempo(analisis.tiempo_total_ms)}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* Imagen Procesada */}
          {analisis.estado === 'completado' && (
            <Card sx={{ mt: 2 }}>
              <CardHeader
                title="Imagen Procesada"
                avatar={<Image />}
              />
              <CardContent>
                <ImagenProcesada 
                  analisisId={analisis.id} 
                  showThumbnail={false}
                />
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default DetalleAnalisis;
