// src/pages/LoginPage.tsx

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Button, TextField, Typography, Paper } from '@mui/material';
import { styled } from '@mui/system';
import { useAuth } from '../context/AuthContext';

import MainLogo from '../assets/images/main-logo.png';
import CornerLogoImg from '../assets/images/corner-logo.png';
import BackgroundImage from '../assets/images/login-bg.png';

// Full-screen container with background
const LoginContainer = styled(Box)({
  position: 'fixed',
  top: 0,
  left: 0,
  width: '100vw',
  height: '100vh',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  backgroundImage: `url(${BackgroundImage})`,
  backgroundSize: 'cover',
  backgroundPosition: 'center',
  backgroundRepeat: 'no-repeat',
  overflow: 'hidden',
});

// Form wrapper
const FormContainer = styled(Paper)({
  padding: '40px',
  width: '400px',
  maxWidth: '90%',
  textAlign: 'center',
  borderRadius: '10px',
  backgroundColor: 'rgba(0, 0, 0, 0.6)',
  color: '#FFFFFF',
});

// Main logo
const Logo = styled('img')({
  width: '150px',
  marginBottom: '20px',
});

// Corner logo
const CornerLogo = styled('img')({
  position: 'absolute',
  bottom: '20px',
  right: '20px',
  width: '160px',
  opacity: 0.8,
});

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login(username, password);
      navigate('/');
    } catch {
      setError('Usuario o contraseña incorrectos.');
    }
  };

  return (
    <LoginContainer>
      <FormContainer elevation={5}>
        <Logo src={MainLogo} alt="Logo principal" />
        <Typography variant="h5" gutterBottom>
          Iniciar Sesión
        </Typography>
        {error && <Typography color="error" sx={{ mb: 1 }}>{error}</Typography>}
        <Box component="form" onSubmit={handleLogin}>
          <TextField
            fullWidth
            variant="outlined"
            label="Usuario"
            margin="normal"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            sx={{
              '& .MuiOutlinedInput-root': {
                '& fieldset': { borderColor: '#b3cb04' },
                '&:hover fieldset': { borderColor: '#b3cb04' },
                '&.Mui-focused fieldset': { borderColor: '#b3cb04' },
              },
              input: { color: '#FFF' },
              '& .MuiInputLabel-root': { color: '#FFF' },
            }}
          />
          <TextField
            fullWidth
            variant="outlined"
            type="password"
            label="Contraseña"
            margin="normal"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            sx={{
              '& .MuiOutlinedInput-root': {
                '& fieldset': { borderColor: '#b3cb04' },
                '&:hover fieldset': { borderColor: '#b3cb04' },
                '&.Mui-focused fieldset': { borderColor: '#b3cb04' },
              },
              input: { color: '#FFF' },
              '& .MuiInputLabel-root': { color: '#FFF' },
            }}
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{
              marginTop: '20px',
              backgroundColor: '#1b4044',
              color: '#FFF',
              '&:hover': { backgroundColor: '#1b4044' },
            }}
          >
            Ingresar
          </Button>
        </Box>
      </FormContainer>
      <CornerLogo src={CornerLogoImg} alt="Logo esquina" />
    </LoginContainer>
  );
};

export default LoginPage;
