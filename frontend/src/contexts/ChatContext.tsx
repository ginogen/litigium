import { createContext, useContext, useReducer, ReactNode, useCallback } from 'react';
import { chatAPI, categoryAPI, Category } from '@/lib/api';

// Tipos
export interface Message {
  id: string;
  type: 'user' | 'bot' | 'error';
  text: string;
  timestamp: string;
  options?: string[];
  showDownload?: boolean;
  showPreview?: boolean;
  showRefresh?: boolean;
}

interface SelectionContext {
  surroundingText: string;
  position: {
    start: number;
    end: number;
  };
  elementType: string;
}

interface ChatState {
  messages: Message[];
  sessionId: string | null;
  isTyping: boolean;
  typingType: 'writing' | 'generating' | 'editing';
  shouldScrollToBottom: boolean;
  isInitialized: boolean;
  categories: Category[];
  isLoadingCategories: boolean;
  isLoadingMessages: boolean;
}

// Acciones del reducer
type ChatAction =
  | { type: 'SET_SESSION_ID'; payload: string }
  | { type: 'ADD_MESSAGE'; payload: Message }
  | { type: 'SET_TYPING'; payload: boolean }
  | { type: 'SET_TYPING_TYPE'; payload: 'writing' | 'generating' | 'editing' }
  | { type: 'SET_SCROLL_TO_BOTTOM'; payload: boolean }
  | { type: 'SET_INITIALIZED'; payload: boolean }
  | { type: 'SET_CATEGORIES'; payload: Category[] }
  | { type: 'SET_LOADING_CATEGORIES'; payload: boolean }
  | { type: 'SET_LOADING_MESSAGES'; payload: boolean }
  | { type: 'CLEAR_MESSAGES' };

// Estado inicial
const initialState: ChatState = {
  messages: [],
  sessionId: null,
  isTyping: false,
  typingType: 'writing',
  shouldScrollToBottom: false,
  isInitialized: false,
  categories: [],
  isLoadingCategories: false,
  isLoadingMessages: false,
};

// Reducer
function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'SET_SESSION_ID':
      return { ...state, sessionId: action.payload };
    case 'ADD_MESSAGE':
      return { 
        ...state, 
        messages: [...state.messages, action.payload],
        shouldScrollToBottom: true
      };
    case 'SET_TYPING':
      return { ...state, isTyping: action.payload };
    case 'SET_TYPING_TYPE':
      return { ...state, typingType: action.payload };
    case 'SET_SCROLL_TO_BOTTOM':
      return { ...state, shouldScrollToBottom: action.payload };
    case 'SET_INITIALIZED':
      return { ...state, isInitialized: action.payload };
    case 'SET_CATEGORIES':
      return { ...state, categories: action.payload };
    case 'SET_LOADING_CATEGORIES':
      return { ...state, isLoadingCategories: action.payload };
    case 'SET_LOADING_MESSAGES':
      return { ...state, isLoadingMessages: action.payload };
    case 'CLEAR_MESSAGES':
      return { ...state, messages: [] };
    default:
      return state;
  }
}

// Contexto
interface ChatContextType {
  state: ChatState;
  initialize: () => Promise<void>;
  sendMessage: (text: string, selectionContext?: SelectionContext) => Promise<void>;
  selectOption: (option: string) => Promise<void>;
  loadCategories: () => Promise<void>;
  loadMessages: (sessionId: string) => Promise<void>;
  clear: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

// Provider
interface ChatProviderProps {
  children: ReactNode;
}

export function ChatProvider({ children }: ChatProviderProps) {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  // Función para agregar mensaje
  const addMessage = useCallback((message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      text: message.text || '',
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      timestamp: new Date().toLocaleTimeString('es-ES', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    };
    dispatch({ type: 'ADD_MESSAGE', payload: newMessage });
  }, []);

  // Función helper para activar typing con tipo específico
  const setTypingWithType = useCallback((isTyping: boolean, type: 'writing' | 'generating' | 'editing' = 'writing') => {
    if (isTyping) {
      dispatch({ type: 'SET_TYPING_TYPE', payload: type });
    }
    dispatch({ type: 'SET_TYPING', payload: isTyping });
  }, []);

  // Cargar categorías
  const loadCategories = useCallback(async () => {
    try {
      dispatch({ type: 'SET_LOADING_CATEGORIES', payload: true });
      
      // Agregar timeout para evitar requests colgados
      const response = await Promise.race([
        categoryAPI.obtenerCategorias(),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Timeout cargando categorías')), 12000)
        )
      ]) as any;
      
      if (response.success) {
        dispatch({ type: 'SET_CATEGORIES', payload: response.categories });
      } else {
        console.warn('⚠️ No se pudieron cargar las categorías');
      }
    } catch (error: any) {
      console.error('Error cargando categorías:', error);
      if (error.message === 'Timeout cargando categorías') {
        console.warn('⚠️ Timeout cargando categorías - usando array vacío');
      }
      // En caso de error, asegurar que categories quede como array vacío
      dispatch({ type: 'SET_CATEGORIES', payload: [] });
    } finally {
      dispatch({ type: 'SET_LOADING_CATEGORIES', payload: false });
    }
  }, []);

