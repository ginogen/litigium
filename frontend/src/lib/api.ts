// @ts-check
// API Configuration and endpoints for the legal assistant application
import axios from 'axios';
import type { Annotation, AnnotationTemplate, Document } from '../types/annotation';

// Tipos TypeScript para las respuestas de la API
export interface ChatSession {
  session_id: string;
  mensaje: string;
}

export interface ChatMessage {
  respuesta: string;
  opciones?: string[];
  mostrar_descarga?: boolean;
  mostrar_preview?: boolean;
  mostrar_refrescar?: boolean;
}

export interface ParagraphData {
  numero: number;
  contenido: string;
  tipo: string;
  modificado: boolean;
  fecha_modificacion?: string;
}

export interface EditHistoryItem {
  id: string;
  comando: string;
  operacion: string;
  parrafo_numero?: number;
  timestamp: string;
  exito: boolean;
  mensaje?: string;
  resultado?: any;
}

export interface EditCommandResult {
  success: boolean;
  message?: string;
  error?: string;
  parrafos_actualizados?: ParagraphData[];
}

// Tipos para el sistema de entrenamiento
export interface ProcessDocumentResult {
  success: boolean;
  message?: string;
  error?: string;
  document_id?: string;
  processing_status?: string;
}

export interface DocumentProcessingStatus {
  id: string;
  estado_procesamiento: string;
  vectorizado: boolean;
  qdrant_collection?: string;
  error_procesamiento?: string;
  texto_extraido?: string;
  progreso?: number;
}

// Configuración base de Axios
const getBaseURL = () => {
  // Si hay una URL específica de API definida, usarla
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  // Detectar si estamos en producción
  const isProduction = import.meta.env.PROD || 
                      process.env.NODE_ENV === 'production' || 
                      window.location.hostname !== 'localhost';
  
  if (isProduction) {
    // En producción, intentar usar el mismo dominio
    return window.location.origin;
  }
  // En desarrollo, usar localhost
  return 'http://localhost:8000';
};

const baseURL = getBaseURL();

// Cliente principal con timeout moderado para operaciones normales
export const api = axios.create({
  baseURL,
  timeout: 45000, // 45 segundos para operaciones normales
  headers: {
    'Content-Type': 'application/json',
  }
});

// Cliente especializado para operaciones largas (generación de demandas)
export const apiLong = axios.create({
  baseURL,
  timeout: 180000, // 3 minutos para operaciones largas
  headers: {
    'Content-Type': 'application/json',
  }
});

// Importar funciones de autenticación
import { getAuthToken } from './auth-api';

