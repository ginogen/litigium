import React, { createContext, useContext, useState, ReactNode, useCallback } from 'react';

// Tipos
interface SelectionContext {
  surroundingText: string;
  position: {
    start: number;
    end: number;
  };
  elementType: string;
}

interface TextSelectionState {
  selectedText: string;
  selectionContext: SelectionContext | null;
  isSelectionActive: boolean;
}

interface TextSelectionContextType {
  state: TextSelectionState;
  setSelection: (text: string, context: SelectionContext) => void;
  clearSelection: () => void;
  getSelectionPrompt: (userInstruction: string) => string;
  hasActiveSelection: () => boolean;
}

const TextSelectionContext = createContext<TextSelectionContextType | undefined>(undefined);

// Provider
interface TextSelectionProviderProps {
  children: ReactNode;
}

export function TextSelectionProvider({ children }: TextSelectionProviderProps) {
  const [state, setState] = useState<TextSelectionState>({
    selectedText: '',
    selectionContext: null,
    isSelectionActive: false,
  });

  // Establecer selección
  const setSelection = useCallback((text: string, context: SelectionContext) => {
    setState({
      selectedText: text,
      selectionContext: context,
      isSelectionActive: true,
    });
  }, []);

  // Limpiar selección
  const clearSelection = useCallback(() => {
    setState({
      selectedText: '',
      selectionContext: null,
      isSelectionActive: false,
    });
  }, []);

  // Obtener prompt con selección
  const getSelectionPrompt = useCallback((userInstruction: string): string => {
    if (!state.isSelectionActive || !state.selectedText || !state.selectionContext) {
      return userInstruction;
    }

    const contextualPrompt = `
TEXTO SELECCIONADO: "${state.selectedText}"

CONTEXTO CIRCUNDANTE: "${state.selectionContext.surroundingText}"

ELEMENTO: ${state.selectionContext.elementType}

POSICIÓN: caracteres ${state.selectionContext.position.start}-${state.selectionContext.position.end}

INSTRUCCIÓN DEL USUARIO: ${userInstruction}

Por favor, procesa esta instrucción teniendo en cuenta el texto seleccionado y su contexto.
    `.trim();

    return contextualPrompt;
  }, [state]);

  // Verificar si hay selección activa
  const hasActiveSelection = useCallback((): boolean => {
    return state.isSelectionActive && !!state.selectedText;
  }, [state.isSelectionActive, state.selectedText]);

  const value: TextSelectionContextType = {
    state,
    setSelection,
    clearSelection,
    getSelectionPrompt,
    hasActiveSelection,
  };

  return (
    <TextSelectionContext.Provider value={value}>
      {children}
    </TextSelectionContext.Provider>
  );
}

// Hook personalizado
export function useTextSelection() {
  const context = useContext(TextSelectionContext);
  if (context === undefined) {
    throw new Error('useTextSelection must be used within a TextSelectionProvider');
  }
  return context;
} 