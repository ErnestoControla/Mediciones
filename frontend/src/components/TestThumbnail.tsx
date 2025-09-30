import React, { useState, useEffect } from 'react';
import { Box, Typography, Button } from '@mui/material';

const TestThumbnail: React.FC = () => {
  const [imageData, setImageData] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadThumbnail = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('http://localhost:8000/api/analisis/imagenes/test/');
      const data = await response.json();
      
      console.log('Test thumbnail response:', data);
      setImageData(data.thumbnail_data);
    } catch (err) {
      console.error('Error loading thumbnail:', err);
      setError('Error al cargar la miniatura');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadThumbnail();
  }, []);

  if (loading) {
    return <Typography>Cargando miniatura...</Typography>;
  }

  if (error) {
    return <Typography color="error">{error}</Typography>;
  }

  return (
    <Box sx={{ p: 2, border: '1px solid #ccc', borderRadius: 1 }}>
      <Typography variant="h6" gutterBottom>
        Prueba de Miniatura (ID: 14)
      </Typography>
      
      <Button onClick={loadThumbnail} variant="outlined" sx={{ mb: 2 }}>
        Recargar Miniatura
      </Button>
      
      {imageData ? (
        <Box>
          <img
            src={`data:image/png;base64,${imageData}`}
            alt="Miniatura de análisis"
            style={{
              width: '180px',
              height: '180px',
              objectFit: 'contain',
              display: 'block',
              borderRadius: '4px',
              backgroundColor: '#ffffff',
              border: '2px solid #00ff00',
            }}
            onLoad={() => console.log('✅ Thumbnail loaded successfully')}
            onError={(e) => console.error('❌ Thumbnail load error:', e)}
          />
          <Typography variant="caption" display="block" sx={{ mt: 1 }}>
            Longitud: {imageData.length} caracteres
          </Typography>
          <Typography variant="caption" display="block">
            Data: {imageData.substring(0, 50)}...
          </Typography>
        </Box>
      ) : (
        <Typography>No hay datos de miniatura</Typography>
      )}
    </Box>
  );
};

export default TestThumbnail;
