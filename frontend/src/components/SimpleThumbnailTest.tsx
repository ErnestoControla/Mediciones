import React, { useState, useEffect } from 'react';
import { Box, Typography, Button } from '@mui/material';

const SimpleThumbnailTest: React.FC = () => {
  const [imageData, setImageData] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadImage = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('🔄 Loading thumbnail from test endpoint...');
      const response = await fetch('http://localhost:8000/api/analisis/imagenes/test/');
      const data = await response.json();
      
      console.log('📦 Test response:', data);
      setImageData(data.thumbnail_data);
    } catch (err) {
      console.error('❌ Error loading thumbnail:', err);
      setError('Error al cargar la miniatura');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadImage();
  }, []);

  if (loading) {
    return <Typography>Cargando miniatura de prueba...</Typography>;
  }

  if (error) {
    return <Typography color="error">{error}</Typography>;
  }

  return (
    <Box sx={{ p: 2, border: '1px solid #ccc', borderRadius: 1 }}>
      <Typography variant="h6" gutterBottom>
        Prueba Simple de Miniatura
      </Typography>
      
      <Button onClick={loadImage} variant="outlined" sx={{ mb: 2 }}>
        Recargar Miniatura
      </Button>
      
      {imageData ? (
        <Box>
          <img
            src={`data:image/png;base64,${imageData}`}
            alt="Miniatura de prueba"
            style={{
              width: '180px',
              height: '180px',
              objectFit: 'contain',
              display: 'block',
              borderRadius: '4px',
              backgroundColor: '#ffffff',
              border: '3px solid #00ff00',
            }}
            onLoad={() => console.log('✅ Simple thumbnail loaded successfully')}
            onError={(e) => {
              console.error('❌ Simple thumbnail load error:', e);
              console.error('❌ Image src:', `data:image/png;base64,${imageData.substring(0, 100)}...`);
            }}
          />
          <Typography variant="caption" display="block" sx={{ mt: 1 }}>
            Longitud: {imageData.length} caracteres
          </Typography>
        </Box>
      ) : (
        <Typography>No hay datos de miniatura</Typography>
      )}
    </Box>
  );
};

export default SimpleThumbnailTest;
