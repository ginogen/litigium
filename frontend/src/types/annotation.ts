export interface Document {
  id: string;
  nombre_archivo: string;
  archivo_url: string;
  tipo_mime: string;
  tipo_demanda: string;
  estado_procesamiento: string;
  vectorizado: boolean;
  created_at: string;
  processed_at?: string;
  categoria?: {
    nombre: string;
    color: string;
    icon: string;
  };
  tamaño_bytes?: number;
  error_procesamiento?: string;
  total_anotaciones?: number;
}

export interface Annotation {
  id?: string;
  posicion_inicio: number;
  posicion_fin: number;
  contenido_seleccionado: string;
  contenido_anotacion: string;
  tipo: 'comentario' | 'precedente' | 'estrategia' | 'problema';
  etiquetas?: string[];
  prioridad?: number;
  created_at: string;
  author?: string;
}

export interface AnnotationTemplate {
  id?: string;
  nombre: string;
  tipo: 'comentario' | 'precedente' | 'estrategia' | 'problema';
  contenido: string;
  etiquetas: string[];
  prioridad_sugerida?: number;
  is_default?: boolean;
  created_at?: string;
} 