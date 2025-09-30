import React, { useState, useRef, useCallback } from 'react';
import { Box, Typography, Button, Alert } from '@mui/material';
import { CameraAlt, Stop } from '@mui/icons-material';

const CapturaSimple: React.FC = () => {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const startCamera = async () => {
    try {
      setError(null);
      setLoading(true);
      
      console.log('🔄 Iniciando cámara...');
      console.log('📱 Navigator.mediaDevices disponible:', !!navigator.mediaDevices);
      console.log('📱 getUserMedia disponible:', !!navigator.mediaDevices?.getUserMedia);
      
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { 
          width: { ideal: 640 },
          height: { ideal: 640 }
        }
      });
      
      console.log('✅ Cámara iniciada:', mediaStream);
      console.log('📹 Tracks de video:', mediaStream.getVideoTracks());
      console.log('📹 Tracks de audio:', mediaStream.getAudioTracks());
      
      setStream(mediaStream);
      
      // Usar setTimeout para asegurar que el componente se haya renderizado
      setTimeout(() => {
        if (videoRef.current) {
          console.log('🎥 Asignando stream al video element...');
          videoRef.current.srcObject = mediaStream;
          
          // Agregar event listeners para debugging
          videoRef.current.addEventListener('loadedmetadata', () => {
            console.log('✅ Video metadata cargado');
            if (videoRef.current) {
              console.log('📐 Dimensiones del video:', 
                videoRef.current.videoWidth, 'x', videoRef.current.videoHeight);
            }
          });
          
          videoRef.current.addEventListener('canplay', () => {
            console.log('✅ Video puede reproducirse');
          });
          
          videoRef.current.addEventListener('error', (e) => {
            console.error('❌ Error en video element:', e);
          });
        } else {
          console.error('❌ videoRef.current sigue siendo null después del timeout');
        }
      }, 100);
    } catch (err) {
      console.error('❌ Error iniciando cámara:', err);
      setError(`Error al acceder a la cámara: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const stopCamera = () => {
    if (stream) {
      console.log('🛑 Deteniendo cámara...');
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
      
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
    }
  };

  const captureImage = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) {
      console.error('❌ Referencias de video o canvas no disponibles');
      return;
    }

    try {
      console.log('📸 Capturando imagen...');
      
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');
      
      if (!context) {
        console.error('❌ No se pudo obtener contexto del canvas');
        return;
      }

      // Configurar canvas para imagen cuadrada de 640x640 (como en Expo_modelos)
      const targetSize = 640;
      canvas.width = targetSize;
      canvas.height = targetSize;
      
      // Calcular el recorte centrado para mantener proporciones
      const videoWidth = video.videoWidth;
      const videoHeight = video.videoHeight;
      
      // Calcular el tamaño del recorte (cuadrado)
      const cropSize = Math.min(videoWidth, videoHeight);
      
      // Calcular la posición de inicio para centrar el recorte
      const startX = (videoWidth - cropSize) / 2;
      const startY = (videoHeight - cropSize) / 2;
      
      console.log('📐 Dimensiones del video:', videoWidth, 'x', videoHeight);
      console.log('✂️ Recorte:', cropSize, 'x', cropSize, 'desde', startX, ',', startY);
      
      // Dibujar el recorte centrado en el canvas de 640x640
      context.drawImage(
        video,
        startX, startY, cropSize, cropSize,  // Área de origen (recorte)
        0, 0, targetSize, targetSize         // Área de destino (640x640)
      );
      
      // Convertir a base64
      const imageData = canvas.toDataURL('image/png');
      console.log('✅ Imagen capturada (640x640):', imageData.length, 'caracteres');
      console.log('📦 Primeros 100 chars:', imageData.substring(0, 100));
      
      setCapturedImage(imageData);
    } catch (err) {
      console.error('❌ Error capturando imagen:', err);
      setError('Error al capturar la imagen');
    }
  }, []);

  const convertToBase64 = (dataUrl: string): string => {
    // Remover el prefijo "data:image/png;base64,"
    return dataUrl.split(',')[1];
  };

  return (
    <Box sx={{ p: 2, border: '1px solid #ccc', borderRadius: 1 }}>
      <Typography variant="h6" gutterBottom>
        Captura Simple
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ mb: 2 }}>
        {!stream ? (
          <Button
            variant="contained"
            startIcon={<CameraAlt />}
            onClick={startCamera}
            disabled={loading}
          >
            {loading ? 'Iniciando...' : 'Iniciar Cámara'}
          </Button>
        ) : (
          <Box>
            <Button
              variant="outlined"
              startIcon={<Stop />}
              onClick={stopCamera}
              sx={{ mr: 2 }}
            >
              Detener Cámara
            </Button>
            <Button
              variant="contained"
              onClick={captureImage}
            >
              Capturar Imagen
            </Button>
          </Box>
        )}
      </Box>

      {stream && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Stream activo: {stream.id} | Tracks: {stream.getTracks().length}
          </Typography>
          <Box sx={{ position: 'relative' }}>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              style={{
                width: '320px',
                height: '320px',
                border: '2px solid #00ff00',
                borderRadius: '4px',
                backgroundColor: '#f0f0f0',
                display: 'block',
                objectFit: 'cover',
              }}
              onLoadedMetadata={() => {
                console.log('✅ Video metadata cargado (desde onLoadedMetadata)');
                if (videoRef.current) {
                  console.log('📐 Dimensiones del video:', 
                    videoRef.current.videoWidth, 'x', videoRef.current.videoHeight);
                }
              }}
              onCanPlay={() => {
                console.log('✅ Video puede reproducirse (desde onCanPlay)');
              }}
              onError={(e) => {
                console.error('❌ Error en video element (desde onError):', e);
              }}
            />
            <canvas
              ref={canvasRef}
              style={{ display: 'none' }}
            />
          </Box>
          <Typography variant="caption" display="block" sx={{ mt: 1 }}>
            Video element: {videoRef.current ? 'Conectado' : 'No conectado'}
          </Typography>
        </Box>
      )}

      {capturedImage && (
        <Box>
          <Typography variant="body2" gutterBottom>
            Imagen Capturada:
          </Typography>
          <img
            src={capturedImage}
            alt="Imagen capturada (640x640)"
            style={{
              width: '320px',
              height: '320px',
              border: '2px solid #ff0000',
              borderRadius: '4px',
              objectFit: 'cover',
            }}
            onLoad={() => console.log('✅ Imagen capturada renderizada correctamente')}
            onError={(e) => console.error('❌ Error renderizando imagen capturada:', e)}
          />
          <Typography variant="caption" display="block" sx={{ mt: 1 }}>
            Longitud total: {capturedImage.length} caracteres
          </Typography>
          <Typography variant="caption" display="block">
            Base64 puro: {convertToBase64(capturedImage).length} caracteres
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default CapturaSimple;
