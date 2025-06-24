import React, { useState, useCallback } from 'react';
import { useCanvas } from '@/contexts/CanvasContext';
import { useChat } from '@/contexts/ChatContext';
import { Globe, Sparkles, ArrowRight, X, Check } from 'lucide-react';

interface GlobalEditPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function GlobalEditPanel({ isOpen, onClose }: GlobalEditPanelProps) {
  const { processEditCommand } = useCanvas();
  const { state: chatState } = useChat();
  
  const [instruction, setInstruction] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const handleSubmit = useCallback(async () => {
    if (!instruction.trim() || !chatState.sessionId || isProcessing) return;
    
    setIsProcessing(true);
    setResult(null);
    
    try {
      // Enviar comando de edición global
      const command = `GLOBAL: ${instruction.trim()}`;
      const response = await processEditCommand(command, chatState.sessionId);
      
      if (response.success) {
        setResult({ type: 'success', message: response.message || 'Modificación global aplicada exitosamente' });
        setInstruction('');
        
        // Auto-cerrar después de 2 segundos
        setTimeout(() => {
          onClose();
          setResult(null);
        }, 2000);
      } else {
        setResult({ type: 'error', message: response.error || 'Error aplicando modificación global' });
      }
    } catch (error) {
      setResult({ type: 'error', message: 'Error procesando la modificación global' });
    } finally {
      setIsProcessing(false);
    }
  }, [instruction, chatState.sessionId, isProcessing, processEditCommand, onClose]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSubmit();
    } else if (e.key === 'Escape') {
      onClose();
    }
  }, [handleSubmit, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <Globe className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Modificaciones Globales
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="mb-4">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Aplica cambios en <strong>todo el documento</strong> usando inteligencia artificial. 
              Perfecto para datos repetitivos como nombres, fechas, empresas, etc.
            </p>
            
            {/* Ejemplos */}
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 mb-4">
              <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
                💡 Ejemplos de modificaciones globales:
              </h4>
              <div className="space-y-1 text-sm text-blue-800 dark:text-blue-200">
                <div>• "cambiar Gino Gentile por Gino Gustavo Gentile"</div>
                <div>• "reemplazar ARCOR S.A. por MICROSOFT CORP"</div>
                <div>• "cambiar todas las fechas por 15/03/2024"</div>
                <div>• "la empresa es COCA-COLA FEMSA"</div>
                <div>• "agregar Gustavo al nombre"</div>
              </div>
            </div>
          </div>

          {/* Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Instrucción de modificación global:
            </label>
            <textarea
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ejemplo: cambiar Gino Gentile por Gino Gustavo Gentile"
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none"
              rows={3}
              disabled={isProcessing}
            />
            <div className="flex items-center justify-between mt-2">
              <p className="text-xs text-gray-500">
                Presiona Ctrl+Enter para aplicar • Esc para cerrar
              </p>
              <div className="text-xs text-gray-400">
                {instruction.length}/200
              </div>
            </div>
          </div>

          {/* Result */}
          {result && (
            <div className={`mb-4 p-3 rounded-lg ${
              result.type === 'success' 
                ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200' 
                : 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200'
            }`}>
              <div className="flex items-center gap-2">
                {result.type === 'success' ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <X className="w-4 h-4" />
                )}
                <span className="text-sm font-medium">{result.message}</span>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              disabled={isProcessing}
            >
              Cancelar
            </button>
            <button
              onClick={handleSubmit}
              disabled={!instruction.trim() || isProcessing}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isProcessing ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Procesando...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Aplicar Global
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
} 