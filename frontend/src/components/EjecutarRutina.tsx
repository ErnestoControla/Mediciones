// src/components/EjecutarRutina.tsx
import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Button,
  Alert,
  CircularProgress,
  LinearProgress,
  Box,
  Typography,
  Chip,
} from '@mui/material';
import {
  ThreeSixty,
  CheckCircle,
} from '@mui/icons-material';
import Swal from 'sweetalert2';
import { rutinasAPI } from '../api/rutinas';
import { useNavigate } from 'react-router-dom';

const EjecutarRutina: React.FC = () => {
  const navigate = useNavigate();
  const [ejecutando, setEjecutando] = useState(false);
  const [progreso, setProgreso] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const handleEjecutarRutina = async () => {
    try {
      setEjecutando(true);
      setError(null);
      setProgreso(0);

      // Iniciar rutina
      const inicioResponse = await rutinasAPI.iniciarRutina();
      
      setProgreso(10);

      // Ejecutar barrido automático
      const barridoResponse = await rutinasAPI.ejecutarBarrido(inicioResponse.rutina.id);
      
      setProgreso(100);

      await Swal.fire({
        title: '✅ Rutina Completada',
        html: `
          <p><strong>${barridoResponse.num_capturas}</strong> imágenes capturadas y analizadas</p>
          <p style="margin-top: 10px;">
            <a href="/rutina-inspeccion" style="color: #2196f3; text-decoration: none;">
              📊 Ver resultados detallados →
            </a>
          </p>
        `,
        icon: 'success',
        confirmButtonText: 'Ver Resultados'
      }).then((result) => {
        if (result.isConfirmed) {
          navigate('/rutina-inspeccion');
        }
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
      setProgreso(0);
    }
  };

  return (
    <Card>
      <CardHeader
        title="Rutina de Inspección"
        subheader="Barrido automático de 4 ángulos"
        avatar={<ThreeSixty />}
      />
      <CardContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            🎬 Captura automática: <strong>4 imágenes</strong>
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            ⏱️ Intervalo de captura: <strong>2 segundos</strong>
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            🔍 Análisis: <strong>Solo defectos</strong>
          </Typography>
          <Typography variant="body2" color="text.secondary">
            ⏱️ Tiempo estimado: <strong>~20 segundos</strong>
          </Typography>
        </Box>

        {ejecutando && (
          <Box sx={{ mb: 2 }}>
            <Box display="flex" alignItems="center" gap={1} mb={1}>
              <CircularProgress size={20} />
              <Typography variant="body2">
                Ejecutando barrido automático...
              </Typography>
            </Box>
            <LinearProgress variant="determinate" value={progreso} />
          </Box>
        )}

        <Button
          variant="contained"
          color="secondary"
          startIcon={ejecutando ? <CircularProgress size={20} /> : <ThreeSixty />}
          onClick={handleEjecutarRutina}
          disabled={ejecutando}
          fullWidth
          size="large"
        >
          {ejecutando ? 'Ejecutando Rutina...' : 'Ejecutar Rutina de Inspección'}
        </Button>

        {ejecutando && (
          <Alert severity="info" sx={{ mt: 2 }}>
            🎬 El barrido tomará aproximadamente 20 segundos. Por favor espera...
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default EjecutarRutina;

