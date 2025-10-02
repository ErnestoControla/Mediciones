/**
 * API de control de cámara GigE
 * 
 * Endpoints para control de cámara, preview e hibernación
 */

import API from './axios';

export interface EstadoCamara {
  activa: boolean;
  en_preview: boolean;
  hibernada: boolean;
  modelo_cargado: 'piezas' | 'defectos' | 'ninguno';
  modelo_cargado_display: string;
  frame_rate_actual: number;
  ultimo_uso: string;
  ultima_actualizacion: string;
  tiempo_desde_ultimo_uso: string;
}

export interface EstadoCamaraResponse {
  estado_servicio: {
    activa: boolean;
    en_preview: boolean;
    hibernada: boolean;
    modelo_cargado: string;
    frame_rate_actual: number;
    ultimo_uso: string | null;
    usando_webcam: boolean;
    tiene_frame: boolean;
  };
  estado_bd: EstadoCamara;
}

export interface InicializarCamaraRequest {
  ip_camara?: string;
}

export interface PreviewRequest {
  fps?: number;
}

/**
 * Inicializa la cámara GigE
 */
export const inicializarCamara = async (data: InicializarCamaraRequest = {}) => {
  const response = await API.post('/camara/inicializar/', data);
  return response.data;
};

/**
 * Libera la cámara
 */
export const liberarCamara = async () => {
  const response = await API.post('/camara/liberar/');
  return response.data;
};

/**
 * Obtiene el estado actual de la cámara
 */
export const obtenerEstadoCamara = async (): Promise<EstadoCamaraResponse> => {
  const response = await API.get('/camara/estado/');
  return response.data;
};

/**
 * Inicia el preview de la cámara
 */
export const iniciarPreview = async (data: PreviewRequest = {}) => {
  const response = await API.post('/camara/preview/iniciar/', data);
  return response.data;
};

/**
 * Detiene el preview de la cámara
 */
export const detenerPreview = async () => {
  const response = await API.post('/camara/preview/detener/');
  return response.data;
};

/**
 * Reactiva el preview desde hibernación
 */
export const reactivarPreview = async (data: PreviewRequest = {}) => {
  const response = await API.post('/camara/preview/reactivar/', data);
  return response.data;
};

/**
 * Obtiene la URL del frame actual del preview
 * @returns URL completa del endpoint de frame
 */
export const getPreviewFrameUrl = (): string => {
  const baseURL = API.defaults.baseURL || 'http://localhost:8000/api/';
  // Eliminar trailing slash del baseURL para evitar doble slash
  const cleanBaseURL = baseURL.endsWith('/') ? baseURL.slice(0, -1) : baseURL;
  return `${cleanBaseURL}/camara/preview/frame/`;
};

