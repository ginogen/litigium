import React, { createContext, useContext, useCallback, ReactNode } from 'react';
import { supabase } from './AuthContext';
import { useAuth } from './AuthContext';
import { chatAPI } from '../lib';

// Tipos basados en tu esquema de Supabase (UUID)
export interface ChatSession {
  id: string; // UUID como string
  session_id: string;
  abogado_id: string; // UUID como string
  carpeta_id?: string; // UUID como string
  titulo: string;
  tipo_demanda?: string;
  estado: string;
  cliente_nombre?: string;
  cliente_dni?: string;
  cliente_datos: any;
  hechos_adicionales?: string;
  notas_abogado?: string;
  created_at: string;
  updated_at: string;
  archivado_at?: string;
}

export interface ChatMessage {
  id: string; // UUID como string
  sesion_id: string; // UUID como string
  tipo: string;
  mensaje: string;
  metadata: any;
  created_at: string;
}

export interface ChatFolder {
  id: string; // UUID como string
  abogado_id: string; // UUID como string
  nombre: string;
  descripcion?: string;
  color: string;
  icono: string;
  parent_id?: string; // UUID como string
  orden: number;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string; // UUID como string
  sesion_id: string; // UUID como string
  abogado_id: string; // UUID como string
  texto_demanda: string;
  version: number;
  archivo_docx_url?: string;
  archivo_pdf_url?: string;
  modelo_usado: string;
  casos_consultados: number;
  tiempo_generacion?: number;
  created_at: string;
  updated_at: string;
}

export interface TrainingDocument {
  id: string; // UUID como string
  abogado_id: string; // UUID como string
  nombre_archivo: string;
  archivo_url: string;
  tipo_mime?: string;
  tamaño_bytes?: number;
  tipo_demanda: string;
  categoria?: string;
  tags: string[];
  estado_procesamiento: string;
  vectorizado: boolean;
  qdrant_collection?: string;
  error_procesamiento?: string;
  texto_extraido?: string;
  secciones_extraidas: any;
  created_at: string;
  processed_at?: string;
}

interface ChatStorageContextType {
  // Folders
  createFolder: (name: string, color?: string) => Promise<ChatFolder>;
  getFolders: () => Promise<ChatFolder[]>;
  updateFolder: (id: string, data: Partial<ChatFolder>) => Promise<void>;
  deleteFolder: (id: string) => Promise<void>;

  // Sessions
  createSession: (titulo: string, carpetaId?: string) => Promise<ChatSession>;
  getSessions: (carpetaId?: string) => Promise<ChatSession[]>;
  updateSession: (id: string, data: Partial<ChatSession>) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  deleteSessionsBulk: (sessionIds: string[]) => Promise<void>;
  moveSession: (sessionId: string, carpetaId: string | null) => Promise<void>;

  // Messages
  saveMessage: (sessionId: string, tipo: string, mensaje: string, metadata?: any) => Promise<ChatMessage>;
  getMessages: (sessionId: string) => Promise<ChatMessage[]>;
  deleteMessage: (id: string) => Promise<void>;

  // Documents
  saveDocument: (sessionId: string, textodemanda: string) => Promise<Document>;
  getDocument: (sessionId: string) => Promise<Document | null>;
  updateDocument: (sessionId: string, textodemanda: string) => Promise<void>;
  deleteDocument: (id: string) => Promise<void>;

  // Training documents
  uploadTrainingDocument: (file: File, tipodemanda: string, categoria?: string) => Promise<string>;
  getTrainingDocuments: () => Promise<TrainingDocument[]>;
}

const ChatStorageContext = createContext<ChatStorageContextType | undefined>(undefined);

// Provider
interface ChatStorageProviderProps {
  children: ReactNode;
}

