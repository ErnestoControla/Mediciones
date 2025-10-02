/**
 * Componente de Captura y Análisis
 * 
 * Permite capturar imagen de la cámara y ejecutar análisis de segmentación
 */

import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Button,
  Stack,
  Typography,
  Alert,
  Box,
  CircularProgress,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  CameraAlt,
  CheckCircle,
  Analytics
} from '@mui/icons-material';
import Swal from 'sweetalert2';
import API from '../api/axios';

interface ResultadoAnalisis {
  id: number;
  tipo_analisis: string;
  estado: string;
  imagen_procesada_url?: string;
  segmentaciones_count: number;
  tiempo_total_ms: number;
}

const CapturaYAnalisis: React.FC = () => {
  const [tipoAnalisis, setTipoAnalisis] = useState<'medicion_piezas' | 'medicion_defectos'>('medicion_piezas');
  const [capturando, setCapturando] = useState(false);
  const [analizando, setAnalizando] = useState(false);
  const [imagenCapturada, setImagenCapturada] = useState<string | null>(null);
  const [timestampCaptura, setTimestampCaptura] = useState<string | null>(null);
  const [ultimoAnalisis, setUltimoAnalisis] = useState<ResultadoAnalisis | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCapturar = async () => {
    setCapturando(true);
    setError(null);

    try {
      // Capturar desde CameraService (la cámara del preview)
      const response = await API.post('/analisis/sistema/capturar/');

      if (response.data.exito) {
        setImagenCapturada(response.data.imagen_url);
        setTimestampCaptura(response.data.timestamp);
        
        await Swal.fire({
          title: '📸 Imagen Capturada',
          html: `
            <p>Imagen guardada desde cámara GigE</p>
            <p><small>${response.data.timestamp}</small></p>
          `,
          icon: 'success',
          timer: 2000
        });
      } else {
        throw new Error(response.data.error || 'Error capturando imagen');
      }

    } catch (err: any) {
      const errorMsg = err.response?.data?.error || err.message || 'Error capturando imagen';
      setError(errorMsg);
      
      await Swal.fire({
        title: 'Error',
        text: errorMsg,
        icon: 'error'
      });
    } finally {
      setCapturando(false);
    }
  };

  const handleAnalizar = async () => {
    setAnalizando(true);
    setError(null);

    try {
      // Ejecutar análisis con el tipo seleccionado
      const response = await API.post('/analisis/resultados/', {
        tipo_analisis: tipoAnalisis
      });

      const analisis = response.data;
      setUltimoAnalisis({
        id: analisis.id,
        tipo_analisis: analisis.tipo_analisis_display,
        estado: analisis.estado,
        imagen_procesada_url: analisis.imagen_procesada_url,
        segmentaciones_count: 
          (analisis.segmentaciones_piezas?.length || 0) + 
          (analisis.segmentaciones_defectos?.length || 0),
        tiempo_total_ms: analisis.tiempo_total_ms
      });

      await Swal.fire({
        title: '✅ Análisis Completado',
        html: `
          <p><strong>Tipo:</strong> ${analisis.tipo_analisis_display || 'N/A'}</p>
          <p><strong>Segmentaciones:</strong> ${
            (analisis.segmentaciones_piezas?.length || 0) + 
            (analisis.segmentaciones_defectos?.length || 0)
          }</p>
          <p><strong>Tiempo:</strong> ${(analisis.tiempo_total_ms || 0).toFixed(0)}ms</p>
          <p style="margin-top: 10px; color: #4caf50;">
            ✨ Mediciones calculadas automáticamente
          </p>
          <a href="/admin/analisis_coples/analisiscople/${analisis.id}/change/" 
             target="_blank"
             style="display: inline-block; margin-top: 10px; color: #2196f3; text-decoration: none;">
            📊 Ver detalles en admin →
          </a>
        `,
        icon: 'success'
      });

    } catch (err: any) {
      const errorMsg = err.response?.data?.error || err.message || 'Error en análisis';
      setError(errorMsg);
      
      await Swal.fire({
        title: 'Error',
        text: errorMsg,
        icon: 'error'
      });
    } finally {
      setAnalizando(false);
    }
  };

  return (
    <Card>
      <CardHeader
        title="Captura y Análisis"
        subheader="Capturar imagen y ejecutar segmentación con mediciones"
      />
      
      <CardContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Stack spacing={3}>
          {/* Tipo de análisis */}
          <FormControl fullWidth>
            <InputLabel>Tipo de Análisis</InputLabel>
            <Select
              value={tipoAnalisis}
              label="Tipo de Análisis"
              onChange={(e) => setTipoAnalisis(e.target.value as any)}
              disabled={capturando || analizando}
            >
              <MenuItem value="medicion_piezas">🔩 Medición de Piezas</MenuItem>
              <MenuItem value="medicion_defectos">⚠️ Medición de Defectos</MenuItem>
            </Select>
          </FormControl>

          {/* Botones de acción */}
          <Stack direction="row" spacing={2}>
            <Button
              variant="contained"
              color="primary"
              startIcon={capturando ? <CircularProgress size={20} /> : <CameraAlt />}
              onClick={handleCapturar}
              disabled={capturando || analizando}
              fullWidth
            >
              {capturando ? 'Capturando...' : 'Capturar'}
            </Button>

            <Button
              variant="contained"
              color="success"
              startIcon={analizando ? <CircularProgress size={20} /> : <Analytics />}
              onClick={handleAnalizar}
              disabled={capturando || analizando}
              fullWidth
            >
              {analizando ? 'Analizando...' : 'Analizar'}
            </Button>
          </Stack>

          {/* Imagen capturada */}
          {imagenCapturada && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Última Captura
              </Typography>
              <Box
                component="img"
                src={`http://localhost:8000${imagenCapturada}`}
                alt="Imagen capturada"
                sx={{
                  width: '100%',
                  borderRadius: 1,
                  border: '2px solid #4caf50',
                  mb: 1
                }}
              />
              <Chip
                icon={<CheckCircle />}
                label={`${timestampCaptura}`}
                color="success"
                size="small"
              />
            </Box>
          )}

          {/* Resultado de análisis */}
          {ultimoAnalisis && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Último Análisis - {ultimoAnalisis.tipo_analisis}
              </Typography>
              <Stack spacing={1}>
                {/* Imagen procesada si existe */}
                {ultimoAnalisis.imagen_procesada_url && (
                  <Box
                    component="img"
                    src={ultimoAnalisis.imagen_procesada_url}
                    alt="Imagen procesada"
                    sx={{
                      width: '100%',
                      borderRadius: 1,
                      border: '2px solid #2196f3',
                      mb: 1
                    }}
                  />
                )}
                
                <Chip
                  icon={<CheckCircle />}
                  label={`${ultimoAnalisis.segmentaciones_count} segmentaciones`}
                  color="primary"
                  size="small"
                />
                <Typography variant="body2">
                  <strong>Tiempo:</strong> {ultimoAnalisis.tiempo_total_ms?.toFixed(0) || 0}ms
                </Typography>
                <Typography variant="body2" color="success.main">
                  <strong>Estado:</strong> {ultimoAnalisis.estado}
                </Typography>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => window.open(`http://localhost:8000/admin/analisis_coples/analisiscople/${ultimoAnalisis.id}/change/`, '_blank')}
                >
                  📊 Ver Mediciones Completas en Admin
                </Button>
              </Stack>
            </Box>
          )}

          {/* Instrucciones */}
          <Alert severity="info">
            <Typography variant="body2">
              <strong>📋 Flujo de trabajo:</strong>
            </Typography>
            <Typography variant="body2" component="div">
              1. Selecciona tipo (piezas/defectos)<br/>
              2. Posiciona el cople en el preview<br/>
              3. <strong>Capturar</strong> → guarda imagen<br/>
              4. <strong>Analizar</strong> → segmenta y mide<br/><br/>
              <strong>✨ Mediciones automáticas:</strong><br/>
              Ancho, alto, área, perímetro, excentricidad, orientación
            </Typography>
          </Alert>
        </Stack>
      </CardContent>
    </Card>
  );
};

export default CapturaYAnalisis;

