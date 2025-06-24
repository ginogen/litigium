import React, { useState, useEffect, useRef, useCallback } from 'react';
import { cn } from '../../lib/utils';
import { categoryAPI } from '../../lib';
import { 
  X, 
  Download, 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  FileText,
  AlertCircle,
  Loader2,
  Eye,
  EyeOff,
  Edit3,
  MessageSquareIcon,
  ChevronRight,
  ChevronLeft,
  Plus,
  Settings
} from 'lucide-react';

interface Document {
  id: string;
  nombre_archivo: string;
  archivo_url: string;
  tipo_mime: string;
  tipo_demanda: string;
  estado_procesamiento: string;
}

interface Annotation {
  id: string;
  posicion_inicio: number;
  posicion_fin: number;
  contenido_seleccionado: string;
  contenido_anotacion: string;
  tipo: 'comentario' | 'precedente' | 'estrategia' | 'problema';
  etiquetas?: string[];
  prioridad?: number;
  created_at: string;
  author?: string;
  color?: string;
}

interface DocumentViewerProps {
  document: Document | null;
  annotations?: Annotation[];
  onClose: () => void;
  onAnnotationCreate?: (annotation: Partial<Annotation>) => void;
  onAnnotationSelect?: (annotation: Annotation) => void;
  showAnnotations?: boolean;
  isLoading?: boolean;
}

