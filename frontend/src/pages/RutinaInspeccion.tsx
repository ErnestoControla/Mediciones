// src/pages/RutinaInspeccion.tsx - Historial de Rutinas
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Refresh,
  Assessment,
  ExpandMore,
  CheckCircle,
  Error as ErrorIcon,
  Schedule,
} from '@mui/icons-material';
import Swal from 'sweetalert2';
import { rutinasAPI } from '../api/rutinas';
import type { RutinaInspeccionList } from '../api/rutinas';
import dayjs from 'dayjs';

const RutinaInspeccion: React.FC = () => {
  const [rutinas, setRutinas] = useState<RutinaInspeccionList[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedRutina, setExpandedRutina] = useState<number | null>(null);

  useEffect(() => {
    cargarRutinas();
  }, []);

  const cargarRutinas = async () => {
    try {
      setLoading(true);
      const data = await rutinasAPI.getRutinas();
      // Limitar a las últimas 5
      setRutinas(data.slice(0, 5));
    } catch (error) {
      console.error('Error cargando rutinas:', error);
      Swal.fire('Error', 'Error al cargar el historial de rutinas', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleVerDetalles = async (rutinaId: number) => {
    try {
      const rutina = await rutinasAPI.getRutinaById(rutinaId);
      
      // Mostrar detalles en modal
      await Swal.fire({
        title: `Rutina ${rutina.id_rutina}`,
        html: `
          <div style="text-align: left;">
            <p><strong>Estado:</strong> ${rutina.estado_display}</p>
            <p><strong>Imágenes:</strong> ${rutina.num_imagenes_capturadas}/4</p>
            <p><strong>Duración:</strong> ${rutina.duracion_segundos || 0}s</p>
            ${rutina.imagen_consolidada_url ? 
              `<img src="${rutina.imagen_consolidada_url}" style="width: 100%; margin-top: 10px; border-radius: 8px;"/>` 
              : ''}
          </div>
        `,
        width: 600,
        showCloseButton: true,
      });
    } catch (error) {
      Swal.fire('Error', 'Error al cargar detalles de la rutina', 'error');
    }
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

  const getEstadoIcon = (estado: string) => {
    switch (estado) {
      case 'completado':
        return <CheckCircle />;
      case 'error':
        return <ErrorIcon />;
      case 'en_progreso':
        return <Schedule />;
      default:
        return <Schedule />;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          🔍 Historial de Rutinas de Inspección
        </Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={cargarRutinas}
        >
          Actualizar
        </Button>
      </Box>

      <Typography variant="body1" color="text.secondary" gutterBottom>
        Últimas 5 rutinas ejecutadas. Ve a "Control de Cámara" para ejecutar una nueva rutina.
      </Typography>

      {rutinas.length === 0 ? (
        <Card sx={{ mt: 3 }}>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <Assessment sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No hay rutinas ejecutadas
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Ve a "Control de Cámara" para ejecutar la primera rutina de inspección
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Box sx={{ mt: 3 }}>
          {rutinas.map((rutina) => (
            <Accordion
              key={rutina.id}
              expanded={expandedRutina === rutina.id}
              onChange={() => setExpandedRutina(expandedRutina === rutina.id ? null : rutina.id)}
              sx={{ mb: 2 }}
            >
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Box display="flex" alignItems="center" gap={2} width="100%">
                  {getEstadoIcon(rutina.estado)}
                  <Box flexGrow={1}>
                    <Typography variant="h6">
                      {rutina.id_rutina}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {dayjs(rutina.timestamp_inicio).format('DD/MM/YYYY HH:mm:ss')} • {rutina.usuario_nombre}
                    </Typography>
                  </Box>
                  <Chip
                    label={rutina.estado_display}
                    color={getEstadoColor(rutina.estado) as any}
                    size="small"
                  />
                  <Chip
                    label={`${rutina.num_defectos_totales} defectos`}
                    color="primary"
                    size="small"
                    variant="outlined"
                  />
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3}>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Información de la Rutina
                    </Typography>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableBody>
                          <TableRow>
                            <TableCell><strong>Estado</strong></TableCell>
                            <TableCell>{rutina.estado_display}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Imágenes</strong></TableCell>
                            <TableCell>{rutina.num_imagenes_capturadas} / 4</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Defectos Totales</strong></TableCell>
                            <TableCell><strong>{rutina.num_defectos_totales}</strong></TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Duración</strong></TableCell>
                            <TableCell>{rutina.duracion_segundos || 0}s</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Inicio</strong></TableCell>
                            <TableCell>
                              {dayjs(rutina.timestamp_inicio).format('DD/MM/YYYY HH:mm:ss')}
                            </TableCell>
                          </TableRow>
                          {rutina.timestamp_fin && (
                            <TableRow>
                              <TableCell><strong>Fin</strong></TableCell>
                              <TableCell>
                                {dayjs(rutina.timestamp_fin).format('DD/MM/YYYY HH:mm:ss')}
                              </TableCell>
                            </TableRow>
                          )}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Grid>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Button
                      variant="outlined"
                      fullWidth
                      onClick={() => handleVerDetalles(rutina.id)}
                    >
                      📊 Ver Detalles Completos
                    </Button>
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      )}
    </Box>
  );
};

export default RutinaInspeccion;
