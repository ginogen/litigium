import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useTextSelection } from '../../contexts/TextSelectionContext';
import { cn } from '@/utils';

export function FormattingToolbar() {
  const { state } = useTextSelection();
  const toolbarRef = useRef<HTMLDivElement>(null);
  const [toolbarPosition, setToolbarPosition] = useState({ x: 0, y: 0 });

  // Posicionar toolbar cerca de la selección
  const updateToolbarPosition = useCallback(() => {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) return;
    
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    
    let x = rect.left + (rect.width / 2) - 150; // Centrar toolbar
    let y = rect.top - 50; // Posicionar arriba de la selección
    
    // Ajustar si se sale de la pantalla
    if (x < 10) x = 10;
    if (x > window.innerWidth - 300) x = window.innerWidth - 300;
    if (y < 10) y = rect.bottom + 10;
    
    setToolbarPosition({ x, y });
  }, []);

  // Actualizar posición cuando hay selección activa
  useEffect(() => {
    if (state.isSelectionActive && toolbarRef.current) {
      updateToolbarPosition();
    }
  }, [state.isSelectionActive, updateToolbarPosition]);

  const applyFormat = useCallback((command: string, value?: string) => {
    try {
      document.execCommand(command, false, value);
      
      // Mantener la selección después del formato
      setTimeout(() => {
        const selection = window.getSelection();
        if (selection && selection.rangeCount > 0) {
          const selectedText = selection.toString();
          if (selectedText) {
            // Actualizar el store con el texto formateado
            const range = selection.getRangeAt(0);
            const container = range.commonAncestorContainer;
            const parentElement = container.nodeType === Node.TEXT_NODE 
              ? (container.parentElement as HTMLElement)
              : (container as HTMLElement);
            
            const context = {
              surroundingText: parentElement?.textContent || '',
              position: { start: range.startOffset, end: range.endOffset },
              elementType: parentElement?.tagName?.toLowerCase() || 'div'
            };
            
            // Aquí podrías actualizar el contexto si es necesario
          }
        }
      }, 100);
    } catch (error) {
      console.error('Error aplicando formato:', error);
    }
  }, []);

  const handleBold = useCallback(() => {
    applyFormat('bold');
  }, [applyFormat]);

  const handleItalic = useCallback(() => {
    applyFormat('italic');
  }, [applyFormat]);

  const handleUnderline = useCallback(() => {
    applyFormat('underline');
  }, [applyFormat]);

  const handleHighlight = useCallback(() => {
    applyFormat('backColor', '#fff3cd');
  }, [applyFormat]);

  const handleRemoveFormat = useCallback(() => {
    applyFormat('removeFormat');
  }, [applyFormat]);

  if (!state.isSelectionActive) {
    return null;
  }

  return (
    <div 
      ref={toolbarRef}
      className={cn(
        "fixed z-50 bg-card border border-border rounded-lg p-1.5",
        "shadow-lg backdrop-blur-sm pointer-events-auto",
        "animate-in fade-in-0 zoom-in-95 duration-200"
      )}
      style={{ 
        left: `${toolbarPosition.x}px`, 
        top: `${toolbarPosition.y}px`,
        transform: window.innerWidth <= 768 ? 'none' : undefined
      }}
    >
      <div className="flex items-center gap-1">
        <button 
          onClick={handleBold}
          className={cn(
            "w-7 h-7 rounded-md border border-transparent transition-all duration-200",
            "flex items-center justify-center text-sm font-bold",
            "hover:bg-background/80 hover:border-primary text-foreground",
            "active:scale-95"
          )}
          title="Negrita (Ctrl+B)"
        >
          B
        </button>
        
        <button 
          onClick={handleItalic}
          className={cn(
            "w-7 h-7 rounded-md border border-transparent transition-all duration-200",
            "flex items-center justify-center text-sm italic",
            "hover:bg-background/80 hover:border-primary text-foreground",
            "active:scale-95"
          )}
          title="Cursiva (Ctrl+I)"
        >
          I
        </button>
        
        <button 
          onClick={handleUnderline}
          className={cn(
            "w-7 h-7 rounded-md border border-transparent transition-all duration-200",
            "flex items-center justify-center text-sm underline",
            "hover:bg-background/80 hover:border-primary text-foreground",
            "active:scale-95"
          )}
          title="Subrayado (Ctrl+U)"
        >
          U
        </button>
        
        <div className="w-px h-4 bg-border mx-1" />
        
        <button 
          onClick={handleHighlight}
          className={cn(
            "w-7 h-7 rounded-md border border-transparent transition-all duration-200",
            "flex items-center justify-center text-sm",
            "hover:bg-purple-100/20 hover:border-purple-500/50 text-foreground",
            "active:scale-95"
          )}
          title="Resaltar texto"
        >
          🖍️
        </button>
        
        <button 
          onClick={handleRemoveFormat}
          className={cn(
            "w-7 h-7 rounded-md border border-transparent transition-all duration-200",
            "flex items-center justify-center text-sm",
            "hover:bg-red-500/20 hover:border-red-500/50 text-foreground",
            "active:scale-95"
          )}
          title="Quitar formato"
        >
          🗑️
        </button>
      </div>
      

    </div>
  );
} 