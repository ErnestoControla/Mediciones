import React, { useState, useEffect } from 'react';
import { Box, Typography, CircularProgress, Alert } from '@mui/material';
import { analisisAPI } from '../api/analisis';

interface ImagenProcesadaSimpleProps {
  analisisId: number;
  showThumbnail?: boolean;
}

const ImagenProcesadaSimple: React.FC<ImagenProcesadaSimpleProps> = ({ 
  analisisId, 
  showThumbnail = true 
}) => {
  const [imageData, setImageData] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadImage = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log(`🔄 Loading ${showThumbnail ? 'thumbnail' : 'image'} for analysis ${analisisId}`);
        
        const response = showThumbnail 
          ? await analisisAPI.getMiniaturaAnalisis(analisisId)
          : await analisisAPI.getImagenProcesada(analisisId);
        
        console.log(`📦 ${showThumbnail ? 'Thumbnail' : 'Image'} response:`, response);
        
        const data = showThumbnail ? response.thumbnail_data : response.image_data;
        
        if (data && typeof data === 'string' && data.length > 0) {
          // El backend devuelve solo el base64 puro, necesitamos agregar el prefijo
          const fullDataUrl = data.startsWith('data:') ? data : `data:image/png;base64,${data}`;
          setImageData(fullDataUrl);
          console.log(`✅ ${showThumbnail ? 'Thumbnail' : 'Image'} data loaded:`, data.length, 'chars');
          console.log(`📦 Full data URL length:`, fullDataUrl.length, 'chars');
        } else {
          throw new Error('No image data received');
        }
      } catch (err) {
        console.error(`❌ Error loading ${showThumbnail ? 'thumbnail' : 'image'}:`, err);
        setError(`Error al cargar la ${showThumbnail ? 'miniatura' : 'imagen'}`);
      } finally {
        setLoading(false);
      }
    };

    loadImage();
  }, [analisisId, showThumbnail]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
        <Typography variant="body2" sx={{ ml: 2 }}>
          Cargando {showThumbnail ? 'miniatura' : 'imagen'}...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        {error}
      </Alert>
    );
  }

  if (!imageData) {
    return (
      <Alert severity="warning">
        No hay {showThumbnail ? 'miniatura' : 'imagen'} disponible
      </Alert>
    );
  }

  return (
    <Box
      component="img"
      src={imageData}
      alt={`Análisis ${analisisId}`}
      sx={{
        width: '100%',
        height: 'auto',
        borderRadius: 1,
        border: '1px solid',
        borderColor: 'divider',
      }}
      onLoad={() => {
        console.log(`✅ ${showThumbnail ? 'Thumbnail' : 'Image'} loaded successfully for analysis ${analisisId}`);
      }}
      onError={() => {
        console.error(`❌ ${showThumbnail ? 'Thumbnail' : 'Image'} load error for analysis ${analisisId}`);
        setError(`Error al cargar la ${showThumbnail ? 'miniatura' : 'imagen'}`);
      }}
    />
  );
};

export default ImagenProcesadaSimple;
