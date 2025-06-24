import React, { useEffect, useState, useCallback } from 'react';
import { useCanvas } from '@/contexts/CanvasContext';
import { useChat } from '@/contexts/ChatContext';
import { ParagraphItem } from './ParagraphItem';
import { CommandPanel } from './CommandPanel';
import { EditHistory } from './EditHistory';
import { cn } from '@/lib/utils';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export function ParagraphEditor() {
  const { state, initializeEditor, processEditCommand, loadEditHistory } = useCanvas();
  const { state: chatState } = useChat();
  
  const [commandInput, setCommandInput] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [lastResult, setLastResult] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true); // Colapsada por defecto

  // Inicializar editor al montar
  useEffect(() => {
    if (chatState.sessionId && !state.isEditorInitialized) {
      initializeEditor(chatState.sessionId);
    }
  }, [chatState.sessionId, state.isEditorInitialized, initializeEditor]);

  // Ejecutar comando de edición
  const executeCommand = useCallback(async () => {
    if (!commandInput.trim() || isExecuting || !chatState.sessionId) return;
    
    setIsExecuting(true);
    const command = commandInput.trim();
    
    try {
      const result = await processEditCommand(command, chatState.sessionId);
      
      if (result.success) {
        setLastResult({ type: 'success', message: result.message || 'Comando ejecutado correctamente' });
        setCommandInput('');
        
        // Auto-limpiar resultado después de 3 segundos
        setTimeout(() => {
          setLastResult(null);
        }, 3000);
      } else {
        setLastResult({ type: 'error', message: result.error || 'Error ejecutando comando' });
        
        // Auto-limpiar error después de 5 segundos
        setTimeout(() => {
          setLastResult(null);
        }, 5000);
      }
    } catch (error) {
      setLastResult({ type: 'error', message: 'Error procesando comando' });
      setTimeout(() => {
        setLastResult(null);
      }, 5000);
    } finally {
      setIsExecuting(false);
    }
  }, [commandInput, isExecuting, chatState.sessionId, processEditCommand]);

  // Manejar teclas especiales
  const handleKeydown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      executeCommand();
    }
  }, [executeCommand]);

  // Stats derivados
  const totalParagraphs = state.paragraphs.length;
  const modifiedParagraphs = state.paragraphs.filter(p => p.modificado).length;
  const totalEdits = state.editHistory.length;

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header con estadísticas */}
      <div className="p-4 border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center gap-6 mb-2">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Párrafos:</span>
            <span className="text-sm font-semibold text-foreground">{totalParagraphs}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Modificados:</span>
            <span className="text-sm font-semibold text-purple-400">{modifiedParagraphs}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Ediciones:</span>
            <span className="text-sm font-semibold text-foreground">{totalEdits}</span>
          </div>
        </div>
        
        {lastResult && (
          <div className={cn(
            "p-2 rounded-lg text-sm font-medium transition-all duration-300",
            "animate-in slide-in-from-top-2",
            lastResult.type === 'success' 
              ? "bg-green-500/15 text-green-400 border border-green-500/30"
              : "bg-red-500/15 text-red-400 border border-red-500/30"
          )}>
            {lastResult.type === 'success' ? '✅' : '❌'} {lastResult.message}
          </div>
        )}
      </div>

      {/* Layout principal del editor */}
      <div className="flex flex-1 min-h-0">
        {/* Panel izquierdo: Párrafos */}
        <div className="flex-1 flex flex-col border-r border-border min-w-0">
          <div className="p-4 border-b border-border">
            <h3 className="text-lg font-semibold text-foreground mb-1">📄 Documento</h3>
            <div className="text-sm text-muted-foreground">
              {totalParagraphs} párrafos • {modifiedParagraphs} modificados
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto p-2">
            {state.paragraphs.length > 0 ? (
              <div className="space-y-2">
                {state.paragraphs.map((paragraph) => (
                  <ParagraphItem key={paragraph.numero} paragraph={paragraph} />
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center py-16">
                <div className="text-6xl mb-4 opacity-70">📝</div>
                <h4 className="text-lg font-medium text-foreground mb-2">Sin párrafos</h4>
                <p className="text-sm text-muted-foreground max-w-sm">
                  {state.isLoading 
                    ? "Cargando párrafos del documento..."
                    : "Inicializa el editor para ver los párrafos del documento"
                  }
                </p>
                {state.isLoading && (
                  <div className="mt-4 w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                )}
              </div>
            )}
          </div>
        </div>

        {/* Panel derecho: Comandos e Historial */}
        <div className={cn(
          "flex flex-col bg-card/50 border-l border-border transition-all duration-300",
          sidebarCollapsed ? "w-12" : "w-80"
        )}>
          {/* Header con botón de toggle */}
          <div className="p-3 border-b border-border flex items-center justify-between">
            {!sidebarCollapsed && (
              <h3 className="text-sm font-semibold text-foreground">⚡ Editor</h3>
            )}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-2 text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg transition-colors"
              title={sidebarCollapsed ? "Expandir panel" : "Contraer panel"}
            >
              {sidebarCollapsed ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </button>
          </div>

          {!sidebarCollapsed && (
            <>
              {/* Panel de comandos */}
              <div className="border-b border-border">
                <CommandPanel 
                  commandInput={commandInput}
                  setCommandInput={setCommandInput}
                  executeCommand={executeCommand}
                  isExecuting={isExecuting}
                  handleKeydown={handleKeydown}
                />
              </div>

              {/* Historial de ediciones */}
              <div className="flex-1 min-h-0">
                <EditHistory history={state.editHistory} />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
} 