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
      // Usar el endpoint de descarga que fuerza el download con Content-Disposition
      const downloadUrl = `http://localhost:8000/api/analisis/resultados/${id}/descargar-imagen/`;
      
      // Abrir directamente en nueva ventana para descargar
      // El backend enviará headers que fuerzan la descarga
      window.open(downloadUrl, '_blank');

      Swal.fire({
        title: '✅ Descarga Iniciada',
        text: 'La imagen procesada se está descargando',
        icon: 'success',
        timer: 2000,
        showConfirmButton: false
      });
    } catch (error: any) {
      console.error('Error descargando imagen:', error);
      Swal.fire('Error', `No se pudo descargar la imagen: ${error.message}`, 'error');
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
