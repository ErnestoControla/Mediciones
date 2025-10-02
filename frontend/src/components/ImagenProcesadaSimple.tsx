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
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadImage = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log(`🔄 Loading image for analysis ${analisisId}`);
        
        // Obtener detalles del análisis para conseguir la URL de la imagen
        const analisis = await analisisAPI.getAnalisisById(analisisId);
        
        console.log(`📦 Analysis response:`, analisis);
        console.log(`📷 archivo_imagen:`, analisis.archivo_imagen);
        console.log(`🔗 imagen_procesada_url:`, analisis.imagen_procesada_url);
        
        if (analisis.imagen_procesada_url) {
          // Usar la URL completa construida por el serializer
          setImageUrl(analisis.imagen_procesada_url);
          console.log(`✅ Image URL set:`, analisis.imagen_procesada_url);
        } else {
          throw new Error('No hay imagen procesada disponible');
        }
      } catch (err) {
        console.error(`❌ Error loading image:`, err);
        setError(`Error al cargar la imagen`);
      } finally {
        setLoading(false);
      }
    };

    loadImage();
  }, [analisisId, showThumbnail]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100px">
        <CircularProgress size={20} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ py: 1 }}>
        {error}
      </Alert>
    );
  }

  if (!imageUrl) {
    return (
      <Alert severity="warning" sx={{ py: 1 }}>
        No hay imagen disponible
      </Alert>
    );
  }

  return (
    <Box
      component="img"
      src={imageUrl}
      alt={`Análisis ${analisisId}`}
      sx={{
        width: '100%',
        height: 'auto',
        borderRadius: 1,
        border: '1px solid',
        borderColor: 'divider',
        maxHeight: showThumbnail ? '200px' : 'none',
        objectFit: 'contain',
      }}
      onLoad={() => {
        console.log(`✅ Image loaded successfully for analysis ${analisisId}`);
      }}
      onError={() => {
        console.error(`❌ Image load error for analysis ${analisisId}`);
        setError(`Error al cargar la imagen`);
      }}
    />
  );
};

export default ImagenProcesadaSimple;
