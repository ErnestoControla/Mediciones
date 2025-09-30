import { useEffect, useState } from 'react';
import {
  DataGrid,
  getGridStringOperators,
  type GridColDef,
} from '@mui/x-data-grid';
import { Box, Button, Dialog, DialogTitle, DialogContent } from '@mui/material';
import * as Swal from '../utils/swal';
import PageHeader from '../components/PageHeader';
import {
  fetchUsuarios,
  createUsuario,
  updateUsuario,
  deleteUsuario,
  type UsuarioPerfil,
  type UsuarioPayload,
} from '../api/usuarios';
import UsuarioForm from '../components/UsuarioForm';

type Row = UsuarioPerfil;

export default function Usuarios() {
  const [rows, setRows] = useState<Row[]>([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Row | null>(null);

  const load = async () => {
    try {
      const { data } = await fetchUsuarios();
      setRows(data.filter(u => u.rol_nombre !== 'Super Administrador'));
    } catch {
      Swal.fire({ title: 'Error', text: 'No se pudieron cargar los usuarios', icon: 'error' });
    }
  };

  useEffect(() => { load(); }, []);

  const handleSave = async (payload: UsuarioPayload) => {
    try {
      // Separa confirmPassword (no se envía) y obtiene el resto
      const { confirmPassword, ...rest } = payload;
      // Omitimos confirmPassword: rest es Omit<UsuarioPayload,'confirmPassword'>
      // Creamos un objeto Partial sin confirmPassword:
      const dataToSend: Partial<Omit<UsuarioPayload, 'confirmPassword'>> = { ...rest };

      if (editing) {
        // Si estamos editando y no llenaron password, quitamos el campo
        if (!dataToSend.password) {
          delete dataToSend.password;
        }
        await updateUsuario(editing.id, dataToSend);
      } else {
        await createUsuario(dataToSend as Omit<UsuarioPayload, 'confirmPassword'>);
      }

      setOpen(false);
      setEditing(null);
      load();
    } catch (err: any) {
      Swal.fire({
        title: 'Error',
        text: err.response?.data?.detail || err.message || 'No se pudo guardar el usuario',
        icon: 'error',
      });
    }
  };

  const cols: GridColDef<Row>[] = [
    { field: 'username', headerName: 'Usuario', flex: 1, filterOperators: getGridStringOperators() },
    { field: 'name',     headerName: 'Nombre',  flex: 1 },
    { field: 'email',    headerName: 'Correo',  flex: 1 },
    { field: 'rol_nombre', headerName: 'Rol',   flex: 1 },
    {
      field: 'acciones',
      headerName: 'Acciones',
      width: 240,
      sortable: false,
      filterable: false,
      renderCell: ({ row }) => (
        <>
          <Button
            variant="contained"
            size="small"
            sx={{ mr: 1, bgcolor: 'editar_btn.main', color: 'editar_btn.texto', '&:hover': { bgcolor: 'editar_btn.hover' } }}
            onClick={() => { setEditing(row); setOpen(true); }}
          >
            Editar
          </Button>
          <Button
            variant="contained"
            size="small"
            sx={{ bgcolor: 'borrar_btn.main', color: 'borrar_btn.texto', '&:hover': { bgcolor: 'borrar_btn.hover' } }}
            onClick={() => {
              Swal.fire({
                title: 'Confirmar',
                text: '¿Eliminar usuario?',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Sí, eliminar',
              }).then(res => { if (res.isConfirmed) deleteUsuario(row.id).then(load); });
            }}
          >
            Borrar
          </Button>
        </>
      ),
    },
  ];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, minHeight: 0 }}>
      <PageHeader title="USUARIOS" subtitle="Gestión de Usuarios" />

      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-start' }}>
        <Button
          variant="contained"
          sx={{ bgcolor: 'nuevo_btn.main', color: 'nuevo_btn.texto', '&:hover': { bgcolor: 'nuevo_btn.hover' } }}
          onClick={() => { setEditing(null); setOpen(true); }}
        >
          NUEVO USUARIO
        </Button>
      </Box>

      <Box sx={{ flex: '1 1 auto', minHeight: 0 }}>
        <DataGrid
          rows={rows}
          columns={cols}
          getRowId={r => r.id}
          disableRowSelectionOnClick
          showToolbar
          pageSizeOptions={[25, 50, 100]}
          initialState={{ pagination: { paginationModel: { pageSize: 25 } }, density: 'standard' }}
          sx={{
            '& .MuiDataGrid-columnHeader': { backgroundColor: 'grid_top.main' },
            '& .MuiDataGrid-footerContainer': { backgroundColor: 'grid_bottom.main' },
            '& .MuiDataGrid-row:nth-of-type(even)': { backgroundColor: 'row.dark' },
          }}
        />
      </Box>

      <Dialog
        disableAutoFocus
        open={open}
        onClose={() => { setOpen(false); setEditing(null); }}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>{editing ? 'Editar usuario' : 'Nuevo usuario'}</DialogTitle>
        <DialogContent>
          <UsuarioForm
            initialValues={{
              username:       editing?.username || '',
              email:          editing?.email    || '',
              name:           editing?.name     || '',
              password:       '',
              confirmPassword:'',
              rol:            editing?.rol      ?? 0,
            }}
            isEdit={Boolean(editing)}
            onSubmit={handleSave}
            onCancel={() => { setOpen(false); setEditing(null); }}
          />
        </DialogContent>
      </Dialog>
    </Box>
  );
}
