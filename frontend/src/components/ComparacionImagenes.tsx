import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, Alert, Card, CardContent } from '@mui/material';
import { analisisAPI } from '../api/analisis';

const ComparacionImagenes: React.FC = () => {
  const [backendImage, setBackendImage] = useState<string | null>(null);
  const [cameraImage, setCameraImage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadBackendImage = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('🔄 Cargando imagen del backend...');
      
      // Usar el endpoint de prueba que sabemos que funciona
      const response = await fetch('http://localhost:8000/api/analisis/imagenes/test/');
      const data = await response.json();
      
      console.log('📦 Backend response:', data);
      
      if (data.thumbnail_data) {
        setBackendImage(data.thumbnail_data);
        console.log('✅ Backend image loaded:', data.thumbnail_data.length, 'chars');
      } else {
        throw new Error('No backend image data received');
      }
    } catch (err) {
      console.error('❌ Error loading backend image:', err);
      setError('Error al cargar imagen del backend');
    } finally {
      setLoading(false);
    }
  };

  const loadCameraImage = () => {
    // Simular una imagen de cámara (como la que funciona)
    const testCameraImage = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==';
    setCameraImage(testCameraImage);
    console.log('✅ Camera image set (test)');
  };

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Comparación de Imágenes
        </Typography>
        
        <Box sx={{ mb: 2 }}>
          <Button 
            variant="contained" 
            onClick={loadBackendImage}
            disabled={loading}
            sx={{ mr: 2 }}
          >
            Cargar Imagen Backend
          </Button>
          <Button 
            variant="outlined" 
            onClick={loadCameraImage}
          >
            Cargar Imagen Cámara (Test)
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box display="flex" gap={2} flexWrap="wrap">
          {/* Imagen del Backend */}
          <Box>
            <Typography variant="body2" gutterBottom>
              Imagen del Backend:
            </Typography>
            {backendImage ? (
              <Box>
                <img
                  src={`data:image/png;base64,${backendImage}`}
                  alt="Backend Image"
                  style={{
                    width: '200px',
                    height: '200px',
                    border: '2px solid #ff0000',
                    display: 'block',
                  }}
                  onLoad={() => console.log('✅ Backend image rendered successfully')}
                  onError={(e) => {
                    console.error('❌ Backend image render error:', e);
                    console.error('Backend data length:', backendImage.length);
                    console.error('First 100 chars:', backendImage.substring(0, 100));
                  }}
                />
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  Backend: {backendImage.length} chars
                </Typography>
              </Box>
            ) : (
              <Box 
                sx={{ 
                  width: '200px', 
                  height: '200px', 
                  border: '2px dashed #ccc',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <Typography variant="caption">No cargada</Typography>
              </Box>
            )}
          </Box>

          {/* Imagen de la Cámara */}
          <Box>
            <Typography variant="body2" gutterBottom>
              Imagen de la Cámara (Test):
            </Typography>
            {cameraImage ? (
              <Box>
                <img
                  src={cameraImage}
                  alt="Camera Image"
                  style={{
                    width: '200px',
                    height: '200px',
                    border: '2px solid #00ff00',
                    display: 'block',
                  }}
                  onLoad={() => console.log('✅ Camera image rendered successfully')}
                  onError={(e) => {
                    console.error('❌ Camera image render error:', e);
                    console.error('Camera data length:', cameraImage.length);
                  }}
                />
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  Cámara: {cameraImage.length} chars
                </Typography>
              </Box>
            ) : (
              <Box 
                sx={{ 
                  width: '200px', 
                  height: '200px', 
                  border: '2px dashed #ccc',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <Typography variant="caption">No cargada</Typography>
              </Box>
            )}
          </Box>
        </Box>

        {/* Información de Debug */}
        <Box sx={{ mt: 2, p: 2, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
          <Typography variant="body2" gutterBottom>
            <strong>Información de Debug:</strong>
          </Typography>
          <Typography variant="caption" display="block">
            Backend Image: {backendImage ? `${backendImage.length} chars` : 'No cargada'}
          </Typography>
          <Typography variant="caption" display="block">
            Camera Image: {cameraImage ? `${cameraImage.length} chars` : 'No cargada'}
          </Typography>
          <Typography variant="caption" display="block">
            Backend starts with: {backendImage ? backendImage.substring(0, 50) + '...' : 'N/A'}
          </Typography>
          <Typography variant="caption" display="block">
            Camera starts with: {cameraImage ? cameraImage.substring(0, 50) + '...' : 'N/A'}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default ComparacionImagenes;
