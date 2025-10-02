/**
 * Página de control de cámara
 * 
 * Permite gestionar la cámara GigE, preview y preparación para análisis
 */

import React from 'react';
import { Container, Grid, Typography, Box, Stack, Card, CardContent } from '@mui/material';
import PageHeader from '../components/PageHeader';
import CameraPreview from '../components/CameraPreview';
import CapturaYAnalisis from '../components/CapturaYAnalisis';

const ControlCamara: React.FC = () => {
  return (
    <Container maxWidth="xl">
      <PageHeader
        title="Control de Cámara"
        subtitle="Gestión de cámara GigE y preview en tiempo real"
      />

      <Grid container spacing={3}>
        {/* Preview de Cámara */}
        <Grid size={{ xs: 12, lg: 8 }}>
          <CameraPreview />
        </Grid>

        {/* Panel lateral con captura y análisis */}
        <Grid size={{ xs: 12, lg: 4 }}>
          <Stack spacing={3}>
            {/* Captura y Análisis */}
            <CapturaYAnalisis />

            {/* Instrucciones */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📋 Instrucciones
                </Typography>
                <Typography variant="body2" paragraph>
                  1. <strong>Inicializar Cámara:</strong> Conecta con GigE (172.16.1.24)
                </Typography>
                <Typography variant="body2" paragraph>
                  2. <strong>Iniciar Preview:</strong> Visualiza en tiempo real (5 FPS)
                </Typography>
                <Typography variant="body2" paragraph>
                  3. <strong>Posiciona el cople:</strong> Verifica que se vea en el preview
                </Typography>
                <Typography variant="body2" paragraph>
                  4. <strong>Capturar Imagen:</strong> Guarda la imagen desde la cámara GigE
                </Typography>
                
                <Box mt={2}>
                  <Typography variant="caption" color="text.secondary">
                    💡 La cámara hiberna automáticamente después de 1 minuto de inactividad
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Stack>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ControlCamara;

