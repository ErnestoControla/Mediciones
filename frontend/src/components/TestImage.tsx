import React, { useState, useEffect } from 'react';
import { Box, Typography, Button } from '@mui/material';

const TestImage: React.FC = () => {
  const [imageData, setImageData] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTestImage = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('http://localhost:8000/api/analisis/imagenes/test/');
      const data = await response.json();
      
      console.log('Test image response:', data);
      setImageData(data.image_data);
    } catch (err) {
      console.error('Error loading test image:', err);
      setError('Error al cargar la imagen de prueba');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTestImage();
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
        Imagen de Prueba
      </Typography>
      
      <Button onClick={loadTestImage} variant="outlined" sx={{ mb: 2 }}>
        Recargar Imagen
      </Button>
      
      {imageData ? (
        <Box>
          <img
            src={`data:image/png;base64,${imageData}`}
            alt="Imagen de prueba"
            style={{
              width: '200px',
              height: '200px',
              border: '1px solid #ddd',
              borderRadius: '4px',
            }}
            onLoad={() => console.log('✅ Test image loaded successfully')}
            onError={(e) => console.error('❌ Test image load error:', e)}
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

export default TestImage;
