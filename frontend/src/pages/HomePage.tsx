// src/pages/HomePage.tsx
import React from 'react';
import { Box, Typography } from '@mui/material';

const HomePage: React.FC = () => {
  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4" gutterBottom>
        Bienvenido a Asistente Controla
      </Typography>
      <Typography variant="body1">
        Esta es la página principal. Aquí podrás ver un resumen o iniciar tus tareas.
      </Typography>
    </Box>
  );
};

export default HomePage;
