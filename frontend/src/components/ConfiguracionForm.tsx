// src/components/ConfiguracionForm.tsx
import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  FormControlLabel,
  Switch,
  Box,
} from '@mui/material';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import type { ConfiguracionSistema } from '../api/analisis';

interface ConfiguracionFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: Partial<ConfiguracionSistema>) => void;
  configuracion?: ConfiguracionSistema;
  loading?: boolean;
}

const ConfiguracionForm: React.FC<ConfiguracionFormProps> = ({
  open,
  onClose,
  onSubmit,
  configuracion,
  loading = false,
}) => {
  const isEditing = !!configuracion;

  const validationSchema = Yup.object({
    nombre: Yup.string()
      .required('El nombre es requerido')
      .min(3, 'El nombre debe tener al menos 3 caracteres'),
    ip_camara: Yup.string()
      .required('La IP de la cámara es requerida')
      .matches(
        /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
        'IP inválida'
      ),
    umbral_confianza: Yup.number()
      .required('El umbral de confianza es requerido')
      .min(0, 'El umbral debe ser mayor o igual a 0')
      .max(1, 'El umbral debe ser menor o igual a 1'),
    umbral_iou: Yup.number()
      .required('El umbral IoU es requerido')
      .min(0, 'El umbral debe ser mayor o igual a 0')
      .max(1, 'El umbral debe ser menor o igual a 1'),
    configuracion_robustez: Yup.string()
      .required('La configuración de robustez es requerida')
      .oneOf(['original', 'moderada', 'permisiva', 'ultra_permisiva']),
  });

  const formik = useFormik({
    initialValues: {
      nombre: configuracion?.nombre || '',
      ip_camara: configuracion?.ip_camara || '172.16.1.21',
      umbral_confianza: configuracion?.umbral_confianza || 0.55,
      umbral_iou: configuracion?.umbral_iou || 0.35,
      configuracion_robustez: configuracion?.configuracion_robustez || 'original',
      activa: configuracion?.activa || false,
    },
    validationSchema,
    onSubmit: (values) => {
      onSubmit(values);
    },
    enableReinitialize: true,
  });

  const handleClose = () => {
    formik.resetForm();
    onClose();
  };

  const getRobustezLabel = (value: string) => {
    const labels: { [key: string]: string } = {
      original: 'Original - Alta precisión',
      moderada: 'Moderada - Balanceada',
      permisiva: 'Permisiva - Alta sensibilidad',
      ultra_permisiva: 'Ultra Permisiva - Condiciones extremas',
    };
    return labels[value] || value;
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {isEditing ? 'Editar Configuración' : 'Nueva Configuración'}
      </DialogTitle>
      <form onSubmit={formik.handleSubmit}>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Nombre de la configuración"
                name="nombre"
                value={formik.values.nombre}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.nombre && Boolean(formik.errors.nombre)}
                helperText={formik.touched.nombre && formik.errors.nombre}
                disabled={loading}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="IP de la cámara"
                name="ip_camara"
                value={formik.values.ip_camara}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.ip_camara && Boolean(formik.errors.ip_camara)}
                helperText={formik.touched.ip_camara && formik.errors.ip_camara}
                disabled={loading}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Configuración de robustez</InputLabel>
                <Select
                  name="configuracion_robustez"
                  value={formik.values.configuracion_robustez}
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  error={formik.touched.configuracion_robustez && Boolean(formik.errors.configuracion_robustez)}
                  disabled={loading}
                >
                  <MenuItem value="original">
                    {getRobustezLabel('original')}
                  </MenuItem>
                  <MenuItem value="moderada">
                    {getRobustezLabel('moderada')}
                  </MenuItem>
                  <MenuItem value="permisiva">
                    {getRobustezLabel('permisiva')}
                  </MenuItem>
                  <MenuItem value="ultra_permisiva">
                    {getRobustezLabel('ultra_permisiva')}
                  </MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Umbral de confianza"
                name="umbral_confianza"
                type="number"
                inputProps={{ min: 0, max: 1, step: 0.01 }}
                value={formik.values.umbral_confianza}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.umbral_confianza && Boolean(formik.errors.umbral_confianza)}
                helperText={formik.touched.umbral_confianza && formik.errors.umbral_confianza}
                disabled={loading}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Umbral IoU"
                name="umbral_iou"
                type="number"
                inputProps={{ min: 0, max: 1, step: 0.01 }}
                value={formik.values.umbral_iou}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.umbral_iou && Boolean(formik.errors.umbral_iou)}
                helperText={formik.touched.umbral_iou && formik.errors.umbral_iou}
                disabled={loading}
              />
            </Grid>

            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    name="activa"
                    checked={formik.values.activa}
                    onChange={formik.handleChange}
                    disabled={loading}
                  />
                }
                label="Activar esta configuración"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={loading}>
            Cancelar
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={loading || !formik.isValid}
          >
            {loading ? 'Guardando...' : isEditing ? 'Actualizar' : 'Crear'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default ConfiguracionForm;