export function DocumentViewer({ 
  document, 
  annotations = [], 
  onClose, 
  onAnnotationCreate,
  onAnnotationSelect,
  showAnnotations = true,
  isLoading: externalLoading = false
}: DocumentViewerProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(100);
  const [selectedText, setSelectedText] = useState<string>('');
  const [selectionRange, setSelectionRange] = useState<{ start: number; end: number } | null>(null);
  const [showAnnotationForm, setShowAnnotationForm] = useState(false);
  const [showAnnotationPanel, setShowAnnotationPanel] = useState(true);
  const [showAnnotationHighlights, setShowAnnotationHighlights] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const documentRef = useRef<HTMLDivElement>(null);
  const [documentContent, setDocumentContent] = useState<string>('');
  const [formatType, setFormatType] = useState<'plain' | 'rich' | 'html'>('html');
  const [hasRichFormat, setHasRichFormat] = useState<boolean>(false);
  const [formatMetadata, setFormatMetadata] = useState<any>(null);
  const [newAnnotation, setNewAnnotation] = useState<{
    tipo: 'comentario' | 'precedente' | 'estrategia' | 'problema';
    contenido_anotacion: string;
    etiquetas: string[];
    prioridad: number;
  }>({
    tipo: 'comentario',
    contenido_anotacion: '',
    etiquetas: [],
    prioridad: 2
  });

  useEffect(() => {
    if (document) {
      loadDocument();
    }
  }, [document]);

  // Recargar cuando cambie el tipo de formato
  useEffect(() => {
    if (document && hasRichFormat) {
      loadDocument();
    }
  }, [formatType]);

  const loadDocument = async () => {
    if (!document) return;

    try {
      setIsLoading(true);
      setError(null);

      // Intentar cargar con formato rico primero, luego fallback a plano
      const targetFormat = hasRichFormat ? formatType : (formatType === 'html' ? 'html' : 'plain');
      const response = await categoryAPI.obtenerContenidoDocumento(document.id, targetFormat);
      
      if (response.success && response.document) {
        const doc = response.document;
        
        // Actualizar estado con información de formato
        setDocumentContent(doc.contenido);
        setHasRichFormat(doc.tiene_formato_rico || false);
        setFormatMetadata(doc.metadatos_formato || null);
        
        // Si es la primera vez cargando y tiene formato rico, usar HTML por defecto
        if (doc.tiene_formato_rico && formatType !== 'plain' && !hasRichFormat) {
          setFormatType('html');
        }
        
        // Mostrar información de formato en consola
        console.log('📄 Documento cargado con formato:', {
          formato: doc.format_type,
          tieneFormatoRico: doc.tiene_formato_rico,
          version: doc.version_extraccion,
          metadatos: doc.metadatos_formato
        });
        
      } else {
        if (response.error) {
          setError(response.error);
        } else if (response.estado_procesamiento === 'procesando') {
          setError('El documento aún se está procesando. Inténtalo en unos momentos.');
        } else if (response.estado_procesamiento === 'error') {
          setError('Error procesando el documento. El contenido no está disponible.');
        } else {
          setError('No se pudo cargar el contenido del documento.');
        }
        setDocumentContent('');
      }

    } catch (error) {
      console.error('Error loading document:', error);
      setError('Error cargando documento');
      setDocumentContent('');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTextSelection = useCallback(() => {
    const selection = window.getSelection();
    if (selection && selection.toString().trim() && selection.rangeCount > 0) {
      const selectedText = selection.toString().trim();
      const range = selection.getRangeAt(0);
      
      // Calcular posición aproximada en el texto
      const documentElement = documentRef.current;
      if (documentElement) {
        const preCaretRange = range.cloneRange();
        preCaretRange.selectNodeContents(documentElement);
        preCaretRange.setEnd(range.startContainer, range.startOffset);
        const start = preCaretRange.toString().length;
        const end = start + selectedText.length;
        
        setSelectedText(selectedText);
        setSelectionRange({ start, end });
        // Activar formulario en sidebar, no modal
        setShowAnnotationForm(true);
        // Asegurar que el sidebar esté visible y no colapsado
        setShowAnnotationPanel(true);
        setSidebarCollapsed(false);
      }
    }
  }, []);

  const handleAnnotationCreate = useCallback(() => {
    if (!selectionRange || !selectedText || !newAnnotation.contenido_anotacion.trim()) return;

    const annotation: Partial<Annotation> = {
      posicion_inicio: selectionRange.start,
      posicion_fin: selectionRange.end,
      contenido_seleccionado: selectedText,
      contenido_anotacion: newAnnotation.contenido_anotacion,
      tipo: newAnnotation.tipo,
      etiquetas: newAnnotation.etiquetas,
      prioridad: newAnnotation.prioridad,
      color: getTypeColor(newAnnotation.tipo)
    };

         onAnnotationCreate?.(annotation);
     
     // Reset form y limpiar selección
     setShowAnnotationForm(false);
     setSelectedText('');
     setSelectionRange(null);
     setNewAnnotation({
       tipo: 'comentario',
       contenido_anotacion: '',
       etiquetas: [],
       prioridad: 2
     });
     
     // Clear text selection
     window.getSelection()?.removeAllRanges();
  }, [selectionRange, selectedText, newAnnotation, onAnnotationCreate]);

  const renderDocumentContent = () => {
    if (!documentContent) return null;

    let content = documentContent;
    
    // Aplicar highlights de anotaciones
    if (showAnnotationHighlights && annotations.length > 0) {
      // Ordenar anotaciones por posición para aplicar highlights correctamente
      const sortedAnnotations = [...annotations].sort((a, b) => a.posicion_inicio - b.posicion_inicio);
      
      let offset = 0;
      sortedAnnotations.forEach((annotation) => {
        const start = annotation.posicion_inicio + offset;
        const end = annotation.posicion_fin + offset;
        const highlightClass = cn(
          "annotation-highlight cursor-pointer transition-all duration-200",
          getAnnotationClasses(annotation.tipo)
        );
        
        const before = content.substring(0, start);
        const highlighted = content.substring(start, end);
        const after = content.substring(end);
        
        const highlightedSpan = `<span class="${highlightClass}" data-annotation-id="${annotation.id}" title="${annotation.contenido_anotacion}">${highlighted}</span>`;
        
        content = before + highlightedSpan + after;
        offset += highlightedSpan.length - highlighted.length;
      });
    }

    return (
      <div 
        ref={documentRef}
        className="word-document-content"
        style={{ 
          fontSize: `${zoom}%`,
          lineHeight: '1.6',
          fontFamily: 'Times New Roman, serif'
        }}
        onMouseUp={handleTextSelection}
        dangerouslySetInnerHTML={{ 
          __html: content.replace(/\n/g, '<br/>').replace(/\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;')
        }}
      />
    );
  };

  const getTypeColor = (tipo: string) => {
    switch (tipo) {
      case 'comentario': return '#3b82f6';
      case 'precedente': return '#10b981';
      case 'estrategia': return '#f59e0b';
      case 'problema': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getAnnotationClasses = (tipo: string) => {
    switch (tipo) {
      case 'comentario':
        return 'bg-blue-100 border-l-2 border-blue-500 hover:bg-blue-200';
      case 'precedente':
        return 'bg-green-100 border-l-2 border-green-500 hover:bg-green-200';
      case 'estrategia':
        return 'bg-yellow-100 border-l-2 border-yellow-500 hover:bg-yellow-200';
      case 'problema':
        return 'bg-red-100 border-l-2 border-red-500 hover:bg-red-200';
      default:
        return 'bg-gray-100 border-l-2 border-gray-500 hover:bg-gray-200';
    }
  };

  const getTypeIcon = (tipo: string) => {
    switch (tipo) {
      case 'comentario': return '💬';
      case 'precedente': return '📚';
      case 'estrategia': return '🎯';
      case 'problema': return '⚠️';
      default: return '📝';
    }
  };

  const handleZoom = (direction: 'in' | 'out') => {
    setZoom(prev => {
      if (direction === 'in' && prev < 200) return prev + 10;
      if (direction === 'out' && prev > 50) return prev - 10;
      return prev;
    });
  };

  if (!document) return null;

  return (
    <div className="fixed inset-0 z-50 bg-gray-900/95 backdrop-blur-sm">
      <div className="flex h-full">
        {/* Panel principal del documento */}
        <div className={cn(
          "flex flex-col transition-all duration-300",
          showAnnotationPanel && !sidebarCollapsed ? "flex-1" : "w-full"
        )}>
          {/* Header */}
          <div className="flex items-center justify-between p-4 bg-white border-b border-gray-200 shadow-sm">
            <div className="flex items-center gap-3">
              <FileText className="w-5 h-5 text-blue-600" />
              <div>
                <h2 className="font-semibold text-gray-900">{document.nombre_archivo}</h2>
                <p className="text-sm text-gray-600">{document.tipo_demanda}</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Controles de zoom */}
              <button
                onClick={() => handleZoom('out')}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                title="Alejar"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              
              <span className="text-sm text-gray-600 min-w-[4rem] text-center font-mono">
                {zoom}%
              </span>
              
              <button
                onClick={() => handleZoom('in')}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                title="Acercar"
              >
                <ZoomIn className="w-4 h-4" />
              </button>

              <div className="w-px h-6 bg-gray-300 mx-2" />

              {/* NUEVO: Controles de formato rico */}
              {hasRichFormat && (
                <>
                  <div className="flex items-center gap-1 bg-blue-50 rounded-lg p-1">
                    <button
                      onClick={() => setFormatType('html')}
                      className={cn(
                        "px-2 py-1 text-xs rounded transition-colors",
                        formatType === 'html' 
                          ? "bg-blue-600 text-white" 
                          : "text-blue-600 hover:bg-blue-100"
                      )}
                      title="Vista HTML con formato"
                    >
                      🎨 Rico
                    </button>
                    <button
                      onClick={() => setFormatType('plain')}
                      className={cn(
                        "px-2 py-1 text-xs rounded transition-colors",
                        formatType === 'plain' 
                          ? "bg-blue-600 text-white" 
                          : "text-blue-600 hover:bg-blue-100"
                      )}
                      title="Vista texto plano"
                    >
                      📝 Plano
                    </button>
                  </div>
                  
                  <div className="w-px h-6 bg-gray-300 mx-1" />
                </>
              )}

              {/* Indicador de formato */}
              {formatMetadata && (
                <div className="flex items-center gap-1 text-xs text-gray-500">
                  <span className="bg-green-100 text-green-700 px-2 py-1 rounded">
                    {hasRichFormat ? '✅ Formato Rico' : '📄 Texto Plano'}
                  </span>
                  {formatMetadata.total_blocks && (
                    <span className="text-gray-400">
                      {formatMetadata.total_blocks} bloques
                    </span>
                  )}
                </div>
              )}

              <div className="w-px h-6 bg-gray-300 mx-2" />

              {/* Toggle anotaciones */}
              {showAnnotations && (
                <button
                  onClick={() => setShowAnnotationHighlights(!showAnnotationHighlights)}
                  className={cn(
                    "p-2 rounded-lg transition-colors",
                    showAnnotationHighlights
                      ? "text-blue-600 bg-blue-50"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                  )}
                  title={showAnnotationHighlights ? "Ocultar anotaciones" : "Mostrar anotaciones"}
                >
                  {showAnnotationHighlights ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                </button>
              )}

              {/* Toggle panel */}
              {showAnnotations && (
                <button
                  onClick={() => setShowAnnotationPanel(!showAnnotationPanel)}
                  className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                  title="Alternar panel de anotaciones"
                >
                  <MessageSquareIcon className="w-4 h-4" />
                </button>
              )}

              <div className="w-px h-6 bg-gray-300 mx-2" />

              {/* Descargar */}
              <button
                onClick={() => window.open(document.archivo_url, '_blank')}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                title="Descargar"
              >
                <Download className="w-4 h-4" />
              </button>

              {/* Cerrar */}
              <button
                onClick={onClose}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                title="Cerrar"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Contenido del documento */}
          <div className="flex-1 overflow-hidden">
            {isLoading ? (
              <div className="flex items-center justify-center h-full bg-white">
                <div className="text-center">
                  <Loader2 className="w-8 h-8 text-blue-600 mx-auto mb-2 animate-spin" />
                  <p className="text-gray-600">Cargando documento...</p>
                </div>
              </div>
            ) : error ? (
              <div className="flex items-center justify-center h-full bg-white">
                <div className="text-center">
                  <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
                  <p className="text-red-600 mb-4">{error}</p>
                  <button 
                    onClick={loadDocument}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm"
                  >
                    Reintentar
                  </button>
                </div>
              </div>
            ) : (
              <div className="h-full overflow-auto bg-white">
                {/* Estilo tipo Word */}
                <div className="max-w-4xl mx-auto">
                  <div className="bg-white shadow-lg min-h-full">
                    {/* Márgenes tipo Word */}
                                         <div className="p-16 pt-12 pb-12">
                       <style dangerouslySetInnerHTML={{
                         __html: `
                           .word-document-content {
                             color: #000000 !important;
                             font-size: 12pt;
                             line-height: 1.6;
                             text-align: justify;
                           }
                           .word-document-content h1, 
                           .word-document-content h2, 
                           .word-document-content h3 {
                             color: #000000 !important;
                             font-weight: bold;
                             margin: 1em 0 0.5em 0;
                           }
                           .word-document-content p {
                             margin: 0 0 1em 0;
                             text-indent: 0;
                           }
                           .annotation-highlight {
                             padding: 1px 2px;
                             border-radius: 2px;
                             margin: 0 1px;
                           }
                           .annotation-highlight:hover {
                             box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                           }
                         `
                       }} />
                       {renderDocumentContent()}
                     </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Panel lateral de anotaciones */}
                 {showAnnotationPanel && (
           <div className={cn(
             "bg-gradient-to-b from-gray-800 to-gray-900 border-l-2 border-gray-700 transition-all duration-300 flex flex-col shadow-lg h-full",
             sidebarCollapsed ? "w-12" : "w-80"
           )}>
             {/* Header del panel */}
             <div className="p-4 border-b border-gray-600">
               <div className="flex items-center justify-between">
                 {!sidebarCollapsed && (
                   <div className="flex items-center gap-2">
                     <h3 className="font-bold text-white flex items-center gap-2">
                       <MessageSquareIcon className="w-4 h-4" />
                       Anotaciones
                     </h3>
                     {!showAnnotationForm && (
                       <span className="text-xs text-gray-300 bg-gray-700 px-2 py-1 rounded-full border border-gray-600">
                         Selecciona texto
                       </span>
                     )}
                   </div>
                 )}
                 <button
                   onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                   className="p-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
                 >
                   {sidebarCollapsed ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                 </button>
               </div>
             </div>

            {!sidebarCollapsed && (
              <div className="flex-1 overflow-auto">
                {/* Formulario de nueva anotación en sidebar */}
                {showAnnotationForm && selectedText && (
                  <div className="p-4 border-b border-gray-600">
                    <div className="mb-4">
                      <h4 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                        <Edit3 className="w-4 h-4" />
                        Nueva Anotación
                      </h4>
                      <div className="text-xs text-gray-300 bg-gray-700/50 p-4 rounded-lg min-h-24 max-h-32 overflow-auto border border-gray-600">
                        <span className="font-medium text-white">Texto seleccionado:</span>
                        <br />
                        <span className="text-gray-200">"{selectedText}"</span>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      {/* Tipo de anotación */}
                      <div>
                        <label className="block text-xs font-medium text-gray-300 mb-1">
                          Tipo de anotación:
                        </label>
                        <select 
                          value={newAnnotation.tipo}
                          onChange={(e) => setNewAnnotation(prev => ({ 
                            ...prev, 
                            tipo: e.target.value as 'comentario' | 'precedente' | 'estrategia' | 'problema'
                          }))}
                          className="w-full p-3 text-sm bg-white border-2 border-gray-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 shadow-sm font-medium text-gray-700"
                        >
                          <option value="comentario">💬 Comentario</option>
                          <option value="precedente">📚 Precedente</option>
                          <option value="estrategia">🎯 Estrategia</option>
                          <option value="problema">⚠️ Problema</option>
                        </select>
                      </div>

                      {/* Contenido */}
                      <div>
                        <label className="block text-xs font-medium text-gray-300 mb-1">
                          Contenido de la anotación:
                        </label>
                        <textarea 
                          value={newAnnotation.contenido_anotacion}
                          onChange={(e) => setNewAnnotation(prev => ({ 
                            ...prev, 
                            contenido_anotacion: e.target.value 
                          }))}
                          className="w-full p-3 text-sm bg-white border-2 border-gray-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 shadow-sm text-gray-700 resize-none"
                          rows={6}
                          placeholder="Describe tu anotación aquí..."
                        />
                      </div>

                      {/* Prioridad */}
                      <div>
                        <label className="block text-xs font-medium text-gray-300 mb-1">
                          Prioridad:
                        </label>
                        <select 
                          value={newAnnotation.prioridad}
                          onChange={(e) => setNewAnnotation(prev => ({ 
                            ...prev, 
                            prioridad: parseInt(e.target.value) 
                          }))}
                          className="w-full p-3 text-sm bg-white border-2 border-gray-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 shadow-sm font-medium text-gray-700"
                        >
                          <option value={1}>🔴 Alta prioridad</option>
                          <option value={2}>🟡 Prioridad media</option>
                          <option value={3}>🟢 Baja prioridad</option>
                        </select>
                      </div>

                      {/* Botones */}
                      <div className="flex gap-2 pt-2">
                        <button
                          onClick={() => {
                            setShowAnnotationForm(false);
                            setSelectedText('');
                            setSelectionRange(null);
                            window.getSelection()?.removeAllRanges();
                            setNewAnnotation({
                              tipo: 'comentario',
                              contenido_anotacion: '',
                              etiquetas: [],
                              prioridad: 2
                            });
                          }}
                          className="flex-1 px-4 py-2.5 text-sm font-medium bg-gray-600 hover:bg-gray-700 text-white border border-gray-500 rounded-lg transition-colors"
                        >
                          Cancelar
                        </button>
                        <button
                          onClick={handleAnnotationCreate}
                          disabled={!newAnnotation.contenido_anotacion.trim()}
                          className="flex-1 px-4 py-2.5 text-sm font-medium bg-white hover:bg-gray-100 disabled:bg-gray-500 disabled:text-gray-400 text-gray-700 rounded-lg transition-colors shadow-sm"
                        >
                          Guardar
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Lista de anotaciones */}
                <div className="p-4">
                  {annotations.length === 0 && !showAnnotationForm ? (
                    <div className="text-center py-12">
                      <div className="bg-gray-700 rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                        <MessageSquareIcon className="w-8 h-8 text-gray-300" />
                      </div>
                      <h5 className="font-semibold text-gray-200 text-sm mb-1">Sin anotaciones</h5>
                      <p className="text-gray-400 text-xs">
                        Selecciona texto para crear tu primera anotación
                      </p>
                    </div>
                  ) : annotations.length > 0 ? (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="text-sm font-bold text-gray-200 flex items-center gap-2">
                          <span className="bg-gray-600 text-gray-200 px-2 py-1 rounded-full text-xs font-bold">
                            {annotations.length}
                          </span>
                          Anotaciones
                        </h4>
                      </div>
                      {annotations.map((annotation) => (
                        <div
                          key={annotation.id}
                          className="p-4 bg-gradient-to-r from-gray-700 to-gray-750 rounded-lg border-l-4 hover:shadow-md transition-all duration-200 cursor-pointer group"
                          style={{ borderLeftColor: getTypeColor(annotation.tipo) }}
                          onClick={() => onAnnotationSelect?.(annotation)}
                        >
                          <div className="flex items-start gap-3 mb-3">
                            <div 
                              className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white"
                              style={{ backgroundColor: getTypeColor(annotation.tipo) }}
                            >
                              {getTypeIcon(annotation.tipo)}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span 
                                  className="text-xs font-bold uppercase tracking-wider px-2 py-1 rounded-full text-white"
                                  style={{ backgroundColor: getTypeColor(annotation.tipo) }}
                                >
                                  {annotation.tipo}
                                </span>
                                {annotation.prioridad === 1 && (
                                  <span className="text-xs text-red-400 font-bold">¡ALTA!</span>
                                )}
                              </div>
                              <p className="text-xs text-gray-300 font-medium bg-gray-600 px-2 py-1 rounded border border-gray-500 line-clamp-2">
                                "{annotation.contenido_seleccionado}"
                              </p>
                            </div>
                          </div>
                          <p className="text-sm text-gray-200 line-clamp-3 leading-relaxed">
                            {annotation.contenido_anotacion}
                          </p>
                          {annotation.etiquetas && annotation.etiquetas.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-3">
                              {annotation.etiquetas.slice(0, 3).map((etiqueta, index) => (
                                <span
                                  key={index}
                                  className="px-2 py-1 bg-gray-600 text-gray-200 text-xs rounded-full border border-gray-500 font-medium"
                                >
                                  {etiqueta}
                                </span>
                              ))}
                            </div>
                          )}
                          <div className="opacity-0 group-hover:opacity-100 transition-opacity mt-2">
                            <span className="text-xs text-gray-400">Click para editar</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>
              </div>
            )}
          </div>
        )}
      </div>


    </div>
  );
} 