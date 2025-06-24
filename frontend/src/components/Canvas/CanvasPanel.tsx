import React, { useRef, useEffect, useCallback, useState } from 'react';
import { useCanvas } from '../../contexts/CanvasContext';
import { useChat } from '../../contexts/ChatContext';
import { cn } from '../../lib/utils';
import { ZoomIn, ZoomOut, FileText, Download, X, Plus, MessageSquare, CloudUpload, Globe } from 'lucide-react';
import { GoogleDriveFolderPicker } from './GoogleDriveFolderPicker';
import { GlobalEditPanel } from './GlobalEditPanel';
import { googleDriveAPI, textToBase64 } from '../../lib/google-drive-api';

export function CanvasPanel() {
  const { state, close, downloadDocument, loadCurrentDocument } = useCanvas();
  const { state: chatState } = useChat();
  
  const documentElementRef = useRef<HTMLDivElement>(null);
  const [isDocumentReady, setIsDocumentReady] = useState(false);
  const [zoom, setZoom] = useState(100);
  const [selectedText, setSelectedText] = useState<string>('');
  const [selectionRange, setSelectionRange] = useState<{ start: number; end: number } | null>(null);
  const [showSelectionNotice, setShowSelectionNotice] = useState(false);
  const [isProcessingEdit, setIsProcessingEdit] = useState(false);
  const [showInfoPanel, setShowInfoPanel] = useState(false);
  const [additionalInfo, setAdditionalInfo] = useState('');
  
  // Google Drive functionality
  const [showGoogleDrivePicker, setShowGoogleDrivePicker] = useState(false);
  const [isSavingToDrive, setIsSavingToDrive] = useState(false);
  const [driveConnectionStatus, setDriveConnectionStatus] = useState<{ connected: boolean; google_email?: string } | null>(null);
  
  // Global Edit functionality
  const [showGlobalEditPanel, setShowGlobalEditPanel] = useState(false);

  // Load document when initialized
  useEffect(() => {
    if (state.isOpen && chatState.sessionId && !state.currentDocument) {
      loadCurrentDocument(chatState.sessionId);
    }
  }, [state.isOpen, chatState.sessionId, state.currentDocument, loadCurrentDocument]);

  // Check Google Drive connection when Canvas opens
  useEffect(() => {
    if (state.isOpen) {
      checkGoogleDriveConnection();
    }
  }, [state.isOpen]);

  const checkGoogleDriveConnection = async () => {
    try {
      const status = await googleDriveAPI.getConnectionStatus();
      setDriveConnectionStatus(status);
    } catch (error) {
      console.error('Error checking Google Drive connection:', error);
      setDriveConnectionStatus({ connected: false });
    }
  };

  // Mark document as ready when content loads
  useEffect(() => {
    if (state.currentDocument && !isDocumentReady) {
      setIsDocumentReady(true);
    }
  }, [state.currentDocument, isDocumentReady]);

  const handleClose = useCallback(() => {
    close();
  }, [close]);

  const handleDownload = useCallback(async () => {
    if (chatState.sessionId) {
      await downloadDocument(chatState.sessionId);
    }
  }, [chatState.sessionId, downloadDocument]);

  const handleZoom = useCallback((direction: 'in' | 'out') => {
    setZoom(prev => {
      if (direction === 'in' && prev < 200) return prev + 10;
      if (direction === 'out' && prev > 50) return prev - 10;
      return prev;
    });
  }, []);

  // Manejo de selección de texto - solo logging, la UI se maneja en ChatInput
  const handleTextSelection = useCallback(() => {
    const selection = window.getSelection();
    if (selection && selection.toString().trim() && selection.rangeCount > 0) {
      const selectedText = selection.toString().trim();
      const range = selection.getRangeAt(0);
      
      // Calcular posición aproximada en el texto (para uso interno)
      const documentElement = documentElementRef.current;
      if (documentElement) {
        const preCaretRange = range.cloneRange();
        preCaretRange.selectNodeContents(documentElement);
        preCaretRange.setEnd(range.startContainer, range.startOffset);
        const start = preCaretRange.toString().length;
        const end = start + selectedText.length;
        
        // Solo logging, no mostrar notificación en Canvas
        setSelectedText(selectedText);
        setSelectionRange({ start, end });
        // setShowSelectionNotice(true); // Comentado para evitar doble notificación
        
        console.log('🎯 Texto seleccionado en Canvas:', selectedText.substring(0, 50) + '...');
      }
    } else {
      // Limpiar si no hay selección
      setSelectedText('');
      setSelectionRange(null);
      setShowSelectionNotice(false);
    }
  }, []);

  // Agregar información adicional
  const handleAddInfo = useCallback(async () => {
    if (!additionalInfo.trim() || !chatState.sessionId || isProcessingEdit) return;
    
    setIsProcessingEdit(true);
    
    try {
      const { editorAPI } = await import('../../lib/api');
      
      const command = `Agregar la siguiente información adicional al documento: ${additionalInfo}`;
      const result = await editorAPI.procesarEdicion(command, chatState.sessionId);
      
      if (result.success) {
        await loadCurrentDocument(chatState.sessionId);
        setShowInfoPanel(false);
        setAdditionalInfo('');
      } else {
        alert('Error agregando información: ' + (result.error || 'Error desconocido'));
      }
    } catch (error) {
      console.error('Error agregando información:', error);
      alert('Error agregando información');
    } finally {
      setIsProcessingEdit(false);
    }
  }, [additionalInfo, chatState.sessionId, isProcessingEdit, loadCurrentDocument]);

  // Guardar en Google Drive
  const handleSaveToGoogleDrive = useCallback(async (folderId: string | null, folderName: string) => {
    if (!state.currentDocument || !chatState.sessionId) return;
    
    setIsSavingToDrive(true);
    
    try {
      // Generar nombre del archivo basado en la sesión
      const fileName = `Demanda_${new Date().toLocaleDateString('es-ES').replace(/\//g, '-')}_${Date.now()}.docx`;
      
      // Convertir el contenido del documento a base64
      const documentContent = state.currentDocument;
      const base64Content = textToBase64(documentContent);
      
      // Guardar en Google Drive
      const result = await googleDriveAPI.saveFile({
        file_name: fileName,
        file_content: base64Content,
        folder_id: folderId || undefined,
        mime_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      });
      
      if (result.success) {
        alert(`✅ Demanda guardada exitosamente en Google Drive!\n\nArchivo: ${result.file_name}\nCarpeta: ${folderName}\n\n${result.web_view_link ? 'Puedes verla en: ' + result.web_view_link : ''}`);
      } else {
        alert('❌ Error guardando la demanda en Google Drive');
      }
      
    } catch (error: any) {
      console.error('Error saving to Google Drive:', error);
      
      // Mostrar mensaje de error más específico
      let errorMessage = 'Error guardando en Google Drive';
      if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error?.message) {
        errorMessage = error.message;
      }
      
      alert(`❌ ${errorMessage}`);
    } finally {
      setIsSavingToDrive(false);
      setShowGoogleDrivePicker(false);
    }
  }, [state.currentDocument, chatState.sessionId]);

  // Limpiar selección
  const clearSelection = useCallback(() => {
    setSelectedText('');
    setSelectionRange(null);
    setShowSelectionNotice(false);
    window.getSelection()?.removeAllRanges();
  }, []);

  // Renderizar contenido del documento con formato enriquecido
  const renderDocumentContent = useCallback(() => {
    if (!state.currentDocument) return null;

    const content = state.currentDocument;
    
    return (
      <div 
        ref={documentElementRef}
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
  }, [state.currentDocument, zoom, handleTextSelection]);

  if (!state.isOpen) return null;

  return (
    <div className="w-1/2 h-full bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col">
      {/* Header simplificado */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-blue-600" />
          <div>
            <h2 className="text-lg font-semibold">Demanda Generada</h2>
            <p className="text-sm text-gray-600">
              Selecciona texto y escribe en el chat para modificar
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Controles de zoom */}
          <button
            onClick={() => handleZoom('out')}
            className="p-2 text-gray-800 hover:text-gray-900 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-lg transition-colors"
            title="Alejar"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          
          <span className="text-sm text-gray-800 font-semibold min-w-[4rem] text-center font-mono bg-gray-50 px-2 py-1 rounded border">
            {zoom}%
          </span>
          
          <button
            onClick={() => handleZoom('in')}
            className="p-2 text-gray-800 hover:text-gray-900 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-lg transition-colors"
            title="Acercar"
          >
            <ZoomIn className="w-4 h-4" />
          </button>

          <div className="w-px h-6 bg-gray-400 mx-2" />

          {/* Modificaciones Globales */}
          <button
            onClick={() => setShowGlobalEditPanel(true)}
            className="p-2 text-white bg-purple-600 hover:bg-purple-700 border border-purple-600 rounded-lg transition-colors"
            title="Modificaciones Globales con IA"
          >
            <Globe className="w-4 h-4" />
          </button>

          {/* Agregar información */}
          <button
            onClick={() => setShowInfoPanel(!showInfoPanel)}
            className={cn(
              "p-2 rounded-lg transition-colors border",
              showInfoPanel 
                ? "bg-green-100 text-green-800 border-green-300"
                : "text-gray-800 bg-gray-100 hover:bg-gray-200 border-gray-300"
            )}
            title="Agregar más información"
          >
            <Plus className="w-4 h-4" />
          </button>

          {/* Guardar en Google Drive */}
          {driveConnectionStatus?.connected && (
            <button
              onClick={() => setShowGoogleDrivePicker(true)}
              disabled={!state.currentDocument || isSavingToDrive}
              className={cn(
                "p-2 rounded-lg transition-colors border",
                isSavingToDrive
                  ? "bg-blue-100 text-blue-600 border-blue-300 cursor-not-allowed"
                  : "text-gray-800 bg-gray-100 hover:bg-blue-100 border-gray-300 hover:border-blue-300"
              )}
              title={`Guardar en Google Drive (${driveConnectionStatus.google_email})`}
            >
              {isSavingToDrive ? (
                <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
              ) : (
                <CloudUpload className="w-4 h-4" />
              )}
            </button>
          )}

          <div className="w-px h-6 bg-gray-400 mx-2" />
          
          <button
            onClick={handleDownload}
            className="p-2 text-gray-800 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-lg transition-colors"
            title="Descargar documento"
          >
            <Download className="w-4 h-4" />
          </button>
          
          <button
            onClick={handleClose}
            className="p-2 text-gray-800 bg-gray-100 hover:bg-red-100 hover:text-red-600 border border-gray-300 hover:border-red-300 rounded-lg transition-colors"
            title="Cerrar"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Panel de información adicional */}
      {showInfoPanel && (
        <div className="p-4 bg-green-50 border-b border-green-200">
          <div className="mb-3">
            <h4 className="text-sm font-semibold text-green-800 mb-1 flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Agregar Información al Documento
            </h4>
            <p className="text-xs text-green-600">Describe qué información adicional necesita el documento</p>
          </div>
          
          <div className="space-y-3">
            <textarea
              value={additionalInfo}
              onChange={(e) => setAdditionalInfo(e.target.value)}
              placeholder="Ej: Agregar más detalles sobre los hechos del día 15 de marzo, incluir referencia al artículo 245 LCT, agregar jurisprudencia relevante..."
              className="w-full p-3 text-sm border border-green-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 resize-none"
              rows={4}
            />
            
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setShowInfoPanel(false);
                  setAdditionalInfo('');
                }}
                className="flex-1 px-3 py-2 text-sm border border-green-300 text-green-700 rounded-lg hover:bg-green-100 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleAddInfo}
                disabled={!additionalInfo.trim() || isProcessingEdit}
                className="flex-1 px-3 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                {isProcessingEdit ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Procesando...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4" />
                    Agregar Información
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Notificación de texto seleccionado */}
      {showSelectionNotice && selectedText && (
        <div className="p-3 bg-blue-50 border-b border-blue-200 animate-in slide-in-from-top-2">
          <div className="flex items-start gap-3">
            <MessageSquare className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-semibold text-blue-800">Texto Seleccionado</h4>
                <button
                  onClick={clearSelection}
                  className="text-blue-600 hover:text-blue-800 p-1"
                  title="Limpiar selección"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              
              {/* Texto seleccionado compacto */}
              <div className="bg-white border border-blue-200 rounded p-2 mb-2">
                <div className="text-xs text-blue-600 font-medium mb-1">TEXTO SELECCIONADO:</div>
                <div className="text-sm text-gray-800 italic leading-relaxed max-h-16 overflow-auto">
                  "{selectedText}"
                </div>
              </div>
              
              {/* Instrucción */}
              <div className="flex items-center gap-2 text-xs text-blue-700">
                <MessageSquare className="w-3 h-3" />
                <span className="font-medium">Escribe en el chat cómo quieres modificar este texto</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Contenido del documento con formato tipo Word */}
      <div className="flex-1 overflow-auto bg-gray-50">
        {state.currentDocument ? (
          <div className="max-w-4xl mx-auto py-8">
            <div className="bg-white shadow-lg min-h-full">
              {/* Márgenes tipo Word */}
              <div className="p-16 pt-12 pb-12">
                <style dangerouslySetInnerHTML={{
                  __html: `
                    .word-document-content {
                      color: #000000 !important;
                      font-size: 12pt;
                      line-height: 1.8;
                      text-align: justify;
                      cursor: text;
                    }
                    .word-document-content h1, 
                    .word-document-content h2, 
                    .word-document-content h3 {
                      color: #000000 !important;
                      font-weight: bold;
                      margin: 1.5em 0 1em 0;
                      text-align: center;
                      line-height: 1.4;
                    }
                    .word-document-content p {
                      margin: 0 0 1.2em 0;
                      text-indent: 1.5em;
                    }
                    .word-document-content ::selection {
                      background-color: #dbeafe;
                      color: #1e40af;
                    }
                    .word-document-content::-moz-selection {
                      background-color: #dbeafe;
                      color: #1e40af;
                    }
                    .word-document-content:hover {
                      background-color: #f8fafc;
                    }
                  `
                }} />
                {renderDocumentContent()}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-500">
              {state.isLoading ? (
                <div className="flex flex-col items-center gap-4">
                  <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                  <div className="text-lg">Cargando documento...</div>
                  <div className="text-sm text-gray-400">Preparando la demanda generada</div>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-4">
                  <FileText className="w-16 h-16 text-gray-400" />
                  <div className="text-lg">No hay documento disponible</div>
                  <div className="text-sm text-gray-400">Genera una demanda desde el chat para verla aquí</div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Google Drive Folder Picker Modal */}
      <GoogleDriveFolderPicker
        isOpen={showGoogleDrivePicker}
        onClose={() => setShowGoogleDrivePicker(false)}
        onFolderSelect={handleSaveToGoogleDrive}
        title="Guardar Demanda en Google Drive"
      />

      {/* Global Edit Panel Modal */}
      <GlobalEditPanel 
        isOpen={showGlobalEditPanel} 
        onClose={() => setShowGlobalEditPanel(false)} 
      />
    </div>
  );
} 