export function ChatStorageProvider({ children }: ChatStorageProviderProps) {
  const { user, profile } = useAuth();

  // Folders
  const createFolder = useCallback(async (name: string, color?: string): Promise<ChatFolder> => {
    if (!profile) throw new Error('User profile not loaded');

    const { data, error } = await supabase
      .from('carpetas')
      .insert([
        {
          abogado_id: profile.id, // profile.id es el ID del registro de abogados (TEXT)
          nombre: name,
          color: color || '#3B82F6',
          icono: 'folder',
          orden: 0,
        },
      ])
      .select()
      .single();

    if (error) throw error;
    return data;
  }, [profile]);

  const getFolders = useCallback(async (): Promise<ChatFolder[]> => {
    if (!profile) throw new Error('User profile not loaded');

    console.log('🔍 ChatStorageContext.getFolders - profile.id:', profile.id);

    const { data, error } = await supabase
      .from('carpetas')
      .select('*')
      .eq('abogado_id', profile.id)
      .order('orden', { ascending: true });

    if (error) {
      console.error('❌ Error en getFolders:', error);
      throw error;
    }

    console.log('✅ ChatStorageContext.getFolders - encontradas:', data?.length || 0, 'carpetas');
    
    // Debug: mostrar carpetas
    if (data && data.length > 0) {
      data.forEach((folder, i) => {
        console.log(`  ${i+1}. ID: ${folder.id}, Nombre: ${folder.nombre}`);
      });
    }

    return data || [];
  }, [profile]);

  const updateFolder = useCallback(async (id: string, data: Partial<ChatFolder>): Promise<void> => {
    if (!profile) throw new Error('User profile not loaded');

    const { error } = await supabase
      .from('carpetas')
      .update(data)
      .eq('id', id)
      .eq('abogado_id', profile.id);

    if (error) throw error;
  }, [profile]);

  const deleteFolder = useCallback(async (id: string): Promise<void> => {
    if (!profile) throw new Error('User profile not loaded');

    const { error } = await supabase
      .from('carpetas')
      .delete()
      .eq('id', id)
      .eq('abogado_id', profile.id);

    if (error) throw error;
  }, [profile]);

  // Sessions
  const createSession = useCallback(async (titulo: string, carpetaId?: string): Promise<ChatSession> => {
    if (!profile) throw new Error('User profile not loaded');

    // Generar session_id único
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const { data, error } = await supabase
      .from('chat_sesiones')
      .insert([
        {
          session_id: sessionId,
          abogado_id: profile.id,
          carpeta_id: carpetaId,
          titulo,
          estado: 'en_progreso',
          cliente_datos: {},
        },
      ])
      .select()
      .single();

    if (error) throw error;
    return data;
  }, [profile]);

  const getSessions = useCallback(async (carpetaId?: string): Promise<ChatSession[]> => {
    if (!profile) throw new Error('User profile not loaded');

    console.log('🔍 ChatStorageContext.getSessions - profile.id:', profile.id);
    console.log('🔍 ChatStorageContext.getSessions - carpetaId:', carpetaId);

    let query = supabase
      .from('chat_sesiones')
      .select('*')
      .eq('abogado_id', profile.id);

    if (carpetaId) {
      query = query.eq('carpeta_id', carpetaId);
    }

    const { data, error } = await query.order('updated_at', { ascending: false });

    if (error) {
      console.error('❌ Error en getSessions:', error);
      throw error;
    }

    console.log('✅ ChatStorageContext.getSessions - encontradas:', data?.length || 0, 'sesiones');
    
    // Debug: mostrar algunas sesiones
    if (data && data.length > 0) {
      console.log('📊 Primeras 3 sesiones:');
      data.slice(0, 3).forEach((session, i) => {
        console.log(`  ${i+1}. ID: ${session.id}, Session: ${session.session_id}, Título: ${session.titulo}`);
      });
    }

    return data || [];
  }, [profile]);

  const updateSession = useCallback(async (id: string, data: Partial<ChatSession>): Promise<void> => {
    if (!profile) throw new Error('User profile not loaded');

    // Buscar la sesión por ID para obtener el session_id
    const { data: sessionData, error: fetchError } = await supabase
      .from('chat_sesiones')
      .select('session_id')
      .eq('id', id)
      .eq('abogado_id', profile.id)
      .single();

    if (fetchError || !sessionData) throw fetchError || new Error('Session not found');

    // Usar la API del backend para actualizar
    const response = await fetch(`/api/chat/sesion/${sessionData.session_id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error('Error updating session');
    }
  }, [profile]);

  const deleteSession = useCallback(async (sessionId: string): Promise<void> => {
    if (!profile) throw new Error('User profile not loaded');

    // Usar la API del backend para eliminar la sesión
    await chatAPI.eliminarSesion(sessionId);
  }, [profile]);

  const moveSession = useCallback(async (sessionId: string, carpetaId: string | null): Promise<void> => {
    if (!profile) throw new Error('User profile not loaded');

    console.log('📁 Moviendo sesión:', sessionId, 'a carpeta:', carpetaId);
    
    // Usar la API del backend para mover la sesión
    await chatAPI.moverSesion(sessionId, carpetaId);
  }, [profile]);

  // Messages
  const saveMessage = useCallback(async (
    sessionId: string,
    tipo: string,
    mensaje: string,
    metadata?: any
  ): Promise<ChatMessage> => {
    if (!profile) throw new Error('User profile not loaded');

    const { data, error } = await supabase
      .from('chat_mensajes')
      .insert([
        {
          sesion_id: sessionId,
          tipo,
          mensaje,
          metadata: metadata || {},
        },
      ])
      .select()
      .single();

    if (error) throw error;
    return data;
  }, [profile]);

  const getMessages = useCallback(async (sessionId: string): Promise<ChatMessage[]> => {
    const { data, error } = await supabase
      .from('chat_mensajes')
      .select('*')
      .eq('sesion_id', sessionId)
      .order('created_at', { ascending: true });

    if (error) throw error;
    return data || [];
  }, []);

  const deleteMessage = useCallback(async (id: string): Promise<void> => {
    const { error } = await supabase
      .from('chat_mensajes')
      .delete()
      .eq('id', id);

    if (error) throw error;
  }, []);

  // Documents
  const saveDocument = useCallback(async (
    sessionId: string,
    textodemanda: string
  ): Promise<Document> => {
    if (!profile) throw new Error('User profile not loaded');

    const { data, error } = await supabase
      .from('demandas_generadas')
      .upsert([
        {
          sesion_id: sessionId,
          abogado_id: profile.id,
          texto_demanda: textodemanda,
          version: 1,
          modelo_usado: 'gpt-4',
          casos_consultados: 0,
          updated_at: new Date().toISOString(),
        },
      ])
      .select()
      .single();

    if (error) throw error;
    return data;
  }, [profile]);

  const getDocument = useCallback(async (sessionId: string): Promise<Document | null> => {
    const { data, error } = await supabase
      .from('demandas_generadas')
      .select('*')
      .eq('sesion_id', sessionId)
      .single();

    if (error && error.code !== 'PGRST116') throw error;
    return data || null;
  }, []);

  const updateDocument = useCallback(async (sessionId: string, textodemanda: string): Promise<void> => {
    if (!profile) throw new Error('User profile not loaded');

    const { error } = await supabase
      .from('demandas_generadas')
      .update({
        texto_demanda: textodemanda,
        updated_at: new Date().toISOString(),
      })
      .eq('sesion_id', sessionId)
      .eq('abogado_id', profile.id);

    if (error) throw error;
  }, [profile]);

  const deleteDocument = useCallback(async (id: string): Promise<void> => {
    if (!profile) throw new Error('User profile not loaded');

    const { error } = await supabase
      .from('demandas_generadas')
      .delete()
      .eq('id', id)
      .eq('abogado_id', profile.id);

    if (error) throw error;
  }, [profile]);

  // Training documents
  const uploadTrainingDocument = useCallback(async (file: File, tipodemanda: string, categoria?: string): Promise<string> => {
    if (!profile) throw new Error('User profile not loaded');

    const fileName = `${profile.id}/${tipodemanda}/${Date.now()}_${file.name}`;
    
    const { error: uploadError } = await supabase.storage
      .from('documentos-entrenamiento')
      .upload(fileName, file);

    if (uploadError) throw uploadError;

    // Guardar metadata en la tabla
    const { error: dbError } = await supabase
      .from('documentos_entrenamiento')
      .insert([
        {
          abogado_id: profile.id,
          nombre_archivo: file.name,
          archivo_url: fileName,
          tipo_mime: file.type,
          tamaño_bytes: file.size,
          tipo_demanda: tipodemanda,
          categoria: categoria || 'general',
          tags: [],
          estado_procesamiento: 'pendiente',
          vectorizado: false,
          secciones_extraidas: {},
        },
      ]);

    if (dbError) throw dbError;

    return fileName;
  }, [profile]);

  const getTrainingDocuments = useCallback(async (): Promise<TrainingDocument[]> => {
    if (!profile) throw new Error('User profile not loaded');

    const { data, error } = await supabase
      .from('documentos_entrenamiento')
      .select('*')
      .eq('abogado_id', profile.id)
      .order('created_at', { ascending: false });

    if (error) throw error;
    return data || [];
  }, [profile]);

  // Bulk delete sessions
  const deleteSessionsBulk = useCallback(async (sessionIds: string[]): Promise<void> => {
    console.log('🗑️ Eliminación masiva:', sessionIds.length, 'sesiones');
    
    try {
      const response = await chatAPI.eliminarSesionesMasivo(sessionIds);
      console.log(`✅ Eliminación masiva completada: ${response.deleted_count} eliminadas`);
      
      if (response.errors && response.errors.length > 0) {
        console.warn('⚠️ Algunos errores durante eliminación:', response.errors);
      }
    } catch (error) {
      console.error('❌ Error en eliminación masiva:', error);
      throw error;
    }
  }, []);

  const value: ChatStorageContextType = {
    createFolder,
    getFolders,
    updateFolder,
    deleteFolder,
    createSession,
    getSessions,
    updateSession,
    deleteSession,
    deleteSessionsBulk,
    moveSession,
    saveMessage,
    getMessages,
    deleteMessage,
    saveDocument,
    getDocument,
    updateDocument,
    deleteDocument,
    uploadTrainingDocument,
    getTrainingDocuments,
  };

  return (
    <ChatStorageContext.Provider value={value}>
      {children}
    </ChatStorageContext.Provider>
  );
}

// Hook personalizado
export function useChatStorage() {
  const context = useContext(ChatStorageContext);
  if (context === undefined) {
    throw new Error('useChatStorage must be used within a ChatStorageProvider');
  }
  return context;
} 