import React, { createContext, useContext, useReducer, ReactNode, useCallback, useEffect } from 'react';
import { editorAPI, documentAPI, ParagraphData, EditHistoryItem } from '../lib/api';

// Tipos
export type CanvasMode = 'preview' | 'editor';

interface CanvasState {
  isOpen: boolean;
  mode: CanvasMode;
  currentDocument: string;
  paragraphs: ParagraphData[];
  editHistory: EditHistoryItem[];
  isEditorInitialized: boolean;
  isLoading: boolean;
}

// Acciones del reducer
type CanvasAction =
  | { type: 'SET_OPEN'; payload: boolean }
  | { type: 'SET_MODE'; payload: CanvasMode }
  | { type: 'SET_CURRENT_DOCUMENT'; payload: string }
  | { type: 'SET_PARAGRAPHS'; payload: ParagraphData[] }
  | { type: 'SET_EDIT_HISTORY'; payload: EditHistoryItem[] }
  | { type: 'SET_EDITOR_INITIALIZED'; payload: boolean }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'ADD_EDIT_HISTORY_ITEM'; payload: EditHistoryItem };

// Estado inicial
const initialState: CanvasState = {
  isOpen: false,
  mode: 'preview',
  currentDocument: '',
  paragraphs: [],
  editHistory: [],
  isEditorInitialized: false,
  isLoading: false,
};

// Reducer
function canvasReducer(state: CanvasState, action: CanvasAction): CanvasState {
  switch (action.type) {
    case 'SET_OPEN':
      return { ...state, isOpen: action.payload };
    case 'SET_MODE':
      return { ...state, mode: action.payload };
    case 'SET_CURRENT_DOCUMENT':
      return { ...state, currentDocument: action.payload };
    case 'SET_PARAGRAPHS':
      return { ...state, paragraphs: action.payload };
    case 'SET_EDIT_HISTORY':
      return { ...state, editHistory: action.payload };
    case 'SET_EDITOR_INITIALIZED':
      return { ...state, isEditorInitialized: action.payload };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'ADD_EDIT_HISTORY_ITEM':
      return { 
        ...state, 
        editHistory: [...state.editHistory, action.payload] 
      };
    default:
      return state;
  }
}

// Contexto
interface CanvasContextType {
  state: CanvasState;
  open: (mode?: CanvasMode, content?: string) => Promise<void>;
  close: () => void;
  toggleMode: () => void;
  loadCurrentDocument: (sessionId: string) => Promise<void>;
  initializeEditor: (sessionId: string) => Promise<void>;
  processEditCommand: (command: string, sessionId: string) => Promise<{ success: boolean; message?: string; error?: string }>;
  loadEditHistory: (sessionId: string) => Promise<void>;
  downloadDocument: (sessionId: string) => Promise<void>;
}

const CanvasContext = createContext<CanvasContextType | undefined>(undefined);

// Provider
interface CanvasProviderProps {
  children: ReactNode;
}

