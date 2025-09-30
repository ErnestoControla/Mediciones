// src/api/roles.ts

import API from './axios';

export interface Rol {
  id: number;
  rol_nombre: string;
  rol_descripcion: string;
}

export interface RolPayload {
  rol_nombre: string;
  rol_descripcion: string;
}

/**
 * Obtiene todos los roles
 * GET /api/roles/
 */
export const fetchRoles = () =>
  API.get<Rol[]>('roles/');

/**
 * Crea un nuevo rol
 * POST /api/roles/
 */
export const createRole = (data: RolPayload) =>
  API.post<Rol>('roles/', data);

/**
 * Actualiza un rol existente
 * PUT /api/roles/{id}/
 */
export const updateRole = (
  id: number,
  data: Partial<RolPayload>
) => API.put<Rol>(`roles/${id}/`, data);

/**
 * Elimina un rol
 * DELETE /api/roles/{id}/
 */
export const deleteRole = (id: number) =>
  API.delete<void>(`roles/${id}/`);
