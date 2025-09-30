// src/pages/Roles.tsx
import { useEffect, useState } from 'react';
import {
  DataGrid,
  getGridStringOperators,
  type GridColDef,
  type GridRenderCellParams,
} from '@mui/x-data-grid';
import { Box, Button, Dialog, DialogTitle, DialogContent } from '@mui/material';
import * as Swal from '../utils/swal';
import PageHeader from '../components/PageHeader';
import {
  fetchRoles,
  createRole,
  updateRole,
  deleteRole,
  type Rol,
  type RolPayload,
} from '../api/roles';
import RolForm from '../components/RolForm';

type Row = Rol;

export default function Roles() {
  const [rows, setRows] = useState<Row[]>([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Row | null>(null);

  const load = async () => {
    try {
      const { data } = await fetchRoles();
      setRows(data);
    } catch {
      Swal.fire({ title: 'Error', text: 'No se pudieron cargar los roles', icon: 'error' });
    }
  };

  useEffect(() => { load(); }, []);

  const handleSave = async (payload: RolPayload) => {
    try {
      if (editing) await updateRole(editing.id, payload);
      else await createRole(payload);
      setOpen(false);
      setEditing(null);
      load();
    } catch (err: any) {
      Swal.fire({ title: 'Error', text: err.message || 'No se pudo guardar el rol', icon: 'error' });
    }
  };

  const cols: GridColDef<Row>[] = [
    { field: 'rol_nombre', headerName: 'Nombre', flex: 1, filterOperators: getGridStringOperators() },
    { field: 'rol_descripcion', headerName: 'Descripción', flex: 1 },
    {
      field: 'acciones',
      headerName: 'Acciones',
      width: 200,
      sortable: false,
      filterable: false,
      renderCell: (params: GridRenderCellParams<Row>) => (
        <>
          <Button
            variant="contained"
            size="small"
            sx={{ mr: 1, bgcolor: 'editar_btn.main', color: 'editar_btn.texto', '&:hover': { bgcolor: 'editar_btn.hover' } }}
            onClick={() => { setEditing(params.row); setOpen(true); }}
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
                text: '¿Eliminar rol?',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Sí, eliminar',
              }).then(res => { if (res.isConfirmed) deleteRole(params.row.id).then(load); });
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
      <PageHeader title="ROLES" subtitle="Gestión de Roles" />
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-start' }}>
        <Button
          variant="contained"
          sx={{ bgcolor: 'nuevo_btn.main', color: 'nuevo_btn.texto', '&:hover': { bgcolor: 'nuevo_btn.hover' } }}
          onClick={() => { setEditing(null); setOpen(true); }}
        >
          NUEVO ROL
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

      <Dialog disableAutoFocus open={open} onClose={() => { setOpen(false); setEditing(null); }} fullWidth maxWidth="sm">
        <DialogTitle>{editing ? 'Editar Rol' : 'Nuevo Rol'}</DialogTitle>
        <DialogContent>
          <RolForm
            initialValues={{
              rol_nombre: editing?.rol_nombre || '',
              rol_descripcion: editing?.rol_descripcion || '',
            }}
            onSubmit={handleSave}
            onCancel={() => { setOpen(false); setEditing(null); }}
          />
        </DialogContent>
      </Dialog>
    </Box>
  );
}