  // Cargar mensajes de una sesión existente
  const loadMessages = useCallback(async (sessionId: string) => {
    try {
      console.log('🔍 ChatContext.loadMessages - sessionId:', sessionId);
      
      // Activar estado de carga
      dispatch({ type: 'SET_LOADING_MESSAGES', payload: true });
      
      // Limpiar inmediatamente los mensajes actuales para UX más rápida
      dispatch({ type: 'CLEAR_MESSAGES' });
      
      // Optimización: timeout más corto para requests lentos
      const response = await Promise.race([
        chatAPI.obtenerMensajes(sessionId),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Timeout cargando mensajes')), 8000)
        )
      ]) as any;
      console.log('✅ Respuesta de obtenerMensajes:', response);
      
      if (response.success && response.mensajes) {
        console.log('📊 Mensajes recibidos:', response.mensajes.length);
        
        // Establecer el session_id actual
        dispatch({ type: 'SET_SESSION_ID', payload: sessionId });
        
        // Agregar mensajes de la base de datos
        response.mensajes.forEach((msg: any, index: number) => {
          console.log(`  ${index + 1}. ${msg.tipo}: ${msg.mensaje?.substring(0, 50)}...`);
          
          const message: Message = {
            id: msg.id || `${Date.now()}-${index}`,
            type: msg.tipo as 'user' | 'bot' | 'error',
            text: msg.mensaje || '',
            timestamp: new Date(msg.created_at).toLocaleTimeString('es-ES', { 
              hour: '2-digit', 
              minute: '2-digit' 
            }),
            options: msg.metadata?.opciones,
            showDownload: msg.metadata?.mostrar_descarga || false,
            showPreview: msg.metadata?.mostrar_preview || false
          };
          dispatch({ type: 'ADD_MESSAGE', payload: message });
        });
        
        // Marcar como inicializado para evitar que se ejecute initialize()
        dispatch({ type: 'SET_INITIALIZED', payload: true });
        
        console.log('✅ Mensajes cargados exitosamente en el contexto');
      } else {
        console.warn('⚠️ No se encontraron mensajes o respuesta inválida');
      }
    } catch (error) {
      console.error('❌ Error cargando mensajes:', error);
    } finally {
      // Desactivar estado de carga
      dispatch({ type: 'SET_LOADING_MESSAGES', payload: false });
    }
  }, []);

  // Inicializar chat
  const initialize = useCallback(async () => {
    if (state.isInitialized) {
      console.log('🔍 Chat ya está inicializado, omitiendo...');
      return;
    }

    try {
      console.log('🚀 Inicializando nueva sesión de chat...');
      
      // Verificar categorías antes de iniciar
      const verificacion = await chatAPI.verificarCategorias();
      console.log('📊 Verificación de categorías en initialize:', verificacion);
      
      if (!verificacion.puede_crear_conversacion) {
        console.log('❌ No se puede crear conversación, faltan categorías');
        const mensajeError = verificacion.total_categorias === 0 
          ? 'Para usar el chat, primero debes crear categorías y subir documentos en la sección "Entrenar".'
          : `Tienes ${verificacion.total_categorias} categorías pero ninguna tiene documentos procesados. Ve a "Entrenar" para subir documentos.`;
        
        addMessage({
          type: 'error',
          text: mensajeError
        });
        
        // Marcar como inicializado incluso si hay errores para evitar loops
        dispatch({ type: 'SET_INITIALIZED', payload: true });
        return;
      }
      
      // Cargar categorías
      await loadCategories();
      
      const response = await chatAPI.iniciar();
      console.log('📱 Respuesta de iniciar:', response);
      
      if (!response.session_id) {
        throw new Error('El servidor no devolvió un session_id válido');
      }
      
      dispatch({ type: 'SET_SESSION_ID', payload: response.session_id });
      
      // Agregar mensaje inicial del bot automáticamente
      addMessage({
        type: 'bot',
        text: `¡Hola doctor! Soy su asistente legal inteligente. 🏛️

**Para generar una demanda, puede:**

📤 **Subir archivos:** telegramas, cartas documento, recibos, anotaciones, etc.
💬 **Escribir detalles:** datos del cliente, hechos del caso, tipo de demanda
🔄 **Combinar ambos:** La información se consolidará automáticamente

¿Con qué tipo de caso necesita ayuda? Puede contarme los detalles o subir documentos directamente.`
      });
      
      dispatch({ type: 'SET_INITIALIZED', payload: true });
      console.log('✅ Chat inicializado exitosamente con sessionId:', response.session_id);
    } catch (error) {
      console.error('❌ Error inicializando chat:', error);
      addMessage({
        type: 'error',
        text: 'Error al inicializar el sistema. Por favor, recarga la página.'
      });
      // Marcar como inicializado para evitar reintentos infinitos
      dispatch({ type: 'SET_INITIALIZED', payload: true });
    }
  }, [state.isInitialized, addMessage, loadCategories]);

  // Enviar mensaje
  const sendMessage = useCallback(async (text: string, selectionContext?: SelectionContext) => {
    if (!text.trim()) return;
    
    console.log('📤 sendMessage iniciado:', { 
      text: text.substring(0, 50), 
      sessionId: state.sessionId, 
      isInitialized: state.isInitialized 
    });
    
    // Si no hay sesión, inicializar primero
    if (!state.sessionId || !state.isInitialized) {
      console.log('🔄 Inicializando sesión antes de enviar mensaje...');
      
      // Llamar a initialize y capturar el sessionId directamente
      try {
        await initialize();
        
        // Obtener el sessionId directamente de la respuesta de initialize
        const response = await chatAPI.iniciar();
        if (response.session_id) {
          console.log('✅ SessionId obtenido directamente:', response.session_id);
          
          // Usar el sessionId directamente sin depender del estado
          const sessionIdToUse = response.session_id;
          
          console.log('📤 Enviando mensaje con sessionId directo:', sessionIdToUse);

          // Agregar mensaje del usuario
          let userMessage = text;
          if (selectionContext) {
            userMessage = `Contexto seleccionado: "${selectionContext.surroundingText.substring(
              selectionContext.position.start, 
              selectionContext.position.end
            )}" | Instrucción: ${text}`;
          }

          addMessage({
            type: 'user',
            text: userMessage
          });

          // Determinar tipo de operación según el contexto
          let operationType: 'writing' | 'generating' | 'editing' = 'writing';
          
          if (selectionContext) {
            operationType = 'editing';
          } else {
            const isGenerationRequest = /\b(generar|crear|redactar|escribir|hacer).*demanda\b/i.test(text) ||
                                        /\b(demanda|solicitud|escrito|documento).*(?:laboral|civil|penal)\b/i.test(text) ||
                                        text.toLowerCase().includes('quiero una demanda') ||
                                        text.toLowerCase().includes('necesito un escrito');
            
            if (isGenerationRequest) {
              operationType = 'generating';
            }
          }

          setTypingWithType(true, operationType);

          try {
            const response = await chatAPI.enviarMensaje(text, sessionIdToUse);
            
            setTypingWithType(false);

            addMessage({
              type: 'bot',
              text: response.respuesta || 'Error: respuesta vacía del servidor',
              options: response.opciones,
              showDownload: response.mostrar_descarga,
              showPreview: response.mostrar_preview,
              showRefresh: response.mostrar_refrescar
            });

            if (response.mostrar_preview) {
              console.log('🔍 Abriendo preview automáticamente para sessionId:', sessionIdToUse);
              setTimeout(() => {
                const event = new CustomEvent('openCanvas', { 
                  detail: { mode: 'preview', sessionId: sessionIdToUse } 
                });
                window.dispatchEvent(event);
              }, 500);
            }
          } catch (error) {
            setTypingWithType(false);
            console.error('❌ Error enviando mensaje:', error);
            addMessage({
              type: 'error',
              text: 'Error enviando mensaje. Por favor, intenta de nuevo.'
            });
          }
          
          return; // Salir aquí para evitar el procesamiento normal
        }
      } catch (error) {
        console.error('❌ Error en inicialización:', error);
        addMessage({
          type: 'error',
          text: 'Error al inicializar el chat. Por favor, recarga la página.'
        });
        return;
      }
    }

    if (!state.sessionId) {
      console.error('❌ sessionId es null - esto no debería pasar después de la inicialización');
      return;
    }
    
    console.log('📤 Enviando mensaje con sessionId:', state.sessionId);

    // Agregar mensaje del usuario
    let userMessage = text;
    if (selectionContext) {
      userMessage = `Contexto seleccionado: "${selectionContext.surroundingText.substring(
        selectionContext.position.start, 
        selectionContext.position.end
      )}" | Instrucción: ${text}`;
    }

    addMessage({
      type: 'user',
      text: userMessage
    });

    // Determinar tipo de operación según el contexto
    let operationType: 'writing' | 'generating' | 'editing' = 'writing';
    
    if (selectionContext) {
      // Si hay contexto de selección, es una edición
      operationType = 'editing';
    } else {
      // Detectar si es una solicitud de generación de demanda
      const isGenerationRequest = /\b(generar|crear|redactar|escribir|hacer).*demanda\b/i.test(text) ||
                                  /\b(demanda|solicitud|escrito|documento).*(?:laboral|civil|penal)\b/i.test(text) ||
                                  text.toLowerCase().includes('quiero una demanda') ||
                                  text.toLowerCase().includes('necesito un escrito');
      
      if (isGenerationRequest) {
        operationType = 'generating';
      }
    }

    // Mostrar indicador de escritura con tipo específico
    setTypingWithType(true, operationType);

    try {
      const response = await chatAPI.enviarMensaje(text, state.sessionId);
      
      // Ocultar indicador de escritura
      setTypingWithType(false);

      // Agregar respuesta del bot
      addMessage({
        type: 'bot',
        text: response.respuesta || 'Error: respuesta vacía del servidor',
        options: response.opciones,
        showDownload: response.mostrar_descarga,
        showPreview: response.mostrar_preview,
        showRefresh: response.mostrar_refrescar
      });

      // Si se generó una demanda y muestra preview, abrir automáticamente el canvas
      if (response.mostrar_preview) {
        console.log('🔍 Abriendo preview automáticamente para sessionId:', state.sessionId);
        // Usar timeout para permitir que el mensaje se renderice primero
        setTimeout(() => {
          // Disparar evento personalizado para abrir canvas
          const event = new CustomEvent('openCanvas', { 
            detail: { mode: 'preview', sessionId: state.sessionId } 
          });
          window.dispatchEvent(event);
        }, 500);
      }

    } catch (error) {
      setTypingWithType(false);
      console.error('Error enviando mensaje:', error);
      
      addMessage({
        type: 'error',
        text: 'Error al enviar el mensaje. Por favor, inténtalo de nuevo.'
      });
    }
  }, [state.sessionId, state.isInitialized, addMessage, initialize]);

  // Seleccionar opción
  const selectOption = useCallback(async (option: string) => {
    await sendMessage(option);
  }, [sendMessage]);

  // Limpiar mensajes
  const clear = useCallback(() => {
    dispatch({ type: 'CLEAR_MESSAGES' });
    dispatch({ type: 'SET_INITIALIZED', payload: false });
    dispatch({ type: 'SET_SESSION_ID', payload: '' });
  }, []);

  const value: ChatContextType = {
    state,
    initialize,
    sendMessage,
    selectOption,
    loadCategories,
    loadMessages,
    clear
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
}

// Hook personalizado
export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
} 