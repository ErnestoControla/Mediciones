// src/api/rutinas.ts
import API from './axios';

// Interfaces para Rutina de Inspección Multi-Ángulo
export interface AnguloReporte {
  angulo_num: number;
  id_analisis: string;
  num_defectos: number;
  tiempo_ms: number;
  timestamp: string;
}

export interface ReporteConsolidado {
  id_rutina: string;
  num_angulos: number;
  angulos: AnguloReporte[];
  resumen: {
    total_defectos: number;
    defectos_por_angulo: number[];
    promedio_defectos: number;
    tiempo_total_ms: number;
  };
}

// Interfaces principales
export interface RutinaInspeccion {
  id: number;
  id_rutina: string;
  timestamp_inicio: string;
  timestamp_fin: string | null;
  estado: 'en_progreso' | 'completado' | 'error';
  estado_display: string;
  usuario: number;
  usuario_nombre: string;
  configuracion: number | null;
  configuracion_nombre: string | null;
  num_imagenes_capturadas: number;
  imagen_consolidada: string;
  imagen_consolidada_url: string | null;
  reporte_json: ReporteConsolidado;
  duracion_segundos: number | null;
  progreso: {
    actual: number;
    total: number;
    porcentaje: number;
  };
}

export interface RutinaInspeccionList {
  id: number;
  id_rutina: string;
  timestamp_inicio: string;
  timestamp_fin: string | null;
  estado: 'en_progreso' | 'completado' | 'error';
  estado_display: string;
  usuario_nombre: string;
  num_imagenes_capturadas: number;
  duracion_segundos: number | null;
  num_defectos_totales: number;
}

export interface IniciarRutinaRequest {
  configuracion_id?: number;
}

export interface IniciarRutinaResponse {
  message: string;
  rutina: RutinaInspeccion;
  num_angulos: number;
  delay_segundos: number;
}

export interface EjecutarBarridoResponse {
  message: string;
  rutina: RutinaInspeccion;
  num_capturas: number;
  analisis_ids: number[];
}

export interface ReporteResponse {
  id_rutina: string;
  estado: string;
  reporte: ReporteConsolidado;
  imagen_consolidada_url: string | null;
}

export const rutinasAPI = {
  /**
   * Obtiene la lista de rutinas
   */
  getRutinas: async (): Promise<RutinaInspeccionList[]> => {
    const response = await API.get('/analisis/rutinas/');
    return response.data;
  },

  /**
   * Obtiene una rutina por ID
   */
  getRutinaById: async (id: number): Promise<RutinaInspeccion> => {
    const response = await API.get(`/analisis/rutinas/${id}/`);
    return response.data;
  },

  /**
   * Inicia una nueva rutina de inspección
   */
  iniciarRutina: async (data?: IniciarRutinaRequest): Promise<IniciarRutinaResponse> => {
    const response = await API.post('/analisis/rutinas/iniciar/', data || {});
    return response.data;
  },

  /**
   * Ejecuta el barrido automático de 6 ángulos
   * NOTA: Esta operación toma ~18 segundos
   */
  ejecutarBarrido: async (rutinaId: number): Promise<EjecutarBarridoResponse> => {
    const response = await API.post(`/analisis/rutinas/${rutinaId}/ejecutar_barrido/`);
    return response.data;
  },

  /**
   * Obtiene el estado actual de una rutina
   */
  getEstado: async (rutinaId: number): Promise<RutinaInspeccion> => {
    const response = await API.get(`/analisis/rutinas/${rutinaId}/estado/`);
    return response.data;
  },

  /**
   * Obtiene el reporte consolidado de una rutina
   */
  getReporte: async (rutinaId: number): Promise<ReporteResponse> => {
    const response = await API.get(`/analisis/rutinas/${rutinaId}/reporte/`);
    return response.data;
  },
};

