// src/pages/AnalisisCoples.tsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CircularProgress,
} from '@mui/material';
import {
  Refresh,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { analisisAPI } from '../api/analisis';
import type { AnalisisCopleList } from '../api/analisis';
import AnalisisCard from '../components/AnalisisCard';
import Swal from 'sweetalert2';

const AnalisisCoples: React.FC = () => {
  const navigate = useNavigate();
  const [analisisRecientes, setAnalisisRecientes] = useState<AnalisisCopleList[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    cargarDatos();
  }, []);

  const cargarDatos = async () => {
    try {
      setLoading(true);
      const recientes = await analisisAPI.getAnalisisRecientes(10);
      setAnalisisRecientes(recientes);
    } catch (error) {
      console.error('Error cargando análisis:', error);
      Swal.fire('Error', 'Error al cargar los análisis recientes', 'error');
    } finally {
      setLoading(false);
    }
  };


  const handleVerAnalisis = (id: number) => {
    navigate(`/analisis/${id}`);
  };

  const handleDescargarAnalisis = async (id: number) => {
    try {
      // Obtener el análisis para conseguir la URL de la imagen procesada
      const analisis = await analisisAPI.getAnalisisById(id);
      
      if (!analisis.imagen_procesada_url) {
        Swal.fire('Error', 'No hay imagen procesada disponible para este análisis', 'error');
        return;
      }

      // Fetch la imagen como blob para forzar descarga
      const response = await fetch(analisis.imagen_procesada_url);
      const blob = await response.blob();
      
      // Crear URL temporal del blob
      const blobUrl = window.URL.createObjectURL(blob);
      
      // Crear elemento <a> temporal para descargar
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `analisis_${analisis.id_analisis}_procesado.jpg`;
      document.body.appendChild(link);
      link.click();
      
      // Limpiar
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);

      Swal.fire({
        title: '✅ Descarga Completada',
        text: 'La imagen procesada se ha descargado',
        icon: 'success',
        timer: 2000,
        showConfirmButton: false
      });
    } catch (error) {
      console.error('Error descargando imagen:', error);
      Swal.fire('Error', 'No se pudo descargar la imagen procesada', 'error');
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Análisis de Coples - Visualización de Máscaras
        </Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={cargarDatos}
        >
          Actualizar
        </Button>
      </Box>

      {/* Análisis Recientes */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Análisis Recientes (últimos 10)
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Aquí puedes ver las máscaras generadas por los modelos de segmentación
          </Typography>
          {analisisRecientes.length === 0 ? (
            <Typography color="text.secondary" textAlign="center" py={4}>
              No hay análisis recientes. Ve a "Control de Cámara" para realizar un análisis.
            </Typography>
          ) : (
            <Box display="flex" flexWrap="wrap" gap={2}>
              {analisisRecientes.map((analisis) => (
                <Box key={analisis.id} minWidth="300px" flex="1 1 300px">
                  <AnalisisCard
                    analisis={analisis}
                    onView={handleVerAnalisis}
                    onDownload={handleDescargarAnalisis}
                  />
                </Box>
              ))}
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default AnalisisCoples;
