import React, { useState, useRef, useCallback, useEffect } from 'react';
import { cn } from '../../lib/utils';

interface CommandPanelProps {
  commandInput: string;
  setCommandInput: (value: string) => void;
  executeCommand: () => void;
  isExecuting: boolean;
  handleKeydown: (event: React.KeyboardEvent) => void;
}

// Ejemplos de comandos en español
const commandExamples = [
  {
    category: '🔧 Edición Básica',
    commands: [
      'reemplazar en párrafo 3 "demandado" por "demandada"',
      'agregar al final del párrafo 5: "conforme al artículo 1902"',
      'eliminar la última oración del párrafo 2',
      'insertar después del párrafo 4: "Es importante destacar que..."'
    ]
  },
  {
    category: '📋 Hechos',
    commands: [
      'agregar hecho: "El 15 de marzo ocurrió el incidente"',
      'modificar párrafo 2 para incluir fecha exacta',
      'expandir párrafo de hechos con más detalles',
      'reorganizar hechos en orden cronológico'
    ]
  },
  {
    category: '⚖️ Derecho',
    commands: [
      'agregar fundamento legal al párrafo 8',
      'incluir jurisprudencia relevante después del párrafo 6',
      'modificar base legal en párrafo 4',
      'agregar referencia al código civil artículo 1382'
    ]
  },
  {
    category: '🎯 Petitorio',
    commands: [
      'agregar petición de daños morales',
      'incluir solicitud de costas procesales',
      'modificar monto de indemnización a €50,000',
      'agregar petición subsidiaria'
    ]
  }
];

export function CommandPanel({ 
  commandInput, 
  setCommandInput, 
  executeCommand, 
  isExecuting, 
  handleKeydown 
}: CommandPanelProps) {
  const [showExamples, setShowExamples] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const insertExample = useCallback((command: string) => {
    setCommandInput(command);
    setShowExamples(false);
    
    // Focus en el textarea después de insertar
    setTimeout(() => {
      if (textareaRef.current) {
        textareaRef.current.focus();
        textareaRef.current.setSelectionRange(command.length, command.length);
      }
    }, 100);
  }, [setCommandInput]);

  const toggleExamples = useCallback(() => {
    setShowExamples(!showExamples);
  }, [showExamples]);

  // Auto-resize del textarea
  const autoResize = useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const textarea = event.target;
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
    setCommandInput(textarea.value);
  }, [setCommandInput]);

  return (
    <div className="bg-card/30">
      {/* Header */}
      <div className="p-4 border-b border-border/50">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-foreground">⚡ Comandos</h3>
          <button 
            onClick={toggleExamples}
            className={cn(
              "px-3 py-1 text-xs rounded-md border transition-all duration-200",
              "bg-background/50 border-border/50 text-muted-foreground",
              "hover:bg-background/80 hover:border-border hover:text-foreground",
              showExamples && "bg-blue-500/20 border-blue-500/50 text-blue-400"
            )}
            title="Ver ejemplos de comandos"
          >
            💡 Ejemplos
          </button>
        </div>
        
        <div className="text-sm text-muted-foreground">
          Escribe comandos en español para editar párrafos
        </div>
      </div>
      
      {/* Input de comandos */}
      <div className="p-4">
        <div className="space-y-3">
          <textarea
            ref={textareaRef}
            value={commandInput}
            onChange={autoResize}
            onKeyDown={handleKeydown}
            placeholder="Ej: reemplazar en párrafo 3 'antiguo texto' por 'nuevo texto'"
            className={cn(
              "w-full bg-background/50 border border-border rounded-lg p-3",
              "text-sm text-foreground placeholder:text-muted-foreground",
              "resize-none min-h-[80px] max-h-[120px] overflow-y-auto",
              "focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50",
              "transition-all duration-200",
              isExecuting && "opacity-50 cursor-not-allowed"
            )}
            rows={2}
            disabled={isExecuting}
          />
          
          <button 
            onClick={executeCommand}
            disabled={!commandInput.trim() || isExecuting}
            className={cn(
              "w-full flex items-center justify-center gap-2 p-3 rounded-lg",
              "font-medium text-sm transition-all duration-200",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              !commandInput.trim() || isExecuting
                ? "bg-muted/20 text-muted-foreground"
                : "bg-blue-500 hover:bg-blue-600 text-white hover:-translate-y-0.5 shadow-lg"
            )}
            title="Ejecutar comando (Ctrl/Cmd + Enter)"
          >
            {isExecuting ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Procesando...
              </>
            ) : (
              <>
                ▶️ Ejecutar
              </>
            )}
          </button>
        </div>
        
        <div className="mt-2 text-xs text-muted-foreground text-center">
          💡 Presiona <kbd className="px-1 py-0.5 bg-background/50 rounded text-xs">Ctrl</kbd> + <kbd className="px-1 py-0.5 bg-background/50 rounded text-xs">Enter</kbd> para ejecutar
        </div>
      </div>
      
      {/* Panel de ejemplos */}
      {showExamples && (
        <div className="border-t border-border bg-background/20 transition-all duration-300 ease-in-out">
          <div className="p-4">
            <div className="mb-3">
              <h4 className="text-sm font-medium text-foreground mb-1">Ejemplos de Comandos</h4>
              <p className="text-xs text-muted-foreground">Haz clic en cualquier ejemplo para usarlo:</p>
            </div>
            
            <div className="space-y-4 max-h-80 overflow-y-auto">
              {commandExamples.map((category, categoryIndex) => (
                <div key={categoryIndex}>
                  <h5 className="text-sm font-medium text-foreground/80 mb-2">{category.category}</h5>
                  <div className="space-y-1">
                    {category.commands.map((command, commandIndex) => (
                      <button 
                        key={commandIndex}
                        onClick={() => insertExample(command)}
                        className={cn(
                          "w-full text-left p-2 text-xs rounded-md transition-all duration-200",
                          "bg-background/30 hover:bg-background/60 border border-border/30",
                          "hover:border-blue-500/50 hover:text-blue-400 text-foreground/80",
                          "line-clamp-2"
                        )}
                        title="Usar este comando"
                      >
                        {command}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 