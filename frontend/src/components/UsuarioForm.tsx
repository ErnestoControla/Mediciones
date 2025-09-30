import { Formik, Form } from 'formik';
import * as yup from 'yup';
import {
  TextField,
  Button,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  IconButton,
  InputAdornment,
  CircularProgress,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useEffect, useState } from 'react';
import type { UsuarioPayload } from '../api/usuarios';
import { fetchRoles, type Rol } from '../api/roles';

interface Props {
  initialValues: UsuarioPayload;
  onSubmit: (data: UsuarioPayload) => void;
  onCancel: () => void;
  isEdit: boolean;
}

export default function UsuarioForm({
  initialValues,
  onSubmit,
  onCancel,
  isEdit,
}: Props) {
  const [roles, setRoles] = useState<Rol[]|null>(null);
  const [showPwd, setShowPwd] = useState(false);
  const [showConf, setShowConf] = useState(false);

  useEffect(() => {
    fetchRoles()
      .then(({ data }) => setRoles(data.filter(r => r.rol_nombre !== 'Super Administrador')))
      .catch(() => setRoles([]));
  }, []);

  if (roles === null) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  const base = {
    username: yup.string().required('Requerido'),
    email:    yup.string().email('Email inválido').required('Requerido'),
    name:     yup.string().required('Requerido'),
    rol:      yup.number().typeError('Requerido').min(1, 'Requerido').required('Requerido'),
  };

  // Crear usuario: pwd + confirm obligatorios y deben coincidir
  const createSchema = yup.object({
    ...base,
    password: yup.string().required('Requerido'),
    confirmPassword: yup
      .string()
      .required('Requerido')
      .oneOf([yup.ref('password')], 'Las contraseñas no coinciden'),
  });

  // Editar usuario: pwd opcional, confirm solo si cambias pwd
  const editSchema = yup.object({
    ...base,
    password: yup.string(),
    confirmPassword: yup
      .string()
      .test('match-if-changed', 'Las contraseñas no coinciden', function (value) {
        const pwd = this.parent.password as string;
        if (!pwd) return true;        // no cambió pwd → ok
        return value === pwd;          // sí cambió → confirm debe coincidir
      }),
  });

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      validationSchema={isEdit ? editSchema : createSchema}
      onSubmit={(vals, { setSubmitting }) => {
        onSubmit(vals);
        setSubmitting(false);
      }}
    >
      {({ values, handleChange, touched, errors, isSubmitting }) => (
        <Form noValidate>
          <TextField
            fullWidth margin="normal"
            label="Usuario" name="username"
            value={values.username} onChange={handleChange}
            error={Boolean(touched.username && errors.username)}
            helperText={touched.username && errors.username}
          />

          <TextField
            fullWidth margin="normal"
            label="Correo" name="email"
            value={values.email} onChange={handleChange}
            error={Boolean(touched.email && errors.email)}
            helperText={touched.email && errors.email}
          />

          <TextField
            fullWidth margin="normal"
            label="Nombre" name="name"
            value={values.name} onChange={handleChange}
            error={Boolean(touched.name && errors.name)}
            helperText={touched.name && errors.name}
          />

          <TextField
            fullWidth margin="normal"
            label="Contraseña" name="password"
            type={showPwd ? 'text' : 'password'}
            value={values.password} onChange={handleChange}
            error={Boolean(touched.password && errors.password)}
            helperText={
              touched.password && errors.password
                ? errors.password
                : isEdit
                  ? 'Completa solo si deseas cambiar la contraseña.'
                  : ''
            }
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={() => setShowPwd(p => !p)} edge="end">
                    {showPwd ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <TextField
            fullWidth margin="normal"
            label="Confirmar Contraseña" name="confirmPassword"
            type={showConf ? 'text' : 'password'}
            value={values.confirmPassword} onChange={handleChange}
            error={Boolean(touched.confirmPassword && errors.confirmPassword)}
            helperText={touched.confirmPassword && errors.confirmPassword}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={() => setShowConf(p => !p)} edge="end">
                    {showConf ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <FormControl fullWidth margin="normal" error={Boolean(touched.rol && errors.rol)}>
            <InputLabel required id="rol-label">Rol</InputLabel>
            <Select
              labelId="rol-label"
              name="rol"
              value={values.rol}
              label="Rol"
              displayEmpty
              onChange={handleChange}
            >
              <MenuItem value={0}><em>Selecciona un rol</em></MenuItem>
              {roles.map(r => (
                <MenuItem key={r.id} value={r.id}>{r.rol_nombre}</MenuItem>
              ))}
            </Select>
            {touched.rol && errors.rol && (
              <FormHelperText>{errors.rol as string}</FormHelperText>
            )}
          </FormControl>

          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
            <Button
              onClick={onCancel}
              sx={{
                mr: 1,
                bgcolor: 'cancelar_btn.main',
                color: 'cancelar_btn.texto',
                '&:hover': { bgcolor: 'cancelar_btn.hover' },
              }}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={isSubmitting}
              sx={{
                bgcolor: 'guardar_btn.main',
                color: 'guardar_btn.texto',
                '&:hover': { bgcolor: 'guardar_btn.hover' },
              }}
            >
              Guardar
            </Button>
          </Box>
        </Form>
      )}
    </Formik>
  );
}
