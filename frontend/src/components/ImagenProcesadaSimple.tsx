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
    <div style={{ 
      border: '10px solid red', 
      padding: '30px', 
      backgroundColor: 'white',
      margin: '20px',
      position: 'relative',
      zIndex: 9999
    }}>
      <h3 style={{ color: 'black', fontSize: '18px', margin: '0 0 10px 0' }}>
        Debug Info - Análisis {analisisId}:
      </h3>
      <p style={{ color: 'black', margin: '5px 0' }}>
        Chars: {imageData.length} | Data URL: {imageData.startsWith('data:') ? 'Yes' : 'No'}
      </p>
      <p style={{ color: 'black', margin: '5px 0' }}>
        First 50: {imageData.substring(0, 50)}...
      </p>
      
      <h3 style={{ color: 'black', fontSize: '18px', margin: '20px 0 10px 0' }}>
        Imagen Procesada:
      </h3>
      <div style={{
        border: '10px solid blue',
        padding: '20px',
        backgroundColor: 'lightblue',
        display: 'inline-block'
      }}>
        <img
          src={imageData}
          alt={`Análisis ${analisisId}`}
          style={{
            width: '300px',
            height: '300px',
            border: '10px solid orange',
            backgroundColor: 'pink',
            display: 'block',
            position: 'relative',
            zIndex: 10000,
            maxWidth: 'none',
            maxHeight: 'none'
          }}
          onLoad={(e) => {
            const img = e.target as HTMLImageElement;
            console.log(`✅ ${showThumbnail ? 'Thumbnail' : 'Image'} loaded successfully`);
            console.log('Image dimensions:', img.naturalWidth, 'x', img.naturalHeight);
            console.log('Display dimensions:', img.width, 'x', img.height);
            console.log('Image src length:', img.src.length);
            console.log('Image visible:', img.offsetWidth > 0 && img.offsetHeight > 0);
          }}
          onError={(e) => {
            console.error(`❌ ${showThumbnail ? 'Thumbnail' : 'Image'} load error:`, e);
            console.error('Image src length:', imageData.length);
            console.error('Data length:', imageData.length);
            console.error('First 100 chars:', imageData.substring(0, 100));
          }}
        />
      </div>
    </div>
  );
};

export default ImagenProcesadaSimple;
