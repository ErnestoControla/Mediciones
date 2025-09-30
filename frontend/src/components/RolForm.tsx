// src/components/RolForm.tsx
import { Formik, Form } from 'formik';
import * as yup from 'yup';
import { TextField, Button, Box } from '@mui/material';
import type { RolPayload } from '../api/roles';

interface Props {
  initialValues: RolPayload;
  onSubmit: (data: RolPayload) => void;
  onCancel: () => void;
}

const schema = yup.object({
  rol_nombre: yup.string().required('Requerido'),
  rol_descripcion: yup.string(),
});

export default function RolForm({ initialValues, onSubmit, onCancel }: Props) {
  return (
    <Formik initialValues={initialValues} validationSchema={schema} onSubmit={(vals, { setSubmitting }) => { onSubmit(vals); setSubmitting(false); }}>
      {({ values, handleChange, errors, touched, isSubmitting }) => (
        <Form>
          <TextField
            fullWidth
            margin="normal"
            label="Nombre del Rol"
            name="rol_nombre"
            value={values.rol_nombre}
            onChange={handleChange}
            error={Boolean(touched.rol_nombre && errors.rol_nombre)}
            helperText={touched.rol_nombre && errors.rol_nombre}
          />
          <TextField
            fullWidth
            margin="normal"
            label="Descripción"
            name="rol_descripcion"
            value={values.rol_descripcion}
            onChange={handleChange}
            error={Boolean(touched.rol_descripcion && errors.rol_descripcion)}
            helperText={touched.rol_descripcion && errors.rol_descripcion}
          />

          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
            <Button onClick={onCancel} sx={{ mr: 1, bgcolor: 'cancelar_btn.main', color: 'cancelar_btn.texto', '&:hover': { bgcolor: 'cancelar_btn.hover' } }}>
              Cancelar
            </Button>
            <Button type="submit" variant="contained" disabled={isSubmitting} sx={{ bgcolor: 'guardar_btn.main', color: 'guardar_btn.texto', '&:hover': { bgcolor: 'guardar_btn.hover' } }}>
              Guardar
            </Button>
          </Box>
        </Form>
      )}
    </Formik>
  );
}