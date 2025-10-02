/**
 * Componente de Captura y Análisis
 * 
 * Permite capturar imagen de la cámara y ejecutar análisis de segmentación
 */

import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Button,
  Stack,
  Typography,
  Alert,
  Box,
  CircularProgress,
  Chip
} from '@mui/material';
import {
  CameraAlt,
  CheckCircle
} from '@mui/icons-material';
import Swal from 'sweetalert2';
import API from '../api/axios';

interface ResultadoAnalisis {
  id: number;
  tipo_analisis: string;
  estado: string;
  imagen_procesada_url?: string;
  segmentaciones_count: number;
  tiempo_total_ms: number;
}

const CapturaYAnalisis: React.FC = () => {
  const [capturando, setCapturando] = useState(false);
  const [imagenCapturada, setImagenCapturada] = useState<string | null>(null);
  const [timestampCaptura, setTimestampCaptura] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCapturar = async () => {
    setCapturando(true);
    setError(null);

    try {
      // Capturar desde CameraService (la cámara del preview)
      const response = await API.post('/analisis/sistema/capturar/');

      if (response.data.exito) {
        setImagenCapturada(response.data.imagen_url);
        setTimestampCaptura(response.data.timestamp);
        
        await Swal.fire({
          title: '📸 Imagen Capturada',
          html: `
            <p>Imagen guardada desde cámara GigE</p>
            <p><small>${response.data.timestamp}</small></p>
          `,
          icon: 'success',
          timer: 2000
        });
      } else {
        throw new Error(response.data.error || 'Error capturando imagen');
      }

    } catch (err: any) {
      const errorMsg = err.response?.data?.error || err.message || 'Error capturando imagen';
      setError(errorMsg);
      
      await Swal.fire({
        title: 'Error',
        text: errorMsg,
        icon: 'error'
      });
    } finally {
      setCapturando(false);
    }
  };

  return (
    <Card>
      <CardHeader
        title="Captura y Análisis"
        subheader="Capturar imagen y ejecutar segmentación con mediciones"
      />
      
      <CardContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Stack spacing={3}>
          {/* Botón de captura */}
          <Button
            variant="contained"
            color="primary"
            size="large"
            startIcon={capturando ? <CircularProgress size={20} /> : <CameraAlt />}
            onClick={handleCapturar}
            disabled={capturando}
            fullWidth
          >
            {capturando ? 'Capturando...' : '📸 Capturar Imagen'}
          </Button>

          {/* Imagen capturada */}
          {imagenCapturada && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Última Captura
              </Typography>
              <Box
                component="img"
                src={`http://localhost:8000${imagenCapturada}`}
                alt="Imagen capturada"
                sx={{
                  width: '100%',
                  borderRadius: 1,
                  border: '2px solid #4caf50',
                  mb: 1
                }}
              />
              <Chip
                icon={<CheckCircle />}
                label={`Capturada: ${timestampCaptura}`}
                color="success"
                size="small"
              />
            </Box>
          )}

          {/* Instrucciones */}
          <Alert severity="info">
            <Typography variant="body2">
              <strong>📋 Cómo usar:</strong>
            </Typography>
            <Typography variant="body2" component="div">
              1. Inicializa la cámara y activa el preview<br/>
              2. Posiciona el objeto (cople) frente a la cámara<br/>
              3. Verifica que lo veas correctamente en el preview<br/>
              4. Click en "📸 Capturar Imagen"<br/><br/>
              <strong>✅ La imagen se captura de la cámara activa</strong><br/>
              (GigE 172.16.1.24 o webcam fallback)
            </Typography>
          </Alert>
        </Stack>
      </CardContent>
    </Card>
  );
};

export default CapturaYAnalisis;

