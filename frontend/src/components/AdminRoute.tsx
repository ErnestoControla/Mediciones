import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface Props {
  children: ReactNode;
}

export default function AdminRoute({ children }: Props) {
  const { user } = useAuth();
  // Si no hay usuario o no es Super Administrador, redirigimos a inicio
  if (!user || user.rol_nombre !== 'Super Administrador') {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}