export function CanvasProvider({ children }: CanvasProviderProps) {
  const [state, dispatch] = useReducer(canvasReducer, initialState);

  // Abrir canvas
  const open = useCallback(async (mode: CanvasMode = 'preview', content?: string) => {
    dispatch({ type: 'SET_MODE', payload: mode });
    dispatch({ type: 'SET_OPEN', payload: true });
    
    if (content) {
      dispatch({ type: 'SET_CURRENT_DOCUMENT', payload: content });
    }
  }, []);

  // Cerrar canvas
  const close = useCallback(() => {
    dispatch({ type: 'SET_OPEN', payload: false });
  }, []);

  // Alternar modo
  const toggleMode = useCallback(() => {
    const newMode = state.mode === 'preview' ? 'editor' : 'preview';
    dispatch({ type: 'SET_MODE', payload: newMode });
  }, [state.mode]);

  // Cargar documento actual
  const loadCurrentDocument = useCallback(async (sessionId: string) => {
    if (!sessionId) return;
    
    dispatch({ type: 'SET_LOADING', payload: true });
    
    try {
      const response = await editorAPI.obtenerTextoCompleto(sessionId);
      dispatch({ type: 'SET_CURRENT_DOCUMENT', payload: response.contenido });
    } catch (error) {
      console.error('Error cargando documento:', error);
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, []);

  // Función para parsear contenido a párrafos
  const parseContentToParagraphs = useCallback((content: string): ParagraphData[] => {
    const lines = content.split('\n').filter(line => line.trim());
    
    return lines.map((line, index) => {
      let tipo = 'general';
      
      if (line.toLowerCase().includes('hecho') || line.toLowerCase().includes('hechos')) {
        tipo = 'hechos';
      } else if (line.toLowerCase().includes('derecho') || line.toLowerCase().includes('fundament')) {
        tipo = 'derecho';
      } else if (line.toLowerCase().includes('petitorio') || line.toLowerCase().includes('solicita')) {
        tipo = 'petitorio';
      } else if (line.toLowerCase().includes('prueba')) {
        tipo = 'prueba';
      }
      
      return {
        numero: index + 1,
        contenido: line.trim(),
        tipo,
        modificado: false
      };
    });
  }, []);

  // Cargar historial de ediciones
  const loadEditHistory = useCallback(async (sessionId: string) => {
    if (!sessionId) return;
    
    try {
      const response = await editorAPI.obtenerHistorial(sessionId);
      dispatch({ type: 'SET_EDIT_HISTORY', payload: response.historial });
    } catch (error) {
      console.error('Error cargando historial:', error);
    }
  }, []);

  // Inicializar editor
  const initializeEditor = useCallback(async (sessionId: string) => {
    if (!sessionId || state.isEditorInitialized) return;
    
    dispatch({ type: 'SET_LOADING', payload: true });
    
    try {
      const response = await editorAPI.inicializar(sessionId);
      
      if (response.success) {
        dispatch({ type: 'SET_PARAGRAPHS', payload: response.parrafos });
        dispatch({ type: 'SET_EDITOR_INITIALIZED', payload: true });
        
        // También cargar historial
        await loadEditHistory(sessionId);
      } else {
        // Si no hay párrafos del servidor, generar desde el documento actual
        if (state.currentDocument) {
          const parsedParagraphs = parseContentToParagraphs(state.currentDocument);
          dispatch({ type: 'SET_PARAGRAPHS', payload: parsedParagraphs });
          dispatch({ type: 'SET_EDITOR_INITIALIZED', payload: true });
        }
      }
    } catch (error) {
      console.error('Error inicializando editor:', error);
      
      // Fallback: generar párrafos desde el documento actual
      if (state.currentDocument) {
        const parsedParagraphs = parseContentToParagraphs(state.currentDocument);
        dispatch({ type: 'SET_PARAGRAPHS', payload: parsedParagraphs });
        dispatch({ type: 'SET_EDITOR_INITIALIZED', payload: true });
      }
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [state.isEditorInitialized, state.currentDocument, parseContentToParagraphs, loadEditHistory]);

  // Procesar comando de edición
  const processEditCommand = useCallback(async (command: string, sessionId: string) => {
    if (!command.trim() || !sessionId) {
      return { success: false, error: 'Comando o sesión inválidos' };
    }
    
    try {
      const response = await editorAPI.procesarEdicion(command, sessionId);
      
      if (response.success) {
        // Actualizar párrafos si están disponibles
        if (response.parrafos_actualizados) {
          dispatch({ type: 'SET_PARAGRAPHS', payload: response.parrafos_actualizados });
        }
        
        // Agregar al historial
        const historyItem: EditHistoryItem = {
          id: Date.now().toString(),
          comando: command,
          operacion: 'modificar', // Esto debería venir del servidor
          timestamp: new Date().toISOString(),
          exito: true,
          mensaje: response.message,
          resultado: response
        };
        
        dispatch({ type: 'ADD_EDIT_HISTORY_ITEM', payload: historyItem });
        
        // Recargar documento completo
        await loadCurrentDocument(sessionId);
        
        return { success: true, message: response.message };
      } else {
        // Agregar error al historial
        const historyItem: EditHistoryItem = {
          id: Date.now().toString(),
          comando: command,
          operacion: 'error',
          timestamp: new Date().toISOString(),
          exito: false,
          mensaje: response.error
        };
        
        dispatch({ type: 'ADD_EDIT_HISTORY_ITEM', payload: historyItem });
        
        return { success: false, error: response.error };
      }
    } catch (error) {
      console.error('Error procesando comando:', error);
      
      const historyItem: EditHistoryItem = {
        id: Date.now().toString(),
        comando: command,
        operacion: 'error',
        timestamp: new Date().toISOString(),
        exito: false,
        mensaje: 'Error de conexión'
      };
      
      dispatch({ type: 'ADD_EDIT_HISTORY_ITEM', payload: historyItem });
      
      return { success: false, error: 'Error de conexión' };
    }
  }, [loadCurrentDocument]);

  // Descargar documento
  const downloadDocument = useCallback(async (sessionId: string) => {
    if (!sessionId) return;
    
    try {
      const blob = await documentAPI.descargar(sessionId);
      
      // Crear URL para descargar
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `demanda_${new Date().toISOString().split('T')[0]}.docx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error descargando documento:', error);
    }
  }, []);

  // Escuchar eventos de apertura automática del canvas
  useEffect(() => {
    const handleOpenCanvas = (event: CustomEvent) => {
      const { mode, sessionId } = event.detail;
      if (sessionId) {
        open(mode, undefined);
        if (mode === 'preview') {
          loadCurrentDocument(sessionId);
        }
      }
    };

    window.addEventListener('openCanvas', handleOpenCanvas as EventListener);
    
    return () => {
      window.removeEventListener('openCanvas', handleOpenCanvas as EventListener);
    };
  }, [open, loadCurrentDocument]);

  const value: CanvasContextType = {
    state,
    open,
    close,
    toggleMode,
    loadCurrentDocument,
    initializeEditor,
    processEditCommand,
    loadEditHistory,
    downloadDocument
  };

  return (
    <CanvasContext.Provider value={value}>
      {children}
    </CanvasContext.Provider>
  );
}

// Hook personalizado
export function useCanvas() {
  const context = useContext(CanvasContext);
  if (context === undefined) {
    throw new Error('useCanvas must be used within a CanvasProvider');
  }
  return context;
} 