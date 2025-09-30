// src/components/EstadisticasCard.tsx
import React from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Grid,
  Box,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  Assessment,
  CheckCircle,
  Error,
  Schedule,
  TrendingUp,
} from '@mui/icons-material';

interface EstadisticasCardProps {
  estadisticas: {
    total_analisis?: number;
    analisis_exitosos?: number;
    analisis_con_error?: number;
    tasa_exito?: number;
    total_aceptados?: number;
    total_rechazados?: number;
    tasa_aceptacion?: number;
    confianza_promedio?: number;
  };
  loading?: boolean;
}

const EstadisticasCard: React.FC<EstadisticasCardProps> = ({
  estadisticas,
  loading = false,
}) => {
  if (loading) {
    return (
      <Card>
        <CardHeader title="Estadísticas del Sistema" />
        <CardContent>
          <LinearProgress />
        </CardContent>
      </Card>
    );
  }

  const formatPorcentaje = (value: number | undefined | null) => 
    value !== undefined && value !== null ? `${value.toFixed(1)}%` : '0.0%';
  const formatConfianza = (value: number | undefined | null) => 
    value !== undefined && value !== null ? `${(value * 100).toFixed(1)}%` : '0.0%';

  return (
    <Card>
      <CardHeader
        title="Estadísticas del Sistema"
        avatar={<Assessment color="primary" />}
      />
      <CardContent>
        <Grid container spacing={3}>
          {/* Análisis Totales */}
          <Grid item xs={12} sm={6} md={3}>
            <Box textAlign="center">
              <Typography variant="h4" color="primary" gutterBottom>
                {estadisticas.total_analisis}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total de Análisis
              </Typography>
            </Box>
          </Grid>

          {/* Tasa de Éxito */}
          <Grid item xs={12} sm={6} md={3}>
            <Box textAlign="center">
              <Typography variant="h4" color="success.main" gutterBottom>
                {formatPorcentaje(estadisticas.tasa_exito)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Tasa de Éxito
              </Typography>
              <LinearProgress
                variant="determinate"
                value={estadisticas.tasa_exito || 0}
                color="success"
                sx={{ mt: 1 }}
              />
            </Box>
          </Grid>

          {/* Tasa de Aceptación */}
          <Grid item xs={12} sm={6} md={3}>
            <Box textAlign="center">
              <Typography variant="h4" color="info.main" gutterBottom>
                {formatPorcentaje(estadisticas.tasa_aceptacion)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Tasa de Aceptación
              </Typography>
              <LinearProgress
                variant="determinate"
                value={estadisticas.tasa_aceptacion || 0}
                color="info"
                sx={{ mt: 1 }}
              />
            </Box>
          </Grid>

          {/* Confianza Promedio */}
          <Grid item xs={12} sm={6} md={3}>
            <Box textAlign="center">
              <Typography variant="h4" color="warning.main" gutterBottom>
                {formatConfianza(estadisticas.confianza_promedio)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Confianza Promedio
              </Typography>
            </Box>
          </Grid>

          {/* Detalles */}
          <Grid item xs={12}>
            <Box display="flex" gap={2} flexWrap="wrap" justifyContent="center">
              <Chip
                icon={<CheckCircle />}
                label={`${estadisticas.analisis_exitosos} Exitosos`}
                color="success"
                variant="outlined"
              />
              <Chip
                icon={<Error />}
                label={`${estadisticas.analisis_con_error} Con Error`}
                color="error"
                variant="outlined"
              />
              <Chip
                icon={<TrendingUp />}
                label={`${estadisticas.total_aceptados} Aceptados`}
                color="info"
                variant="outlined"
              />
              <Chip
                icon={<TrendingUp />}
                label={`${estadisticas.total_rechazados} Rechazados`}
                color="warning"
                variant="outlined"
              />
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default EstadisticasCard;
