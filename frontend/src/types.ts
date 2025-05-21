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
    intervalo_segundos: number;
    tiempo_transcurrido: number;
    modo: string;
  }
  
  export interface SessionData {
    id: string;               // ← lo nuevo
    intervalo_segundos: number;
    tiempo_transcurrido: number;
    modo: string; 
  }

  export interface PosturaMessage {
    timestamp: string;
    session: SessionData;
    postura: PosturaData;
    historial_postural: HistorialPosturalItem[];
  }
  
  // Añade esto:
  export interface MetricaOut {
    id: string;
    sesion_id: string;
    timestamp: string;      // o Date si lo transformas en front
    datos: PosturaData;
    created_at: string;     // o Date
  }
  