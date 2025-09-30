// src/components/ImagenProcesada.tsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
  Chip,
} from '@mui/material';
import {
  ZoomIn,
  ZoomOut,
  Fullscreen,
  Download,
  Refresh,
} from '@mui/icons-material';
import { analisisAPI } from '../api/analisis';

interface ImagenProcesadaProps {
  analisisId: number;
  showThumbnail?: boolean;
  onImageLoad?: (imageData: string) => void;
}

const ImagenProcesada: React.FC<ImagenProcesadaProps> = ({
  analisisId,
  showThumbnail = false,
  onImageLoad,
}) => {
  const [imageData, setImageData] = useState<string | null>(null);
  const [thumbnailData, setThumbnailData] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const [showFullscreen, setShowFullscreen] = useState(false);

  useEffect(() => {
    loadImage();
  }, [analisisId, showThumbnail]);

  const loadImage = async () => {
    try {
      setLoading(true);
      setError(null);

      if (showThumbnail) {
        const response = await analisisAPI.getMiniaturaAnalisis(analisisId);
        console.log('✅ Miniatura response:', response);
        console.log('✅ Thumbnail data type:', typeof response.thumbnail_data);
        console.log('✅ Thumbnail data length:', response.thumbnail_data?.length);
        setThumbnailData(response.thumbnail_data);
      } else {
        const response = await analisisAPI.getImagenProcesada(analisisId);
        console.log('✅ Imagen response:', response);
        console.log('✅ Image data type:', typeof response.image_data);
        console.log('✅ Image data length:', response.image_data?.length);
        setImageData(response.image_data);
        if (onImageLoad) {
          onImageLoad(response.image_data);
        }
      }
    } catch (err) {
      console.error('❌ Error cargando imagen:', err);
      setError('Error al cargar la imagen procesada');
    } finally {
      setLoading(false);
    }
  };

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 0.2, 3));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 0.2, 0.5));
  };

  const handleDownload = () => {
    if (imageData) {
      const link = document.createElement('a');
      link.href = `data:image/png;base64,${imageData}`;
      link.download = `analisis_${analisisId}_procesada.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const handleFullscreen = () => {
    setShowFullscreen(true);
  };

  const handleCloseFullscreen = () => {
    setShowFullscreen(false);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
        <Typography variant="body2" sx={{ ml: 2 }}>
          Cargando imagen procesada...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert 
        severity="error" 
        action={
          <IconButton color="inherit" size="small" onClick={loadImage}>
            <Refresh />
          </IconButton>
        }
      >
        {error}
      </Alert>
    );
  }

  const currentImageData = showThumbnail ? thumbnailData : imageData;

  console.log('Current image data:', currentImageData ? 'Present' : 'Missing');
  console.log('Show thumbnail:', showThumbnail);
  console.log('Thumbnail data:', thumbnailData ? 'Present' : 'Missing');
  console.log('Image data:', imageData ? 'Present' : 'Missing');

  if (!currentImageData) {
    return (
      <Alert severity="warning">
        No hay imagen procesada disponible para este análisis
      </Alert>
    );
  }

  const imageComponent = (
      <Box
        sx={{
          position: 'relative',
          display: 'inline-block',
          transform: `scale(${zoom})`,
          transformOrigin: 'top left',
          transition: 'transform 0.2s ease-in-out',
          width: '100%',
          height: '100%',
        }}
      >
      <img
        src={`data:image/png;base64,${currentImageData}`}
        alt={`Análisis ${analisisId} procesado`}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          display: 'block',
          borderRadius: '8px',
          boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
          backgroundColor: '#f0f0f0',
        }}
        onLoad={() => console.log('Image loaded successfully')}
        onError={(e) => console.error('Image load error:', e)}
      />
      
      {/* Overlay con controles */}
      {!showThumbnail && (
        <Box
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            display: 'flex',
            gap: 1,
            backgroundColor: 'rgba(0,0,0,0.7)',
            borderRadius: 1,
            p: 1,
          }}
        >
          <Tooltip title="Acercar">
            <IconButton size="small" onClick={handleZoomIn} sx={{ color: 'white' }}>
              <ZoomIn />
            </IconButton>
          </Tooltip>
          <Tooltip title="Alejar">
            <IconButton size="small" onClick={handleZoomOut} sx={{ color: 'white' }}>
              <ZoomOut />
            </IconButton>
          </Tooltip>
          <Tooltip title="Pantalla completa">
            <IconButton size="small" onClick={handleFullscreen} sx={{ color: 'white' }}>
              <Fullscreen />
            </IconButton>
          </Tooltip>
          <Tooltip title="Descargar">
            <IconButton size="small" onClick={handleDownload} sx={{ color: 'white' }}>
              <Download />
            </IconButton>
          </Tooltip>
        </Box>
      )}
    </Box>
  );

  if (showThumbnail) {
    return (
      <Box
        sx={{
          width: 200,
          height: 200,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: '2px solid #e0e0e0',
          borderRadius: 1,
          overflow: 'hidden',
          cursor: 'pointer',
          backgroundColor: '#f5f5f5',
          '&:hover': {
            borderColor: 'primary.main',
            boxShadow: 1,
          },
        }}
        onClick={() => setShowFullscreen(true)}
      >
        {currentImageData ? (
          <Box sx={{ textAlign: 'center' }}>
            <img
              src={`data:image/png;base64,${currentImageData}`}
              alt={`Análisis ${analisisId} procesado`}
              style={{
                width: '180px',
                height: '180px',
                objectFit: 'contain',
                display: 'block',
                borderRadius: '4px',
                backgroundColor: '#ffffff',
                border: '2px solid #ff0000',
              }}
              onLoad={() => console.log('✅ Thumbnail loaded successfully')}
              onError={(e) => {
                console.error('❌ Thumbnail load error:', e);
                console.error('❌ Image src:', `data:image/png;base64,${currentImageData.substring(0, 100)}...`);
                console.error('❌ Data length:', currentImageData.length);
                console.error('❌ Data type:', typeof currentImageData);
              }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Debug: {currentImageData.length} chars
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
              Data: {currentImageData.substring(0, 50)}...
            </Typography>
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            Cargando...
          </Typography>
        )}
      </Box>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Imagen Procesada
          </Typography>
          <Box display="flex" gap={1}>
            <Chip 
              label={`Zoom: ${Math.round(zoom * 100)}%`} 
              size="small" 
              variant="outlined" 
            />
            <IconButton size="small" onClick={loadImage}>
              <Refresh />
            </IconButton>
          </Box>
        </Box>
        
        <Box
          sx={{
            overflow: 'auto',
            maxHeight: '70vh',
            border: '1px solid #e0e0e0',
            borderRadius: 1,
            p: 1,
            backgroundColor: '#f5f5f5',
          }}
        >
          {imageComponent}
        </Box>
      </CardContent>

      {/* Modal de pantalla completa */}
      {showFullscreen && (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.9)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            p: 2,
          }}
          onClick={handleCloseFullscreen}
        >
          <Box
            sx={{
              position: 'relative',
              maxWidth: '90vw',
              maxHeight: '90vh',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={`data:image/png;base64,${currentImageData}`}
              alt={`Análisis ${analisisId} procesado`}
              style={{
                maxWidth: '100%',
                maxHeight: '100%',
                objectFit: 'contain',
                borderRadius: '8px',
              }}
            />
            
            {/* Controles en pantalla completa */}
            <Box
              sx={{
                position: 'absolute',
                top: 16,
                right: 16,
                display: 'flex',
                gap: 1,
                backgroundColor: 'rgba(0,0,0,0.7)',
                borderRadius: 1,
                p: 1,
              }}
            >
              <Tooltip title="Acercar">
                <IconButton size="small" onClick={handleZoomIn} sx={{ color: 'white' }}>
                  <ZoomIn />
                </IconButton>
              </Tooltip>
              <Tooltip title="Alejar">
                <IconButton size="small" onClick={handleZoomOut} sx={{ color: 'white' }}>
                  <ZoomOut />
                </IconButton>
              </Tooltip>
              <Tooltip title="Descargar">
                <IconButton size="small" onClick={handleDownload} sx={{ color: 'white' }}>
                  <Download />
                </IconButton>
              </Tooltip>
              <Tooltip title="Cerrar">
                <IconButton size="small" onClick={handleCloseFullscreen} sx={{ color: 'white' }}>
                  ×
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
        </Box>
      )}
    </Card>
  );
};

export default ImagenProcesada;
