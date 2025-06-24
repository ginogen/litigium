import React from 'react';
import { cn } from '@/lib/utils';
import { 
  X, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  FileText,
  Download,
  RefreshCw
} from 'lucide-react';

interface ImportResult {
  success: boolean;
  message: string;
  file_name: string;
  file_id: string;
  needs_conversion: boolean;
}

interface ImportResultsModalProps {
  isOpen: boolean;
  onClose: () => void;
  results: ImportResult[];
  onRetry?: (failedFiles: ImportResult[]) => void;
}

export function ImportResultsModal({ 
  isOpen, 
  onClose, 
  results, 
  onRetry 
}: ImportResultsModalProps) {
  if (!isOpen) return null;

  const successful = results.filter(r => r.success);
  const failed = results.filter(r => !r.success);

  // Categorizar errores por tipo
  const errorCategories = {
    conversion: failed.filter(f => f.message.includes('Export only supports')),
    permission: failed.filter(f => f.message.includes('permission') || f.message.includes('403')),
    notFound: failed.filter(f => f.message.includes('not found') || f.message.includes('404')),
    processing: failed.filter(f => f.message.includes('processing') || f.message.includes('extract')),
    other: failed.filter(f => 
      !f.message.includes('Export only supports') &&
      !f.message.includes('permission') &&
      !f.message.includes('403') &&
      !f.message.includes('not found') &&
      !f.message.includes('404') &&
      !f.message.includes('processing') &&
      !f.message.includes('extract')
    )
  };

  const getErrorIcon = (message: string) => {
    if (message.includes('Export only supports')) return '🔄';
    if (message.includes('permission') || message.includes('403')) return '🔒';
    if (message.includes('not found') || message.includes('404')) return '❓';
    if (message.includes('processing') || message.includes('extract')) return '⚙️';
    return '❌';
  };

  const getErrorCategory = (message: string) => {
    if (message.includes('Export only supports')) return 'Error de conversión';
    if (message.includes('permission') || message.includes('403')) return 'Error de permisos';
    if (message.includes('not found') || message.includes('404')) return 'Archivo no encontrado';
    if (message.includes('processing') || message.includes('extract')) return 'Error de procesamiento';
    return 'Error desconocido';
  };

  const getSolution = (message: string) => {
    if (message.includes('Export only supports')) {
      return 'Intenta descargar el archivo manualmente y subirlo como .docx';
    }
    if (message.includes('permission') || message.includes('403')) {
      return 'Verifica que tengas permisos para acceder al archivo';
    }
    if (message.includes('not found') || message.includes('404')) {
      return 'El archivo puede haber sido movido o eliminado';
    }
    if (message.includes('processing') || message.includes('extract')) {
      return 'El archivo puede estar corrupto o en un formato no compatible';
    }
    return 'Intenta nuevamente o contacta soporte';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Resultados de Importación
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {successful.length} exitosos, {failed.length} fallidos de {results.length} archivos
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(80vh-140px)]">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {/* Success Card */}
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
              <div className="flex items-center space-x-3">
                <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
                <div>
                  <h3 className="font-medium text-green-900 dark:text-green-100">
                    {successful.length} Archivos Procesados
                  </h3>
                  <p className="text-sm text-green-700 dark:text-green-300">
                    Importados exitosamente
                  </p>
                </div>
              </div>
            </div>

            {/* Error Card */}
            {failed.length > 0 && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <XCircle className="w-8 h-8 text-red-600 dark:text-red-400" />
                  <div>
                    <h3 className="font-medium text-red-900 dark:text-red-100">
                      {failed.length} Archivos Fallaron
                    </h3>
                    <p className="text-sm text-red-700 dark:text-red-300">
                      Requieren atención
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Successful Files */}
          {successful.length > 0 && (
            <div className="mb-6">
              <h3 className="flex items-center space-x-2 text-lg font-medium text-gray-900 dark:text-gray-100 mb-3">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span>Archivos Procesados Exitosamente</span>
              </h3>
              <div className="space-y-2">
                {successful.map((result, index) => (
                  <div 
                    key={`success-${index}`}
                    className="flex items-center space-x-3 p-3 bg-green-50 dark:bg-green-900/10 rounded-lg"
                  >
                    <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400 flex-shrink-0" />
                    <FileText className="w-4 h-4 text-gray-600 dark:text-gray-400 flex-shrink-0" />
                    <span className="text-sm text-gray-900 dark:text-gray-100 truncate">
                      {result.file_name}
                    </span>
                    <span className="text-xs text-green-700 dark:text-green-300 bg-green-100 dark:bg-green-900/30 px-2 py-1 rounded">
                      ✓ Procesado
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Failed Files with Details */}
          {failed.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="flex items-center space-x-2 text-lg font-medium text-gray-900 dark:text-gray-100">
                  <XCircle className="w-5 h-5 text-red-600" />
                  <span>Archivos que Fallaron</span>
                </h3>
                {onRetry && (
                  <button
                    onClick={() => onRetry(failed)}
                    className="flex items-center space-x-2 px-3 py-1 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800"
                  >
                    <RefreshCw className="w-4 h-4" />
                    <span>Reintentar fallidos</span>
                  </button>
                )}
              </div>
              
              <div className="space-y-3">
                {failed.map((result, index) => (
                  <div 
                    key={`failed-${index}`}
                    className="border border-red-200 dark:border-red-800 rounded-lg p-4 bg-red-50 dark:bg-red-900/10"
                  >
                    <div className="flex items-start space-x-3">
                      <span className="text-lg flex-shrink-0 mt-0.5">
                        {getErrorIcon(result.message)}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-2">
                          <FileText className="w-4 h-4 text-gray-600 dark:text-gray-400 flex-shrink-0" />
                          <span className="font-medium text-gray-900 dark:text-gray-100 truncate">
                            {result.file_name}
                          </span>
                          <span className="text-xs text-red-700 dark:text-red-300 bg-red-100 dark:bg-red-900/30 px-2 py-1 rounded">
                            {getErrorCategory(result.message)}
                          </span>
                        </div>
                        
                        <div className="space-y-2">
                          <div className="bg-white dark:bg-gray-800 rounded p-3 border">
                            <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                              <strong>Error:</strong> {result.message}
                            </p>
                            <p className="text-sm text-blue-700 dark:text-blue-300">
                              <strong>Solución sugerida:</strong> {getSolution(result.message)}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end space-x-3 p-6 border-t border-gray-200 dark:border-gray-700">
          {failed.length > 0 && (
            <button
              onClick={() => {
                const errorSummary = failed.map(f => `${f.file_name}: ${f.message}`).join('\n');
                navigator.clipboard.writeText(errorSummary);
              }}
              className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg border border-gray-300 dark:border-gray-600"
            >
              Copiar errores
            </button>
          )}
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
} 