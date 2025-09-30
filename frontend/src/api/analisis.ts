// src/api/analisis.ts
import API from './axios';

export interface AnalisisCopleList {
  id: number;
  id_analisis: string;
  timestamp_captura: string;
  timestamp_procesamiento: string;
  tipo_analisis: string;
  estado: string;
  usuario_nombre: string;
  configuracion_nombre: string;
  clase_predicha?: string;
  confianza?: number;
  tiempo_total_ms: number;
  mensaje_error: string;
}

// Tipos TypeScript para el sistema de análisis de coples
export interface ConfiguracionSistema {
  id: number;
  nombre: string;
  ip_camara: string;
  umbral_confianza: number;
  umbral_iou: number;
  configuracion_robustez: 'original' | 'moderada' | 'permisiva' | 'ultra_permisiva';
  activa: boolean;
  creada_por: number;
  creada_por_nombre: string;
  fecha_creacion: string;
  fecha_modificacion: string;
}

export interface ResultadoClasificacion {
  clase_predicha: string;
  confianza: number;
  tiempo_inferencia_ms: number;
}

export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface Centroide {
  x: number;
  y: number;
}

export interface DeteccionPieza {
  clase: string;
  confianza: number;
  bbox: BoundingBox;
  centroide: Centroide;
  area: number;
}

export interface DeteccionDefecto {
  clase: string;
  confianza: number;
  bbox: BoundingBox;
  centroide: Centroide;
  area: number;
}

export interface SegmentacionDefecto {
  clase: string;
  confianza: number;
  bbox: BoundingBox;
  centroide: Centroide;
  area_mascara: number;
  coeficientes_mascara: number[];
}

export interface SegmentacionPieza {
  clase: string;
  confianza: number;
  bbox: BoundingBox;
  centroide: Centroide;
  area_mascara: number;
  ancho_mascara: number;
  alto_mascara: number;
  coeficientes_mascara: number[];
}

export interface TiemposProcesamiento {
  captura_ms: number;
  clasificacion_ms: number;
  deteccion_piezas_ms: number;
  deteccion_defectos_ms: number;
  segmentacion_defectos_ms: number;
  segmentacion_piezas_ms: number;
  total_ms: number;
}

export interface AnalisisCople {
  id: number;
  id_analisis: string;
  timestamp_captura: string;
  timestamp_procesamiento: string;
  tipo_analisis: 'completo' | 'clasificacion' | 'deteccion_piezas' | 'deteccion_defectos' | 'segmentacion_defectos' | 'segmentacion_piezas';
  estado: 'procesando' | 'completado' | 'error';
  usuario: number;
  usuario_nombre: string;
  configuracion: number;
  configuracion_nombre: string;
  archivo_imagen: string;
  archivo_json: string;
  resolucion_ancho: number;
  resolucion_alto: number;
  resolucion_canales: number;
  tiempos: TiemposProcesamiento;
  metadatos_json: any;
  mensaje_error: string;
  resultado_clasificacion?: ResultadoClasificacion;
  detecciones_piezas: DeteccionPieza[];
  detecciones_defectos: DeteccionDefecto[];
  segmentaciones_defectos: SegmentacionDefecto[];
  segmentaciones_piezas: SegmentacionPieza[];
}

export interface EstadisticasSistema {
  id: number;
  fecha: string;
  total_analisis: number;
  analisis_exitosos: number;
  analisis_con_error: number;
  total_aceptados: number;
  total_rechazados: number;
  tiempo_promedio_captura_ms: number;
  tiempo_promedio_clasificacion_ms: number;
  tiempo_promedio_total_ms: number;
  confianza_promedio: number;
  tasa_exito: number;
  tasa_aceptacion: number;
}

export interface EstadoSistema {
  inicializado: boolean;
  configuracion_activa?: {
    id: number;
    nombre: string;
    umbral_confianza: number;
    configuracion_robustez: string;
  };
  estadisticas?: any;
}

export interface AnalisisRequest {
  tipo_analisis: 'completo' | 'clasificacion' | 'deteccion_piezas' | 'deteccion_defectos' | 'segmentacion_defectos' | 'segmentacion_piezas';
  configuracion_id?: number;
}

export interface ConfiguracionRequest {
  configuracion_id: number;
  activar?: boolean;
}

// Servicios de API
export const analisisAPI = {
  // Configuraciones
  getConfiguraciones: (): Promise<ConfiguracionSistema[]> =>
    API.get('analisis/configuraciones/').then(res => res.data),

  getConfiguracion: (id: number): Promise<ConfiguracionSistema> =>
    API.get(`analisis/configuraciones/${id}/`).then(res => res.data),

  createConfiguracion: (data: Partial<ConfiguracionSistema>): Promise<ConfiguracionSistema> =>
    API.post('analisis/configuraciones/', data).then(res => res.data),

  updateConfiguracion: (id: number, data: Partial<ConfiguracionSistema>): Promise<ConfiguracionSistema> =>
    API.put(`analisis/configuraciones/${id}/`, data).then(res => res.data),

  deleteConfiguracion: (id: number): Promise<void> =>
    API.delete(`analisis/configuraciones/${id}/`),

  activarConfiguracion: (id: number): Promise<any> =>
    API.post(`analisis/configuraciones/${id}/activar/`).then(res => res.data),

  getConfiguracionActiva: (): Promise<ConfiguracionSistema> =>
    API.get('analisis/configuraciones/activa/').then(res => res.data),

  // Análisis
  getAnalisis: (params?: {
    tipo_analisis?: string;
    estado?: string;
    fecha_desde?: string;
    fecha_hasta?: string;
  }): Promise<AnalisisCopleList[]> =>
    API.get('analisis/resultados/', { params }).then(res => res.data),

  getAnalisisById: (id: number): Promise<AnalisisCople> =>
    API.get(`analisis/resultados/${id}/`).then(res => res.data),

  realizarAnalisis: (data: AnalisisRequest): Promise<any> =>
    API.post('analisis/resultados/realizar_analisis/', data).then(res => res.data),

  getAnalisisRecientes: (limite?: number): Promise<AnalisisCopleList[]> =>
    API.get('analisis/resultados/recientes/', { params: { limite } }).then(res => res.data),

  getEstadisticas: (): Promise<any> =>
    API.get('analisis/resultados/estadisticas/').then(res => res.data),

  // Sistema
  getEstadoSistema: (): Promise<EstadoSistema> =>
    API.get('analisis/sistema/estado/').then(res => res.data),

  inicializarSistema: (data: ConfiguracionRequest): Promise<any> =>
    API.post('analisis/sistema/inicializar/', data).then(res => res.data),

  liberarSistema: (): Promise<any> =>
    API.post('analisis/sistema/liberar/').then(res => res.data),

  // Estadísticas
  getEstadisticasSistema: (params?: {
    fecha_desde?: string;
    fecha_hasta?: string;
  }): Promise<EstadisticasSistema[]> =>
    API.get('analisis/estadisticas/', { params }).then(res => res.data),

  getResumenEstadisticas: (): Promise<any> =>
    API.get('analisis/estadisticas/resumen/').then(res => res.data),

  // Imágenes procesadas
  getImagenProcesada: (analisisId: number): Promise<{image_data: string, analisis_id: string, timestamp: string}> =>
    API.get(`analisis/imagenes/procesada/${analisisId}/`).then(res => res.data),

  getMiniaturaAnalisis: (analisisId: number): Promise<{thumbnail_data: string, analisis_id: string}> =>
    API.get(`analisis/imagenes/miniatura/${analisisId}/`).then(res => res.data),
};