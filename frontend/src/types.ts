  export interface HistorialPosturalItem {
    nombre: string;
    conteo: number;
  }
  
  export interface PosturaData {
    actual: string;
    transiciones_malas: number;
    porcentaje_correcta: number;
    porcentaje_incorrecta: number;
    tiempo_parado: number;
    tiempo_sentado: number;
    alertas_enviadas: number;
  }
  
  export interface SessionData {
    id: string;
    intervalo_segundos: number;
    tiempo_transcurrido: number;
    modo: string;
  }
  
  export interface SessionProgressData {
    intervalo_segundos: number;
    elapsed: number; 
  }

  export interface PosturaMessage {
    timestamp: string;
    session: SessionData;
    postura: PosturaData;
    historial_postural: HistorialPosturalItem[];
  }
  
  export interface Paciente {
    id: number;
    telegram_id: string;
    device_id: string;
    nombre: string;
    edad: number;
    sexo: string | null;
    diagnostico: string | null;
  }

  // Añade esto:
  export interface MetricaOut {
    id: string;
    sesion_id: string;
    timestamp: string;   
    datos: PosturaData;
    created_at: string; 
  }
  export interface AnalysisResponse {
    [label: string]: number;
  }

  export interface TimelineEntry {
    timestamp: string;
    postura: string;
    tiempo_mala_postura: number;
  }
