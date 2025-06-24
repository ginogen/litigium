import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useChat } from '../../contexts/ChatContext';
import { useCanvas } from '../../contexts/CanvasContext';
import { cn } from '@/lib/utils';
import { X, Edit3 } from 'lucide-react';
import { AudioRecorder } from './AudioRecorder';

export function ChatInput() {
  const { sendMessage, state, initialize } = useChat();
  const { state: canvasState } = useCanvas();
  const [inputValue, setInputValue] = useState('');
  const [selectedText, setSelectedText] = useState<string>('');
  const [audioError, setAudioError] = useState<string>('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Detectar texto seleccionado desde el Canvas
  useEffect(() => {
    // Solo procesar si el Canvas está abierto
    if (!canvasState.isOpen) {
      if (selectedText) {
        setSelectedText('');
      }
      return;
    }

    const checkSelectedText = () => {
      try {
        // Detectar si hay texto seleccionado
        const selection = window.getSelection();
        if (!selection || !selection.rangeCount) {
          return;
        }

        const selected = selection.toString().trim();
        
        // Si no hay texto seleccionado, no hacer nada (mantener el estado actual)
        if (!selected || selected.length === 0) {
          return;
        }

        // Verificar que viene del Canvas
        const range = selection.getRangeAt(0);
        const selectedElement = range.commonAncestorContainer;
        
        // Buscar el elemento .word-document-content en la jerarquía
        let currentNode = selectedElement.nodeType === Node.TEXT_NODE 
          ? selectedElement.parentElement 
          : selectedElement as Element;
        
        let isFromCanvas = false;
        while (currentNode && currentNode !== document.body) {
          if (currentNode.classList?.contains('word-document-content')) {
            isFromCanvas = true;
            break;
          }
          currentNode = currentNode.parentElement;
        }
        
        if (isFromCanvas && selected !== selectedText) {
          console.log('📝 Texto seleccionado desde Canvas:', selected.substring(0, 50) + '...');
          setSelectedText(selected);
        }
      } catch (error) {
        console.error('Error detectando selección:', error);
      }
    };

    // Función para limpiar selección solo cuando se hace click fuera de áreas relevantes
    const handleDocumentClick = (event: MouseEvent) => {
      const target = event.target as Element;
      
      // No limpiar si el click es en áreas protegidas
      if (target.closest('.word-document-content') || 
          target.closest('[data-chat-input]') ||
          target.closest('.chat-input-container') ||
          target.closest('.canvas-panel')) {
        return;
      }
      
      // Verificar si realmente no hay selección activa
      const selection = window.getSelection();
      const hasActiveSelection = selection && selection.toString().trim().length > 0;
      
      // Solo limpiar si no hay selección activa y tenemos texto guardado
      if (!hasActiveSelection && selectedText) {
        console.log('🧹 Limpiando selección por click fuera del área');
        setSelectedText('');
        selection?.removeAllRanges();
      }
    };

    // Función para manejar cambios de selección
    const handleSelectionChange = () => {
      // Usar requestAnimationFrame para evitar problemas de timing
      requestAnimationFrame(checkSelectedText);
    };

    // Event listeners con mejor timing
    document.addEventListener('mouseup', handleSelectionChange);
    document.addEventListener('selectionchange', handleSelectionChange);
    document.addEventListener('click', handleDocumentClick);

    return () => {
      document.removeEventListener('mouseup', handleSelectionChange);
      document.removeEventListener('selectionchange', handleSelectionChange);
      document.removeEventListener('click', handleDocumentClick);
    };
  }, [selectedText, canvasState.isOpen]);

  // Limpiar texto seleccionado
  const clearSelectedText = useCallback(() => {
    console.log('🧹 Limpiando texto seleccionado manualmente');
    setSelectedText('');
    window.getSelection()?.removeAllRanges();
  }, []);

  // Función para forzar actualización de selección (para debugging)
  const forceCheckSelection = useCallback(() => {
    const selection = window.getSelection();
    const selected = selection?.toString().trim() || '';
    console.log('🔍 Forzando check de selección:', selected.substring(0, 30) + '...');
    
    if (selected && canvasState.isOpen) {
      setSelectedText(selected);
    }
  }, [canvasState.isOpen]);

  // Auto-resize del textarea
  const adjustTextareaHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = 'auto';
    const scrollHeight = textarea.scrollHeight;
    const newHeight = Math.min(scrollHeight, 200);
    textarea.style.height = `${newHeight}px`;
  }, []);

  useEffect(() => {
    adjustTextareaHeight();
  }, [inputValue, adjustTextareaHeight]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim() || state.isTyping) return;

    const messageText = inputValue.trim();
    
    setInputValue('');
    const currentSelectedText = selectedText;
    setSelectedText('');
    window.getSelection()?.removeAllRanges();
    
    try {
      // Si no hay sesión activa, inicializar primero
      if (!state.sessionId || !state.isInitialized) {
        console.log('🆕 No hay sesión activa, inicializando...');
        await initialize();
      }
      
      // Si hay texto seleccionado, formatear como mensaje de edición y enviar vía chat normal
      if (currentSelectedText && canvasState.isOpen) {
        console.log('🎯 Procesando edición de texto seleccionado...');
        console.log('📝 Texto:', currentSelectedText.substring(0, 50) + '...');
        console.log('💭 Instrucción:', messageText);
        
        // Enviar como mensaje de edición via chat normal (no processEditCommand)
        const editCommand = `Modificar el siguiente texto: "${currentSelectedText}"\n\nInstrucción: ${messageText}`;
        await sendMessage(editCommand);
        
        console.log('📤 Mensaje de edición enviado via chat');
      } else {
        // Mensaje normal sin edición
        await sendMessage(messageText);
      }
    } catch (error) {
      console.error('Error processing message:', error);
      // Fallback a mensaje normal
      try {
        await sendMessage(messageText);
      } catch (fallbackError) {
        console.error('Error in fallback message:', fallbackError);
      }
    }
      }, [inputValue, selectedText, canvasState.isOpen, state.isTyping, state.sessionId, state.isInitialized, sendMessage, initialize]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    } else if (e.key === 'Escape' && selectedText) {
      e.preventDefault();
      clearSelectedText();
    }
  }, [handleSubmit, selectedText, clearSelectedText]);
  
  // Listener global para Esc
  useEffect(() => {
    const handleGlobalKeydown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && selectedText && canvasState.isOpen) {
        e.preventDefault();
        clearSelectedText();
      }
    };

    document.addEventListener('keydown', handleGlobalKeydown);
    
    return () => {
      document.removeEventListener('keydown', handleGlobalKeydown);
    };
  }, [selectedText, canvasState.isOpen, clearSelectedText]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
  }, []);

  // Verificar selección cuando el usuario hace focus en el input
  const handleInputFocus = useCallback(() => {
    if (canvasState.isOpen) {
      // Pequeño delay para asegurar que la selección esté disponible
      setTimeout(() => {
        const selection = window.getSelection();
        const selected = selection?.toString().trim() || '';
        
        if (selected && selected.length > 0 && !selectedText) {
          // Verificar que viene del Canvas
          try {
            const range = selection?.getRangeAt(0);
            if (range) {
              const selectedElement = range.commonAncestorContainer;
              let currentNode = selectedElement.nodeType === Node.TEXT_NODE 
                ? selectedElement.parentElement 
                : selectedElement as Element;
              
              let isFromCanvas = false;
              while (currentNode && currentNode !== document.body) {
                if (currentNode.classList?.contains('word-document-content')) {
                  isFromCanvas = true;
                  break;
                }
                currentNode = currentNode.parentElement;
              }
              
              if (isFromCanvas) {
                console.log('📝 Selección detectada al hacer focus:', selected.substring(0, 50) + '...');
                setSelectedText(selected);
              }
            }
          } catch (error) {
            console.error('Error verificando selección en focus:', error);
          }
        }
      }, 50);
    }
  }, [canvasState.isOpen, selectedText]);

  // Manejar transcripción de audio
  const handleAudioTranscription = useCallback((transcription: string) => {
    setInputValue(transcription);
    setAudioError('');
    // Auto-focus en el textarea después de la transcripción
    setTimeout(() => {
      textareaRef.current?.focus();
    }, 100);
  }, []);

  const handleAudioError = useCallback((error: string) => {
    setAudioError(error);
    setTimeout(() => setAudioError(''), 5000); // Limpiar error después de 5s
  }, []);

  const getPlaceholder = () => {
    if (selectedText && canvasState.isOpen) {
      return "Describe cómo quieres modificar el texto seleccionado...";
    }
    if (state.sessionId) {
      return "Escribe tu mensaje...";
    }
    return "Escribe tu consulta para comenzar...";
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-6 chat-input-container" data-chat-input>
      {/* Error de audio */}
      {audioError && (
        <div className="mb-3 p-3 bg-red-900/30 border border-red-500/30 rounded-lg">
          <div className="text-red-300 text-sm">{audioError}</div>
        </div>
      )}

      {/* Indicador de texto seleccionado */}
      {selectedText && canvasState.isOpen && (
        <div className="mb-3 p-3 bg-blue-900/30 border border-blue-500/30 rounded-lg animate-in slide-in-from-top-2">
          <div className="flex items-start gap-3">
            <Edit3 className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-blue-300">TEXTO SELECCIONADO PARA EDITAR:</span>
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" title="Texto detectado"></div>
                </div>
                <div className="flex items-center gap-2">
                  {/* Botón de debug para forzar detección */}
                  <button
                    onClick={forceCheckSelection}
                    className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/20 p-1 rounded transition-colors text-xs"
                    title="Refrescar selección"
                  >
                    🔄
                  </button>
                  <button
                    onClick={clearSelectedText}
                    className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/20 p-1 rounded transition-colors"
                    title="Cancelar edición (Esc)"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              </div>
              <div className="text-sm text-gray-200 italic bg-gray-800/50 p-2 rounded max-h-20 overflow-auto">
                "{selectedText}"
              </div>
              <div className="text-xs text-blue-400 mt-1">
                {selectedText.length} caracteres seleccionados
              </div>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="w-full">
        <div className={cn(
          "relative flex items-end border rounded-2xl shadow-lg hover:shadow-xl transition-shadow duration-200 focus-within:ring-2 focus-within:border-transparent",
          selectedText && canvasState.isOpen
            ? "bg-blue-900/30 border-blue-500/50 focus-within:ring-blue-500"
            : "bg-gray-700 border-gray-600 focus-within:ring-blue-500"
        )}>
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={handleInputFocus}
            placeholder={getPlaceholder()}
            disabled={state.isTyping}
            className={cn(
              "flex-1 resize-none border-0 bg-transparent py-4 px-4 pr-28 text-white placeholder:text-gray-400 focus:outline-none focus:ring-0",
              "max-h-[200px] overflow-y-auto leading-6",
              state.isTyping && "opacity-50"
            )}
            style={{ height: '24px' }}
            rows={1}
          />
          
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-3">
            {/* Botón de audio */}
            <AudioRecorder
              onTranscriptionComplete={handleAudioTranscription}
              onError={handleAudioError}
              sessionId={state.sessionId && state.isInitialized ? state.sessionId : undefined}
              disabled={state.isTyping}
            />
            
            {/* Botón de envío */}
            <button
              type="submit"
              disabled={!inputValue.trim() || state.isTyping}
              className={cn(
                "p-3 rounded-2xl transition-all duration-200 shadow-lg",
                inputValue.trim() && !state.isTyping
                  ? selectedText && canvasState.isOpen
                    ? "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-xl ring-2 ring-blue-400/50 hover:scale-105"
                    : "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-xl hover:scale-105"
                  : "bg-gray-600/70 text-gray-400 cursor-not-allowed"
              )}
              title={selectedText && canvasState.isOpen ? "Aplicar modificación" : "Enviar mensaje"}
            >
              {state.isTyping ? (
                <div className="w-5 h-5 border-2 border-gray-300 border-t-transparent rounded-full animate-spin" />
              ) : selectedText && canvasState.isOpen ? (
                <Edit3 className="w-5 h-5" />
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" className="w-5 h-5">
                  <path d="M7 11L12 6L17 11M12 18V7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              )}
            </button>
          </div>
        </div>
        
        {/* Texto de ayuda contextual */}
        <div className="flex justify-center mt-3">
          <p className="text-xs text-gray-400 text-center">
            {selectedText && canvasState.isOpen ? (
              <>
                Describe el cambio que quieres hacer • 
                <kbd className="px-1.5 py-0.5 text-xs bg-gray-600 text-gray-200 rounded border border-gray-500 ml-1">Esc</kbd> para cancelar
              </>
            ) : (
              <>
                Presiona <kbd className="px-1.5 py-0.5 text-xs bg-gray-600 text-gray-200 rounded border border-gray-500">Enter</kbd> para enviar, 
                <kbd className="px-1.5 py-0.5 text-xs bg-gray-600 text-gray-200 rounded border border-gray-500 ml-1">Shift + Enter</kbd> para nueva línea • 
                🎤 Haz clic en el micrófono para grabar un mensaje de voz
              </>
            )}
          </p>
        </div>
      </form>
    </div>
  );
} 