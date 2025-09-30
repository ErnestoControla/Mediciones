// src/components/PrivateRoute.tsx
import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const PrivateRoute: React.FC = () => {
  const { user } = useAuth();

  // Si no hay usuario, redirige al login
  if (!user) return <Navigate to="/login" replace />;

  // Si hay usuario, renderiza las rutas hijas
  return <Outlet />;
};

export default PrivateRoute;