// Interceptor para agregar token de autenticación automáticamente
const authInterceptor = async (config: any) => {
  try {
    const token = await getAuthToken();
    if (token) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${token}`,
      };
    }
  } catch (error) {
    console.warn('Error agregando token de autenticación:', error);
  }
  return config;
};

// Interceptor para manejar errores globalmente
const errorInterceptor = (error: any) => {
  console.error('API Error:', error);
  
  if (error.code === 'ECONNABORTED') {
    console.error('Timeout: La operación tardó demasiado');
  } else if (error.response) {
    console.error('Error de servidor:', error.response.status, error.response.data);
    
    // Si es error 401/403, posiblemente el token expiró
    if (error.response.status === 401 || error.response.status === 403) {
      console.warn('Token posiblemente expirado. Considera reautenticar.');
    }
  } else if (error.request) {
    console.error('Error de red: No se pudo conectar al servidor');
  }
  
  return Promise.reject(error);
};

// Agregar interceptors a ambos clientes
api.interceptors.request.use(authInterceptor);
api.interceptors.response.use((response) => response, errorInterceptor);

apiLong.interceptors.request.use(authInterceptor); 
apiLong.interceptors.response.use((response) => response, errorInterceptor);

// Funciones específicas de la API
export const chatAPI = {
  async iniciar(): Promise<ChatSession> {
    console.log('🚀 Llamando a /chat/iniciar...');
    try {
      const response = await api.post<ChatSession>('/api/chat/iniciar');
      
      console.log('✅ Respuesta completa de /chat/iniciar:', response.data);
      console.log('🔍 session_id recibido:', response.data.session_id);
      
      if (!response.data.session_id) {
        console.error('❌ PROBLEMA: El servidor no devolvió session_id');
        console.error('❌ Estructura de respuesta:', Object.keys(response.data));
      }
      
      return response.data;
    } catch (error) {
      console.error('❌ Error en iniciar():', error);
      throw error;
    }
  },

  async enviarMensaje(mensaje: string, sessionId: string): Promise<ChatMessage> {
    // Usar timeout largo para mensajes que pueden generar demandas
    const response = await apiLong.post<ChatMessage>('/api/chat/mensaje', {
      mensaje,
      session_id: sessionId
    });
    return response.data;
  },

  async obtenerMensajes(sessionId: string): Promise<{
    success: boolean;
    session_id: string;
    mensajes: Array<{
      id: string;
      tipo: string;
      mensaje: string;
      metadata: any;
      created_at: string;
    }>;
    sesion_info: any;
  }> {
    const response = await api.get(`/api/chat/mensajes/${sessionId}`);
    return response.data;
  },

  // Eliminar sesión/conversación
  async eliminarSesion(sessionId: string): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await api.delete(`/api/chat/sesion/${sessionId}`);
    return response.data;
  },

  // Mover sesión a carpeta
  async moverSesion(sessionId: string, carpetaId: string | null): Promise<{
    success: boolean;
    message: string;
    session: any;
  }> {
    const response = await api.put(`/api/chat/sesion/${sessionId}/mover`, {
      carpeta_id: carpetaId
    });
    return response.data;
  },

  // Eliminar múltiples sesiones
  async eliminarSesionesMasivo(sessionIds: string[]): Promise<{
    success: boolean;
    message: string;
    deleted_count: number;
    errors: string[];
  }> {
    const response = await api.delete('/api/chat/sesiones/bulk', {
      data: { session_ids: sessionIds }
    });
    return response.data;
  },

  // Verificar si hay categorías disponibles
  async verificarCategorias(): Promise<{
    success: boolean;
    puede_crear_conversacion: boolean;
    total_categorias: number;
    categorias_con_documentos: number;
    categorias_disponibles: Array<{id: string, nombre: string, documentos_procesados: number}>;
    mensaje: string;
    error?: string;
  }> {
    const response = await api.get('/api/chat/verificar-categorias');
    return response.data;
  },

  // Iniciar nueva conversación
  async iniciarChat(): Promise<any> {
    const response = await api.post('/api/chat/iniciar');
    return response.data;
  }
};

export const editorAPI = {
  async inicializar(sessionId: string): Promise<{ success: boolean; parrafos: ParagraphData[] }> {
    const response = await api.post('/api/editor/inicializar', {
      session_id: sessionId
    });
    return response.data;
  },

  async procesarEdicion(comando: string, sessionId: string): Promise<EditCommandResult> {
    const response = await apiLong.post<EditCommandResult>('/api/editor/procesar-comando', {
      comando,
      session_id: sessionId
    });
    return response.data;
  },

  async obtenerParrafos(sessionId: string): Promise<{ parrafos: ParagraphData[] }> {
    const response = await api.get(`/api/editor/parrafos/${sessionId}`);
    return response.data;
  },

  async obtenerHistorial(sessionId: string): Promise<{ historial: EditHistoryItem[] }> {
    const response = await api.get(`/api/editor/historial/${sessionId}`);
    return response.data;
  },

  async obtenerTextoCompleto(sessionId: string): Promise<{ contenido: string }> {
    const response = await api.get(`/api/editor/texto-completo/${sessionId}`);
    
    // El backend devuelve 'texto_completo', pero el frontend espera 'contenido'
    if (response.data.success && response.data.texto_completo) {
      return {
        contenido: response.data.texto_completo
      };
    } else {
      throw new Error(response.data.error || 'Error obteniendo texto completo');
    }
  }
};

export const documentAPI = {
  async descargar(sessionId: string): Promise<Blob> {
    const response = await apiLong.get(`/api/documents/descargar/${sessionId}`, {
      responseType: 'blob'
    });
    return response.data;
  }
};

// Nueva API para el sistema de entrenamiento
export const trainingAPI = {
  // Procesar un documento subido (extraer texto y vectorizar)
  async procesarDocumento(documentId: string): Promise<ProcessDocumentResult> {
    const response = await apiLong.post<ProcessDocumentResult>('/api/training/process-document', {
      document_id: documentId
    });
    return response.data;
  },

  // Obtener estado de procesamiento de un documento
  async obtenerEstadoProcesamiento(documentId: string): Promise<DocumentProcessingStatus> {
    const response = await api.get<DocumentProcessingStatus>(`/api/training/document-status/${documentId}`);
    return response.data;
  },

  // Reprocesar un documento que falló
  async reprocesarDocumento(documentId: string): Promise<ProcessDocumentResult> {
    const response = await apiLong.post<ProcessDocumentResult>('/api/training/reprocess-document', {
      document_id: documentId
    });
    return response.data;
  },

  // Obtener estadísticas del entrenamiento
  async obtenerEstadisticas(): Promise<{
    total_documentos: number;
    documentos_procesados: number;
    documentos_pendientes: number;
    documentos_error: number;
    colecciones_qdrant: string[];
    tipos_demanda: { [key: string]: number };
  }> {
    const response = await api.get('/api/training/statistics');
    return response.data;
  },

  // Eliminar documento del entrenamiento (Supabase + Qdrant)
  async eliminarDocumento(documentId: string): Promise<{ success: boolean; message?: string }> {
    const response = await api.delete(`/api/training/document/${documentId}`);
    return response.data;
  },

  // Obtener contenido extraído de un documento
  async obtenerContenidoExtraido(documentId: string): Promise<{
    texto_extraido: string;
    secciones_extraidas: any;
    metadata: any;
  }> {
    const response = await api.get(`/api/training/document-content/${documentId}`);
    return response.data;
  },

  // Buscar documentos similares usando Qdrant
  async buscarDocumentosSimilares(query: string, tipodemanda?: string, limit: number = 5): Promise<{
    resultados: Array<{
      id: string;
      score: number;
      documento: any;
      texto_relevante: string;
    }>;
  }> {
    const response = await api.post('/api/training/search-similar', {
      query,
      tipo_demanda: tipodemanda,
      limit
    });
    return response.data;
  }
};

// Interfaces para categorías
export interface Category {
  id: string;
  user_id: string;
  nombre: string;
  descripcion?: string;
  color: string;
  icon: string;
  activo: boolean;
  created_at: string;
  updated_at: string;
}

export interface CategoryCreate {
  nombre: string;
  descripcion?: string;
  color?: string;
  icon?: string;
}

export interface CategoryUpdate {
  nombre?: string;
  descripcion?: string;
  color?: string;
  icon?: string;
}

export interface CategoryStats {
  categoria_id: string;
  nombre: string;
  color: string;
  icon: string;
  total_documentos: number;
  documentos_procesados: number;
  documentos_pendientes: number;
  total_anotaciones?: number;
}

// API para gestión de categorías personalizadas
export const categoryAPI = {
  // Crear categoría
  async crearCategoria(data: CategoryCreate): Promise<{ success: boolean; category: Category }> {
    const response = await api.post('/api/training/categories', data);
    return response.data;
  },

  // Obtener categorías del usuario
  async obtenerCategorias(search?: string): Promise<{ success: boolean; categories: Category[]; total: number }> {
    const params = new URLSearchParams();
    if (search) {
      params.append('search', search);
    }
    
    const response = await api.get(`/api/training/categories?${params}`);
    return response.data;
  },

  // Obtener estadísticas de categorías
  async obtenerEstadisticasCategorias(): Promise<{
    success: boolean;
    categories: CategoryStats[];
    total_categories: number;
    total_documents: number;
  }> {
    const response = await api.get('/api/training/categories/statistics');
    return response.data;
  },

  // Actualizar categoría
  async actualizarCategoria(categoryId: string, data: CategoryUpdate): Promise<{ 
    success: boolean; 
    category: Category 
  }> {
    const response = await api.put(`/api/training/categories/${categoryId}`, data);
    return response.data;
  },

  // Eliminar categoría
  async eliminarCategoria(categoryId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`/api/training/categories/${categoryId}`);
    return response.data;
  },

  // Crear categorías por defecto
  async crearCategoriasDefecto(): Promise<{ 
    success: boolean; 
    categories: Category[]; 
    message: string 
  }> {
    const response = await api.post('/api/training/categories/default');
    return response.data;
  },

  // Subir documento con categoría
  async subirDocumento(
    file: File, 
    categoriaId: string, 
    tipoDemanda: string
  ): Promise<{ success: boolean; message: string; filename: string }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('categoria_id', categoriaId);
    formData.append('tipo_demanda', tipoDemanda);
    
    const response = await apiLong.post('/api/training/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    });
    
    return response.data;
  },

  // Buscar documentos similares
  async buscarDocumentosSimilares(
    query: string, 
    categoriaId?: string, 
    limit: number = 5
  ): Promise<{
    success: boolean;
    query: string;
    results: Array<{
      id: string;
      score: number;
      filename: string;
      tipo_demanda: string;
      categoria_id: string;
      texto_relevante: string;
      secciones: any;
    }>;
    total: number;
  }> {
    const params = new URLSearchParams({
      query,
      limit: limit.toString()
    });
    
    if (categoriaId) {
      params.append('categoria_id', categoriaId);
    }
    
    const response = await api.get(`/api/training/search?${params}`);
    return response.data;
  },

  // Obtener estadísticas de colección Qdrant
  async obtenerEstadisticasColeccion(): Promise<{
    success: boolean;
    total_documents: number;
    collection_exists: boolean;
    collection_name?: string;
  }> {
    const response = await api.get('/api/training/collection/stats');
    return response.data;
  },

  // Eliminar documento
  async eliminarDocumento(documentId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`/api/training/documents/${documentId}`);
    return response.data;
  },

  // Obtener documentos del usuario (OPTIMIZADO con paginación)
  async obtenerDocumentos(params?: {
    categoria_id?: string;
    estado?: string;
    limit?: number;
    offset?: number;
  }): Promise<{
    success: boolean;
    documents: any[];
    total: number;
    pagination?: {
      limit: number;
      offset: number;
      has_more: boolean;
    };
    performance?: {
      method: string;
      query_time?: string;
      note?: string;
    };
  }> {
    const searchParams = new URLSearchParams();
    
    if (params?.categoria_id) searchParams.append('categoria_id', params.categoria_id);
    if (params?.estado) searchParams.append('estado', params.estado);
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());
    
    const response = await api.get(`/api/training/documents?${searchParams}`);
    return response.data;
  },

  // Obtener URL de descarga de documento
  async obtenerUrlDescarga(documentId: string): Promise<{
    success: boolean;
    download_url: string;
    filename: string;
  }> {
    const response = await api.get(`/api/training/documents/${documentId}/download`);
    return response.data;
  },

  // Obtener contenido extraído de documento con formato rico
  async obtenerContenidoDocumento(documentId: string, formatType: 'plain' | 'rich' | 'html' = 'html'): Promise<{
    success: boolean;
    document?: {
      id: string;
      nombre_archivo: string;
      tipo_demanda: string;
      contenido: string;
      estado_procesamiento: string;
      tiene_formato_rico?: boolean;
      metadatos_formato?: any;
      format_type?: string;
      version_extraccion?: string;
      warning?: string;
    };
    error?: string;
    estado_procesamiento?: string;
  }> {
    const response = await api.get(`/api/training/documents/${documentId}/content`, {
      params: { format_type: formatType }
    });
    return response.data;
  }
};

// ======================================
// API de Gestión de Carpetas
// ======================================

export interface Carpeta {
  id: string;
  abogado_id: string;
  nombre: string;
  descripcion?: string;
  color: string;
  icono: string;
  orden: number;
  created_at: string;
  updated_at: string;
}

export interface CarpetaCreate {
  nombre: string;
  descripcion?: string;
  color?: string;
  icono?: string;
}

export interface CarpetaUpdate {
  nombre?: string;
  descripcion?: string;
  color?: string;
  icono?: string;
}

export const folderAPI = {
  // Obtener todas las carpetas
  async obtenerCarpetas(): Promise<{
    success: boolean;
    carpetas: Carpeta[];
  }> {
    const response = await api.get('/api/folders/');
    return response.data;
  },

  // Crear nueva carpeta
  async crearCarpeta(data: CarpetaCreate): Promise<{
    success: boolean;
    message: string;
    carpeta: Carpeta;
  }> {
    const response = await api.post('/api/folders/', data);
    return response.data;
  },

  // Eliminar carpeta
  async eliminarCarpeta(carpetaId: string): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await api.delete(`/api/folders/${carpetaId}`);
    return response.data;
  },

  // Actualizar carpeta
  async actualizarCarpeta(carpetaId: string, data: CarpetaUpdate): Promise<{
    success: boolean;
    message: string;
    carpeta: Carpeta;
  }> {
    const response = await api.put(`/api/folders/${carpetaId}`, data);
    return response.data;
  }
};

// === ANOTACIONES API ===

// Extended types for API operations
export interface AnnotationDB {
  id: string;
  documento_id: string;
  abogado_id: string;
  pagina?: number;
  posicion_inicio?: number;
  posicion_fin?: number;
  texto_seleccionado: string;
  tipo_anotacion: 'comentario' | 'precedente' | 'estrategia' | 'problema';
  titulo?: string;
  contenido: string;
  etiquetas: string[];
  color: string;
  prioridad: 1 | 2 | 3;
  privacidad: 'privado' | 'compartido';
  created_at: string;
  updated_at: string;
}

export interface AnnotationTemplateDB {
  id: string;
  abogado_id: string;
  nombre: string;
  descripcion?: string;
  tipo_anotacion: 'comentario' | 'precedente' | 'estrategia' | 'problema';
  plantilla_contenido: string;
  etiquetas_sugeridas: string[];
  color_defecto: string;
  uso_frecuente: boolean;
  activo: boolean;
  created_at: string;
  updated_at: string;
}

export interface AnnotationCreate {
  pagina?: number;
  posicion_inicio?: number;
  posicion_fin?: number;
  texto_seleccionado: string;
  tipo_anotacion?: 'comentario' | 'precedente' | 'estrategia' | 'problema';
  titulo?: string;
  contenido: string;
  etiquetas?: string[];
  color?: string;
  prioridad?: 1 | 2 | 3;
  privacidad?: 'privado' | 'compartido';
}

export interface AnnotationUpdate {
  titulo?: string;
  contenido?: string;
  etiquetas?: string[];
  color?: string;
  prioridad?: 1 | 2 | 3;
  privacidad?: 'privado' | 'compartido';
  tipo_anotacion?: 'comentario' | 'precedente' | 'estrategia' | 'problema';
}

export interface TemplateCreate {
  nombre: string;
  descripcion?: string;
  tipo_anotacion: 'comentario' | 'precedente' | 'estrategia' | 'problema';
  plantilla_contenido: string;
  etiquetas_sugeridas?: string[];
  color_defecto?: string;
  uso_frecuente?: boolean;
}

export interface TemplateUpdate {
  nombre?: string;
  descripcion?: string;
  tipo_anotacion?: 'comentario' | 'precedente' | 'estrategia' | 'problema';
  plantilla_contenido?: string;
  etiquetas_sugeridas?: string[];
  color_defecto?: string;
  uso_frecuente?: boolean;
  activo?: boolean;
}

export const annotationAPI = {
  // Obtener anotaciones de un documento
  async obtenerAnotaciones(documentId: string): Promise<{
    success: boolean;
    document: Document;
    annotations: AnnotationDB[];
    total: number;
  }> {
    const response = await api.get(`/api/training/documents/${documentId}/annotations`);
    return response.data;
  },

  // Crear nueva anotación
  async crearAnotacion(documentId: string, data: AnnotationCreate): Promise<{
    success: boolean;
    message: string;
    annotation: AnnotationDB;
  }> {
    const response = await api.post(`/api/training/documents/${documentId}/annotations`, data);
    return response.data;
  },

  // Actualizar anotación
  async actualizarAnotacion(annotationId: string, data: AnnotationUpdate): Promise<{
    success: boolean;
    message: string;
    annotation: AnnotationDB;
  }> {
    const response = await api.put(`/api/training/annotations/${annotationId}`, data);
    return response.data;
  },

  // Eliminar anotación
  async eliminarAnotacion(annotationId: string): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await api.delete(`/api/training/annotations/${annotationId}`);
    return response.data;
  },

  // Convertir de AnnotationDB a Annotation para el frontend
  convertToFrontendAnnotation(dbAnnotation: AnnotationDB): Annotation {
    return {
      id: dbAnnotation.id,
      posicion_inicio: dbAnnotation.posicion_inicio || 0,
      posicion_fin: dbAnnotation.posicion_fin || 0,
      contenido_seleccionado: dbAnnotation.texto_seleccionado,
      contenido_anotacion: dbAnnotation.contenido,
      tipo: dbAnnotation.tipo_anotacion,
      etiquetas: dbAnnotation.etiquetas,
      prioridad: dbAnnotation.prioridad,
      created_at: dbAnnotation.created_at,
      author: 'Usuario'
    };
  }
};

export const templateAPI = {
  // Obtener plantillas de anotación
  async obtenerPlantillas(tipoAnotacion?: string): Promise<{
    success: boolean;
    templates: AnnotationTemplateDB[];
    total: number;
  }> {
    const params = tipoAnotacion ? { tipo_anotacion: tipoAnotacion } : {};
    const response = await api.get('/api/training/templates', { params });
    return response.data;
  },

  // Crear nueva plantilla
  async crearPlantilla(data: TemplateCreate): Promise<{
    success: boolean;
    message: string;
    template: AnnotationTemplateDB;
  }> {
    const response = await api.post('/api/training/templates', data);
    return response.data;
  },

  // Actualizar plantilla
  async actualizarPlantilla(templateId: string, data: TemplateUpdate): Promise<{
    success: boolean;
    message: string;
    template: AnnotationTemplateDB;
  }> {
    const response = await api.put(`/api/training/templates/${templateId}`, data);
    return response.data;
  },

  // Eliminar plantilla
  async eliminarPlantilla(templateId: string): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await api.delete(`/api/training/templates/${templateId}`);
    return response.data;
  },

  // Crear plantillas predeterminadas
  async crearPlantillasPredeterminadas(): Promise<{
    success: boolean;
    message: string;
    templates_created: number;
    templates: AnnotationTemplateDB[];
  }> {
    const response = await api.post('/api/training/templates/default');
    return response.data;
  },

  // Convertir de AnnotationTemplateDB a AnnotationTemplate para el frontend
  convertToFrontendTemplate(dbTemplate: AnnotationTemplateDB): AnnotationTemplate {
    return {
      id: dbTemplate.id,
      nombre: dbTemplate.nombre,
      tipo: dbTemplate.tipo_anotacion,
      contenido: dbTemplate.plantilla_contenido,
      etiquetas: dbTemplate.etiquetas_sugeridas,
      prioridad_sugerida: 1,
      is_default: dbTemplate.uso_frecuente,
      created_at: dbTemplate.created_at
    };
  }
};

// === ANÁLISIS MEJORADO CON IA ===
export const enhancedAnalysisAPI = {
  // Mejorar análisis de documento con anotaciones
  async mejorarAnalisisDocumento(documentId: string): Promise<{
    success: boolean;
    message: string;
    enhanced_analysis: any;
  }> {
    const response = await api.post('/api/training/enhance-document-analysis', { document_id: documentId });
    return response.data;
  }
};