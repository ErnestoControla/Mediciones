// src/pages/RutinaInspeccion.tsx
import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardHeader,
  LinearProgress,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
} from '@mui/material';
import {
  PlayArrow,
  CheckCircle,
  CameraAlt,
  Assessment,
} from '@mui/icons-material';
import Swal from 'sweetalert2';
import { rutinasAPI, RutinaInspeccion, ReporteConsolidado } from '../api/rutinas';

const RutinaInspeccionPage: React.FC = () => {
  const [ejecutando, setEjecutando] = useState(false);
  const [rutina, setRutina] = useState<RutinaInspeccion | null>(null);
  const [reporte, setReporte] = useState<ReporteConsolidado | null>(null);
  const [imagenConsolidadaUrl, setImagenConsolidadaUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pasoActual, setPasoActual] = useState(0);

  const pasos = [
    'Iniciar Rutina',
    'Ejecutando Barrido (6 fotos)',
    'Generando Consolidado',
    'Resultados',
  ];

  const handleIniciarRutina = async () => {
    try {
      setEjecutando(true);
      setError(null);
      setPasoActual(0);
      
      // Paso 1: Iniciar rutina
      setPasoActual(1);
      const inicioResponse = await rutinasAPI.iniciarRutina();
      
      setRutina(inicioResponse.rutina);
      
      // Notificar inicio
      await Swal.fire({
        title: '🚀 Rutina Iniciada',
        html: `
          <p>Se capturarán <strong>${inicioResponse.num_angulos} imágenes</strong></p>
          <p>Intervalo: <strong>${inicioResponse.delay_segundos} segundos</strong></p>
          <p style="margin-top: 15px; color: #666;">
            ⏱️ Duración estimada: ~${inicioResponse.num_angulos * inicioResponse.delay_segundos} segundos
          </p>
        `,
        icon: 'info',
        timer: 3000,
        showConfirmButton: false,
      });
      
      // Paso 2: Ejecutar barrido automático
      setPasoActual(2);
      
      const barridoResponse = await rutinasAPI.ejecutarBarrido(inicioResponse.rutina.id);
      
      setRutina(barridoResponse.rutina);
      
      // Paso 3: Obtener reporte
      setPasoActual(3);
      
      const reporteResponse = await rutinasAPI.getReporte(barridoResponse.rutina.id);
      
      setReporte(reporteResponse.reporte);
      setImagenConsolidadaUrl(reporteResponse.imagen_consolidada_url);
      
      // Paso 4: Completado
      setPasoActual(4);
      
      await Swal.fire({
        title: '✅ Rutina Completada',
        html: `
          <p><strong>Total de defectos detectados:</strong> ${reporteResponse.reporte.resumen.total_defectos}</p>
          <p><strong>Promedio por ángulo:</strong> ${reporteResponse.reporte.resumen.promedio_defectos.toFixed(1)}</p>
        `,
        icon: 'success',
      });
      
    } catch (err: any) {
      console.error('Error en rutina:', err);
      setError(err.response?.data?.error || err.message || 'Error ejecutando rutina');
      
      await Swal.fire({
        title: 'Error',
        text: err.response?.data?.error || err.message || 'Error ejecutando rutina',
        icon: 'error',
      });
    } finally {
      setEjecutando(false);
    }
  };

  const handleNuevaRutina = () => {
    setRutina(null);
    setReporte(null);
    setImagenConsolidadaUrl(null);
    setError(null);
    setPasoActual(0);
  };

  const getEstadoColor = (estado: string) => {
    switch (estado) {
      case 'completado':
        return 'success';
      case 'error':
        return 'error';
      case 'en_progreso':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        🔍 Rutina de Inspección Multi-Ángulo
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Inspección automática de defectos desde 6 ángulos diferentes
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mt: 2, mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Stepper de progreso */}
      {(ejecutando || rutina) && (
        <Card sx={{ mt: 3, mb: 3 }}>
          <CardContent>
            <Stepper activeStep={pasoActual - 1} alternativeLabel>
              {pasos.map((label) => (
                <Step key={label}>
                  <StepLabel>{label}</StepLabel>
                </Step>
              ))}
            </Stepper>
            
            {ejecutando && pasoActual === 2 && (
              <Box sx={{ mt: 3, textAlign: 'center' }}>
                <CircularProgress />
                <Typography variant="body2" sx={{ mt: 2 }}>
                  Ejecutando barrido automático...
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Capturando y analizando 6 imágenes
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Botón de inicio */}
      {!rutina && !ejecutando && (
        <Card sx={{ mt: 3 }}>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <CameraAlt sx={{ fontSize: 80, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Iniciar Rutina de Inspección
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3, maxWidth: 600, mx: 'auto' }}>
              El sistema capturará automáticamente 6 imágenes con intervalos de 3 segundos,
              analizará cada una en busca de defectos y generará un reporte consolidado.
            </Typography>
            <Button
              variant="contained"
              size="large"
              startIcon={<PlayArrow />}
              onClick={handleIniciarRutina}
              disabled={ejecutando}
              sx={{ px: 4, py: 1.5 }}
            >
              Iniciar Rutina
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Resultados */}
      {rutina && pasoActual === 4 && reporte && (
        <Grid container spacing={3} sx={{ mt: 1 }}>
          {/* Información de la rutina */}
          <Grid item xs={12}>
            <Card>
              <CardHeader
                title="Información de la Rutina"
                avatar={<CheckCircle color="success" />}
              />
              <CardContent>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="caption" color="text.secondary">
                      ID Rutina
                    </Typography>
                    <Typography variant="body1">
                      {rutina.id_rutina}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="caption" color="text.secondary">
                      Estado
                    </Typography>
                    <Box>
                      <Chip
                        label={rutina.estado_display}
                        color={getEstadoColor(rutina.estado) as any}
                        size="small"
                      />
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="caption" color="text.secondary">
                      Imágenes Capturadas
                    </Typography>
                    <Typography variant="body1">
                      {rutina.num_imagenes_capturadas} / 6
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="caption" color="text.secondary">
                      Duración Total
                    </Typography>
                    <Typography variant="body1">
                      {rutina.duracion_segundos}s
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Imagen consolidada */}
          {imagenConsolidadaUrl && (
            <Grid item xs={12} lg={6}>
              <Card>
                <CardHeader title="Imagen Consolidada (Grid 2x3)" />
                <CardContent>
                  <Box
                    component="img"
                    src={imagenConsolidadaUrl}
                    alt="Imagen consolidada"
                    sx={{
                      width: '100%',
                      borderRadius: 1,
                      border: '2px solid',
                      borderColor: 'divider',
                    }}
                  />
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Resumen estadístico */}
          <Grid item xs={12} lg={6}>
            <Card>
              <CardHeader
                title="Resumen de Defectos"
                avatar={<Assessment />}
              />
              <CardContent>
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h3" color="primary" gutterBottom>
                    {reporte.resumen.total_defectos}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Defectos totales detectados
                  </Typography>
                </Box>

                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Promedio por ángulo
                    </Typography>
                    <Typography variant="h6">
                      {reporte.resumen.promedio_defectos.toFixed(1)}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Tiempo total procesamiento
                    </Typography>
                    <Typography variant="h6">
                      {(reporte.resumen.tiempo_total_ms / 1000).toFixed(1)}s
                    </Typography>
                  </Grid>
                </Grid>

                <Box sx={{ mt: 3 }}>
                  <Typography variant="caption" color="text.secondary" gutterBottom>
                    Defectos por ángulo
                  </Typography>
                  {reporte.resumen.defectos_por_angulo.map((num, idx) => (
                    <Box key={idx} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Typography variant="body2" sx={{ minWidth: 80 }}>
                        Ángulo {idx + 1}:
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={(num / Math.max(...reporte.resumen.defectos_por_angulo)) * 100}
                        sx={{ flexGrow: 1, mx: 2, height: 8, borderRadius: 4 }}
                      />
                      <Typography variant="body2" sx={{ minWidth: 30, textAlign: 'right' }}>
                        {num}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Tabla detallada por ángulo */}
          <Grid item xs={12}>
            <Card>
              <CardHeader title="Detalle por Ángulo" />
              <CardContent>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Ángulo</TableCell>
                        <TableCell>ID Análisis</TableCell>
                        <TableCell align="right">Defectos</TableCell>
                        <TableCell align="right">Tiempo (ms)</TableCell>
                        <TableCell>Timestamp</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {reporte.angulos.map((angulo) => (
                        <TableRow key={angulo.angulo_num}>
                          <TableCell>
                            <Chip
                              label={`Ángulo ${angulo.angulo_num}`}
                              size="small"
                              color="primary"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>{angulo.id_analisis}</TableCell>
                          <TableCell align="right">
                            <strong>{angulo.num_defectos}</strong>
                          </TableCell>
                          <TableCell align="right">{angulo.tiempo_ms.toFixed(0)}</TableCell>
                          <TableCell>
                            {new Date(angulo.timestamp).toLocaleTimeString()}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>

          {/* Botón para nueva rutina */}
          <Grid item xs={12}>
            <Box sx={{ textAlign: 'center' }}>
              <Button
                variant="outlined"
                size="large"
                startIcon={<PlayArrow />}
                onClick={handleNuevaRutina}
              >
                Ejecutar Nueva Rutina
              </Button>
            </Box>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default RutinaInspeccionPage;

