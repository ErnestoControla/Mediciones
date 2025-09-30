import API from './axios';

export interface UsuarioPerfil {
  id: number;
  username: string;
  email: string;
  name?: string;
  rol: number;
  rol_nombre: string;
}

export interface UsuarioPayload {
  username: string;
  email: string;
  name?: string;
  password?: string;
  confirmPassword?: string;
  rol: number;
}

/** GET /api/users/ */
export const fetchUsuarios = () =>
  API.get<UsuarioPerfil[]>('users/');

/** POST /api/users/ 
 *  confirmPassword no se envía, Omit lo elimina del tipo
 */
export const createUsuario = (data: Omit<UsuarioPayload, 'confirmPassword'>) =>
  API.post<UsuarioPerfil>('users/', data);

/** PUT /api/users/{id}/ 
 *  Partial<Omit<...>>: confirmPassword nunca va
 */
export const updateUsuario = (
  id: number,
  data: Partial<Omit<UsuarioPayload, 'confirmPassword'>>
) => API.put<UsuarioPerfil>(`users/${id}/`, data);

/** DELETE /api/users/{id}/ */
export const deleteUsuario = (id: number) =>
  API.delete<void>(`users/${id}/`);
