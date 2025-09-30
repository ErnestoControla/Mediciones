import React, { useState, useEffect } from 'react';
import { Box, Typography, Button } from '@mui/material';

const TestImageSimple: React.FC = () => {
  const [imageData, setImageData] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadImage = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('🔄 Loading test image...');
      const response = await fetch('http://localhost:8000/api/analisis/imagenes/test/');
      const data = await response.json();
      
      console.log('📦 Test response:', data);
      setImageData(data.thumbnail_data);
    } catch (err) {
      console.error('❌ Error loading test image:', err);
      setError('Error al cargar la imagen de prueba');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadImage();
  }, []);

  if (loading) {
    return <Typography>Cargando imagen de prueba...</Typography>;
  }

  if (error) {
    return <Typography color="error">{error}</Typography>;
  }

  return (
    <Box sx={{ p: 2, border: '1px solid #ccc', borderRadius: 1 }}>
      <Typography variant="h6" gutterBottom>
        Prueba de Imagen Simple
      </Typography>
      
      <Button onClick={loadImage} variant="outlined" sx={{ mb: 2 }}>
        Recargar Imagen
      </Button>
      
      {imageData ? (
        <Box>
          <img
            src={`data:image/png;base64,${imageData}`}
            alt="Imagen de prueba simple"
            style={{
              width: '100px',
              height: '100px',
              border: '2px solid #ff0000',
              display: 'block',
            }}
            onLoad={() => console.log('✅ Test image loaded successfully')}
            onError={(e) => {
              console.error('❌ Test image load error:', e);
              console.error('Image src length:', `data:image/png;base64,${imageData}`.length);
            }}
          />
          <Typography variant="caption" display="block" sx={{ mt: 1 }}>
            Longitud: {imageData.length} caracteres
          </Typography>
        </Box>
      ) : (
        <Typography>No hay datos de imagen</Typography>
      )}
    </Box>
  );
};

export default TestImageSimple;
