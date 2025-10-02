/**
 * Página de control de cámara
 * 
 * Permite gestionar la cámara GigE, preview y preparación para análisis
 */

import React from 'react';
import { Container, Grid, Typography, Box } from '@mui/material';
import PageHeader from '../components/PageHeader';
import CameraPreview from '../components/CameraPreview';

const ControlCamara: React.FC = () => {
  return (
    <Container maxWidth="xl">
      <PageHeader
        title="Control de Cámara"
        subtitle="Gestión de cámara GigE y preview en tiempo real"
      />

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <CameraPreview />
        </Grid>

        <Grid size={{ xs: 12, lg: 4 }}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Instrucciones
            </Typography>
            <Typography variant="body2" paragraph>
              1. <strong>Inicializar Cámara:</strong> Conecta con la cámara GigE en 172.16.1.24
            </Typography>
            <Typography variant="body2" paragraph>
              2. <strong>Iniciar Preview:</strong> Visualiza en tiempo real a 5 FPS
            </Typography>
            <Typography variant="body2" paragraph>
              3. <strong>Hibernación Automática:</strong> Después de 1 minuto sin interacción
            </Typography>
            <Typography variant="body2" paragraph>
              4. <strong>Reactivar:</strong> Usa el botón para volver desde hibernación
            </Typography>
            
            <Box mt={3}>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                💡 Optimización de RAM
              </Typography>
              <Typography variant="body2" color="text.secondary">
                El sistema solo carga un modelo a la vez. Selecciona el tipo de análisis
                antes de ejecutar mediciones.
              </Typography>
            </Box>
          </Box>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ControlCamara;

