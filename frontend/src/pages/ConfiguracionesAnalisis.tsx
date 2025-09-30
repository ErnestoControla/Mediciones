// src/pages/ConfiguracionesAnalisis.tsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardHeader,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  CheckCircle,
  Cancel,
  Settings,
} from '@mui/icons-material';
import { analisisAPI } from '../api/analisis';
import type { ConfiguracionSistema } from '../api/analisis';
import ConfiguracionForm from '../components/ConfiguracionForm';
import Swal from 'sweetalert2';

const ConfiguracionesAnalisis: React.FC = () => {
  const [configuraciones, setConfiguraciones] = useState<ConfiguracionSistema[]>([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<ConfiguracionSistema | undefined>();
  const [formLoading, setFormLoading] = useState(false);

  useEffect(() => {
    cargarConfiguraciones();
  }, []);

  const cargarConfiguraciones = async () => {
    try {
      setLoading(true);
      const data = await analisisAPI.getConfiguraciones();
      setConfiguraciones(data);
    } catch (error) {
      console.error('Error cargando configuraciones:', error);
      Swal.fire('Error', 'Error al cargar las configuraciones', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateConfig = () => {
    setEditingConfig(undefined);
    setFormOpen(true);
  };

  const handleEditConfig = (config: ConfiguracionSistema) => {
    setEditingConfig(config);
    setFormOpen(true);
  };

  const handleDeleteConfig = async (id: number) => {
    const result = await Swal.fire({
      title: '¿Estás seguro?',
      text: 'Esta acción no se puede deshacer',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#d33',
      cancelButtonColor: '#3085d6',
      confirmButtonText: 'Sí, eliminar',
      cancelButtonText: 'Cancelar',
    });

    if (result.isConfirmed) {
      try {
        await analisisAPI.deleteConfiguracion(id);
        Swal.fire('Eliminado', 'La configuración ha sido eliminada', 'success');
        cargarConfiguraciones();
      } catch (error) {
        console.error('Error eliminando configuración:', error);
        Swal.fire('Error', 'Error al eliminar la configuración', 'error');
      }
    }
  };

  const handleActivateConfig = async (id: number) => {
    try {
      await analisisAPI.activarConfiguracion(id);
      Swal.fire('Éxito', 'Configuración activada correctamente', 'success');
      cargarConfiguraciones();
    } catch (error) {
      console.error('Error activando configuración:', error);
      Swal.fire('Error', 'Error al activar la configuración', 'error');
    }
  };

  const handleFormSubmit = async (data: Partial<ConfiguracionSistema>) => {
    try {
      setFormLoading(true);
      
      if (editingConfig) {
        await analisisAPI.updateConfiguracion(editingConfig.id, data);
        Swal.fire('Éxito', 'Configuración actualizada correctamente', 'success');
      } else {
        await analisisAPI.createConfiguracion(data);
        Swal.fire('Éxito', 'Configuración creada correctamente', 'success');
      }
      
      setFormOpen(false);
      cargarConfiguraciones();
    } catch (error) {
      console.error('Error guardando configuración:', error);
      Swal.fire('Error', 'Error al guardar la configuración', 'error');
    } finally {
      setFormLoading(false);
    }
  };

  const handleCloseForm = () => {
    setFormOpen(false);
    setEditingConfig(undefined);
  };

  const getRobustezLabel = (value: string) => {
    const labels: { [key: string]: string } = {
      original: 'Original',
      moderada: 'Moderada',
      permisiva: 'Permisiva',
      ultra_permisiva: 'Ultra Permisiva',
    };
    return labels[value] || value;
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
          Configuraciones del Sistema
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={handleCreateConfig}
        >
          Nueva Configuración
        </Button>
      </Box>

      {configuraciones.length === 0 ? (
        <Card>
          <CardContent>
            <Alert severity="info">
              No hay configuraciones disponibles. Crea una nueva configuración para comenzar.
            </Alert>
          </CardContent>
        </Card>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Nombre</TableCell>
                <TableCell>IP Cámara</TableCell>
                <TableCell>Umbral Confianza</TableCell>
                <TableCell>Umbral IoU</TableCell>
                <TableCell>Robustez</TableCell>
                <TableCell>Estado</TableCell>
                <TableCell>Creada por</TableCell>
                <TableCell>Fecha</TableCell>
                <TableCell align="center">Acciones</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {configuraciones.map((config) => (
                <TableRow key={config.id}>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {config.nombre}
                    </Typography>
                  </TableCell>
                  <TableCell>{config.ip_camara}</TableCell>
                  <TableCell>{config.umbral_confianza}</TableCell>
                  <TableCell>{config.umbral_iou}</TableCell>
                  <TableCell>
                    <Chip
                      label={getRobustezLabel(config.configuracion_robustez)}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      icon={config.activa ? <CheckCircle /> : <Cancel />}
                      label={config.activa ? 'Activa' : 'Inactiva'}
                      color={config.activa ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{config.creada_por_nombre}</TableCell>
                  <TableCell>
                    {new Date(config.fecha_creacion).toLocaleDateString()}
                  </TableCell>
                  <TableCell align="center">
                    <Box display="flex" gap={1} justifyContent="center">
                      {!config.activa && (
                        <IconButton
                          size="small"
                          onClick={() => handleActivateConfig(config.id)}
                          color="success"
                          title="Activar configuración"
                        >
                          <CheckCircle />
                        </IconButton>
                      )}
                      <IconButton
                        size="small"
                        onClick={() => handleEditConfig(config)}
                        color="primary"
                        title="Editar configuración"
                      >
                        <Edit />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteConfig(config.id)}
                        color="error"
                        title="Eliminar configuración"
                      >
                        <Delete />
                      </IconButton>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <ConfiguracionForm
        open={formOpen}
        onClose={handleCloseForm}
        onSubmit={handleFormSubmit}
        configuracion={editingConfig}
        loading={formLoading}
      />
    </Box>
  );
};

export default ConfiguracionesAnalisis;
