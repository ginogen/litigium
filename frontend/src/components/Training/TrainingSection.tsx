import React, { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { categoryAPI, Category, annotationAPI, templateAPI, enhancedAnalysisAPI } from '@/lib/index.ts';
import { googleDriveAPI } from '@/lib/google-drive-api';
import { Annotation, AnnotationTemplate, Document } from '../../types/annotation';
import { cn } from '@/lib/utils';
import { Upload, FileText, CheckCircle, XCircle, Clock, Loader2, Search, Settings, Folder, FolderPlus, Filter, BookOpen, MessageSquare, Brain, Cloud, X } from 'lucide-react';
import { CategoryManager } from './CategoryManager';
import { DocumentLibrary } from './DocumentLibrary';
import { DocumentViewer } from './DocumentViewer';
import { AnnotationPanel } from './AnnotationPanel';
import { AnnotationForm } from './AnnotationForm';
import { AnnotationTemplates } from './AnnotationTemplates';
import { GoogleDriveConnector } from './GoogleDriveConnector';
import { GoogleDriveExplorer } from './GoogleDriveExplorer';
import { ImportResultsModal } from './ImportResultsModal';

interface UploadZoneProps {
  onFileUpload: (files: File[], categoriaId: string, tipoDemanda: string) => void;
  isUploading: boolean;
  categories: Category[];
  selectedCategoryId: string;
  onCategoryChange: (categoryId: string) => void;
}

const UploadZone: React.FC<UploadZoneProps> = ({ 
  onFileUpload, 
  isUploading, 
  categories, 
  selectedCategoryId, 
  onCategoryChange 
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [tipoDemanda, setTipoDemanda] = useState('');

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0] && selectedCategoryId && tipoDemanda.trim()) {
      const files = Array.from(e.dataTransfer.files).filter(file => 
        file.type === 'application/pdf' || 
        file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
        file.type === 'application/msword'
      );
      
      if (files.length > 0) {
        onFileUpload(files, selectedCategoryId, tipoDemanda.trim());
        setTipoDemanda(''); // Limpiar después de subir
      }
    }
  }, [selectedCategoryId, tipoDemanda, onFileUpload]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && selectedCategoryId && tipoDemanda.trim()) {
      const files = Array.from(e.target.files);
      onFileUpload(files, selectedCategoryId, tipoDemanda.trim());
      setTipoDemanda(''); // Limpiar después de subir
      // Reset the input
      e.target.value = '';
    }
  }, [selectedCategoryId, tipoDemanda, onFileUpload]);

  const canUpload = selectedCategoryId && tipoDemanda.trim() && !isUploading;

  return (
    <div className="space-y-4">
      {/* Zona de subida principal */}
      <label
        className={cn(
          "relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 block cursor-pointer",
          dragActive && canUpload
            ? "border-blue-500 bg-blue-500/10"
            : "border-gray-600 hover:border-gray-500",
          !canUpload && "opacity-50 cursor-not-allowed"
        )}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          multiple
          accept=".pdf,.docx,.doc"
          onChange={handleFileSelect}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={!canUpload}
        />
        
        <div className="space-y-4">
          {isUploading ? (
            <>
              <Loader2 className="w-12 h-12 text-blue-400 mx-auto animate-spin" />
              <p className="text-lg font-medium text-gray-100">Subiendo y procesando...</p>
              <p className="text-sm text-gray-400">
                Los documentos se procesan automáticamente con tu colección personal
              </p>
            </>
          ) : (
            <>
              <Upload className="w-12 h-12 text-gray-400 mx-auto" />
              <div>
                <p className="text-lg font-medium text-gray-100 mb-1">
                  {canUpload ? 'Arrastra archivos aquí o haz clic para seleccionar' : 'Configura primero la categoría y tipo de demanda arriba'}
                </p>
                <p className="text-sm text-gray-400">
                  Formatos soportados: PDF, DOC, DOCX (máx. 10MB)
                </p>
              </div>
            </>
          )}
        </div>
        
        {!canUpload && (
          <div className="absolute inset-0 bg-gray-900/30 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <p className="text-gray-300 font-medium">Completa la configuración arriba primero</p>
            </div>
          </div>
        )}
      </label>
      
      {canUpload && (
        <div className="text-center">
          <p className="text-sm text-gray-400">
            Usando: <span className="text-gray-200 font-medium">{categories.find(c => c.id === selectedCategoryId)?.nombre}</span> • <span className="text-gray-200 font-medium">{tipoDemanda}</span>
          </p>
        </div>
      )}
    </div>
  );
};

export function TrainingSection() {
  // Estados principales
  const [activeTab, setActiveTab] = useState<'upload' | 'categories' | 'documents' | 'templates'>('upload');
  const [isGoogleDriveConnected, setIsGoogleDriveConnected] = useState(false);
  const [showGoogleDriveModal, setShowGoogleDriveModal] = useState(false);
  const [selectedCategoryId, setSelectedCategoryId] = useState('');
  const [tipoDemanda, setTipoDemanda] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [showLocalUpload, setShowLocalUpload] = useState(false);

  // Estados para el sistema de anotaciones
  const [selectedDocument, setSelectedDocument] = useState<any>(null);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [selectedAnnotation, setSelectedAnnotation] = useState<Annotation | null>(null);
  const [showAnnotationForm, setShowAnnotationForm] = useState(false);
  const [editingAnnotation, setEditingAnnotation] = useState<Annotation | null>(null);
  const [showAnnotationPanel, setShowAnnotationPanel] = useState(true);
  const [isLoadingAnnotations, setIsLoadingAnnotations] = useState(false);
  
  // Estado para el modal de resultados de importación
  const [showImportResults, setShowImportResults] = useState(false);
  const [importResults, setImportResults] = useState<any[]>([]);

  const queryClient = useQueryClient();

  // ===== TANSTACK QUERY HOOKS SIMPLIFICADOS =====
  
  // Query para categorías
  const categoriesQuery = useQuery({
    queryKey: ['categories'],
    queryFn: async () => {
      console.time('loadCategories');
      const response = await categoryAPI.obtenerCategorias();
      console.timeEnd('loadCategories');
      
      if (!response.success) {
        throw new Error('Error obteniendo categorías del servidor');
      }
      return response;
    },
    staleTime: 5 * 60 * 1000, // 5 minutos
    retry: 2,
    retryDelay: 2000,
  });

  // Query para plantillas
  const templatesQuery = useQuery({
    queryKey: ['templates'],
    queryFn: async () => {
      console.time('loadTemplates');
      const response = await templateAPI.obtenerPlantillas();
      console.timeEnd('loadTemplates');
      
      if (!response.success) {
        console.warn('Templates API returned unsuccessful response');
        return { success: true, templates: [], total: 0 };
      }
      return response;
    },
    staleTime: 10 * 60 * 1000, // 10 minutos
    retry: 1,
    retryDelay: 5000,
  });

  // Query para estado de conexión de Google Drive
  const googleDriveConnectionQuery = useQuery({
    queryKey: ['google-drive-connection'],
    queryFn: async () => {
      try {
        const status = await googleDriveAPI.getConnectionStatus();
        console.log('✅ Google Drive status:', status);
        return status;
      } catch (error) {
        console.error('❌ Error getting Google Drive status:', error);
        // En caso de error, asumir desconectado para evitar estados incorrectos
        return {
          connected: false,
          needs_refresh: false
        };
      }
    },
    staleTime: 2 * 60 * 1000, // 2 minutos
    retry: false, // No reintentar automáticamente para evitar loops
    refetchOnWindowFocus: true, // Refrescar cuando el usuario vuelve a la ventana
  });

  // Derivar datos de las queries
  const categories = categoriesQuery.data?.categories || [];
  const templates = templatesQuery.data?.templates?.map(templateAPI.convertToFrontendTemplate) || [];
  const isLoadingCategories = categoriesQuery.isLoading;
  const isLoadingTemplates = templatesQuery.isLoading;
  
  // Actualizar estado de conexión de Google Drive basado en la query
  useEffect(() => {
    if (googleDriveConnectionQuery.data) {
      const isConnected = googleDriveConnectionQuery.data.connected === true;
      console.log('🔄 Updating Google Drive connection state:', isConnected);
      setIsGoogleDriveConnected(isConnected);
    } else {
      // Si no hay datos, asumir desconectado
      console.log('❌ No Google Drive data, setting to false');
      setIsGoogleDriveConnected(false);
    }
  }, [googleDriveConnectionQuery.data]);

  // Manejar errores de categorías
  useEffect(() => {
    if (categoriesQuery.error) {
      const error = categoriesQuery.error as any;
      console.error('Error loading categories:', error);
      if (error.message?.includes('timeout')) {
        showNotification('error', 'La carga de categorías está tardando demasiado. Intenta refrescar la página.');
      } else {
        showNotification('error', 'Error cargando categorías');
      }
    }
  }, [categoriesQuery.error]);

  // Manejar errores de plantillas (sin notificaciones)
  useEffect(() => {
    if (templatesQuery.error) {
      console.warn('Templates could not be loaded, using empty array');
    }
  }, [templatesQuery.error]);

  // Auto-seleccionar primera categoría
  useEffect(() => {
    if (categories.length > 0 && !selectedCategoryId) {
      setSelectedCategoryId(categories[0].id);
    }
  }, [categories, selectedCategoryId]);

  // Escuchar mensajes de Google Drive para cerrar modal automáticamente
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return;
      
      if (event.data.type === 'google-drive-auth-success') {
        console.log('✅ Conexión exitosa detectada desde TrainingSection');
        // Cerrar modal automáticamente
        setShowGoogleDriveModal(false);
        // Actualizar estado de conexión
        setIsGoogleDriveConnected(true);
        // Invalidar query para refrescar datos
        queryClient.invalidateQueries({ queryKey: ['google-drive-connection'] });
        // Mostrar notificación de éxito
        showNotification('success', '¡Google Drive conectado exitosamente!');
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  };

  const handleFileUpload = async (files: File[], categoriaId: string, tipoDemanda: string) => {
    setIsUploading(true);
    let uploadedCount = 0;
    let errorCount = 0;
    let duplicateCount = 0;

    try {
      for (const file of files) {
        try {
          const response = await categoryAPI.subirDocumento(file, categoriaId, tipoDemanda);
          
          if (response.success) {
            uploadedCount++;
          } else {
            errorCount++;
          }
        } catch (error: any) {
          console.error('Error uploading file:', file.name, error);
          
          // Verificar si es un error de duplicado (status 409)
          if (error.response?.status === 409) {
            duplicateCount++;
            const duplicateInfo = error.response.data.detail;
            
            showNotification('error', 
              `Documento duplicado: "${file.name}" ya existe en esta categoría` +
              (duplicateInfo?.existing_document?.fecha ? 
                ` (subido el ${new Date(duplicateInfo.existing_document.fecha).toLocaleDateString()})` : 
                '')
            );
          } else {
            errorCount++;
          }
        }
      }

      // Mostrar resumen de resultados
      if (uploadedCount > 0 && errorCount === 0 && duplicateCount === 0) {
        showNotification('success', `${uploadedCount} documento(s) subido(s) exitosamente`);
      } else if (uploadedCount > 0) {
        let message = `${uploadedCount} subidos exitosamente`;
        if (duplicateCount > 0) message += `, ${duplicateCount} duplicados omitidos`;
        if (errorCount > 0) message += `, ${errorCount} fallaron`;
        showNotification(errorCount > 0 ? 'error' : 'success', message);
      } else if (duplicateCount > 0 && errorCount === 0) {
        showNotification('error', `${duplicateCount} documento(s) duplicado(s) - no se subieron`);
      } else {
        showNotification('error', 'Error subiendo documentos');
      }

      // Invalidar queries relacionadas después de subir
      queryClient.invalidateQueries({ queryKey: ['documents'] });

    } catch (error) {
      showNotification('error', 'Error procesando documentos');
    } finally {
      setIsUploading(false);
    }
  };



  const selectedCategory = categories.find((cat: Category) => cat.id === selectedCategoryId);

  // ===== FUNCIONES DE ANOTACIONES =====
  
  const loadAnnotations = async (documentId: string) => {
    if (!documentId) return;
    
    try {
      setIsLoadingAnnotations(true);
      const response = await annotationAPI.obtenerAnotaciones(documentId);
      
      if (response.success) {
        // Convertir anotaciones de DB a formato frontend
        const frontendAnnotations = response.annotations.map(annotationAPI.convertToFrontendAnnotation);
        setAnnotations(frontendAnnotations);
      } else {
        showNotification('error', 'Error cargando anotaciones');
      }
    } catch (error) {
      showNotification('error', 'Error cargando anotaciones');
      console.error('Error loading annotations:', error);
    } finally {
      setIsLoadingAnnotations(false);
    }
  };

  const createAnnotation = async (documentId: string, annotationData: any) => {
    try {
      const response = await annotationAPI.crearAnotacion(documentId, {
        texto_seleccionado: annotationData.contenido_seleccionado || '',
        contenido: annotationData.contenido_anotacion || '',
        tipo_anotacion: annotationData.tipo || 'comentario',
        posicion_inicio: annotationData.posicion_inicio,
        posicion_fin: annotationData.posicion_fin,
        etiquetas: annotationData.etiquetas || [],
        prioridad: annotationData.prioridad || 1,
        color: annotationData.color || '#fbbf24'
      });

      if (response.success) {
        // Convertir y añadir a la lista
        const frontendAnnotation = annotationAPI.convertToFrontendAnnotation(response.annotation);
        setAnnotations(prev => [...prev, frontendAnnotation]);
        showNotification('success', 'Anotación creada exitosamente');
        return frontendAnnotation;
      }
    } catch (error) {
      showNotification('error', 'Error creando anotación');
      console.error('Error creating annotation:', error);
    }
  };

  const updateAnnotation = async (annotationId: string, annotationData: any) => {
    try {
      const response = await annotationAPI.actualizarAnotacion(annotationId, {
        contenido: annotationData.contenido_anotacion,
        tipo_anotacion: annotationData.tipo,
        etiquetas: annotationData.etiquetas,
        prioridad: annotationData.prioridad
      });

      if (response.success) {
        const frontendAnnotation = annotationAPI.convertToFrontendAnnotation(response.annotation);
        setAnnotations(prev => 
          prev.map(a => a.id === annotationId ? frontendAnnotation : a)
        );
        showNotification('success', 'Anotación actualizada exitosamente');
        return frontendAnnotation;
      }
    } catch (error) {
      showNotification('error', 'Error actualizando anotación');
      console.error('Error updating annotation:', error);
    }
  };

  const deleteAnnotation = async (annotationId: string) => {
    try {
      const response = await annotationAPI.eliminarAnotacion(annotationId);
      
      if (response.success) {
        setAnnotations(prev => prev.filter(a => a.id !== annotationId));
        showNotification('success', 'Anotación eliminada exitosamente');
      }
    } catch (error) {
      showNotification('error', 'Error eliminando anotación');
      console.error('Error deleting annotation:', error);
    }
  };

  // ===== MUTATIONS PARA PLANTILLAS =====
  
  const createTemplateMutation = useMutation({
    mutationFn: async (templateData: any) => {
      const response = await templateAPI.crearPlantilla({
        nombre: templateData.nombre,
        descripcion: templateData.descripcion,
        tipo_anotacion: templateData.tipo,
        plantilla_contenido: templateData.contenido,
        etiquetas_sugeridas: templateData.etiquetas || [],
        color_defecto: templateData.color || '#fbbf24',
        uso_frecuente: templateData.is_default || false
      });

      if (!response.success) {
        throw new Error('Error creando plantilla');
      }
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      showNotification('success', 'Plantilla creada exitosamente');
    },
    onError: () => {
      showNotification('error', 'Error creando plantilla');
    }
  });

  const updateTemplateMutation = useMutation({
    mutationFn: async ({ templateId, templateData }: { templateId: string; templateData: any }) => {
      const response = await templateAPI.actualizarPlantilla(templateId, {
        nombre: templateData.nombre,
        descripcion: templateData.descripcion,
        tipo_anotacion: templateData.tipo,
        plantilla_contenido: templateData.contenido,
        etiquetas_sugeridas: templateData.etiquetas,
        uso_frecuente: templateData.is_default
      });

      if (!response.success) {
        throw new Error('Error actualizando plantilla');
      }
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      showNotification('success', 'Plantilla actualizada exitosamente');
    },
    onError: () => {
      showNotification('error', 'Error actualizando plantilla');
    }
  });

  const deleteTemplateMutation = useMutation({
    mutationFn: async (templateId: string) => {
      const response = await templateAPI.eliminarPlantilla(templateId);
      
      if (!response.success) {
        throw new Error('Error eliminando plantilla');
      }
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      showNotification('success', 'Plantilla eliminada exitosamente');
    },
    onError: () => {
      showNotification('error', 'Error eliminando plantilla');
    }
  });

  const createDefaultTemplatesMutation = useMutation({
    mutationFn: async () => {
      const response = await templateAPI.crearPlantillasPredeterminadas();
      
      if (!response.success) {
        throw new Error('Error creando plantillas predeterminadas');
      }
      return response;
    },
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      showNotification('success', response.message);
    },
    onError: () => {
      showNotification('error', 'Error creando plantillas predeterminadas');
    }
  });

  // Cargar anotaciones cuando se selecciona un documento
  useEffect(() => {
    if (selectedDocument?.id) {
      loadAnnotations(selectedDocument.id);
    }
    
    // Cleanup al cambiar de documento
    return () => {
      setIsLoadingAnnotations(false);
    };
  }, [selectedDocument?.id]);

  return (
    <div className="flex flex-col h-full training-section relative" style={{ backgroundColor: '#212121' }}>
      {/* Botón flotante de Google Drive - esquina superior derecha */}
      <button
        onClick={() => setShowGoogleDriveModal(true)}
        className={cn(
          "fixed top-6 right-6 z-40 flex items-center gap-2 px-4 py-2 rounded-full shadow-lg border transition-all duration-200 hover:shadow-xl hover:scale-105",
          isGoogleDriveConnected
            ? "bg-green-500 hover:bg-green-600 text-white border-green-400"
            : "bg-white hover:bg-gray-50 text-gray-700 border-gray-200"
        )}
        title={isGoogleDriveConnected ? "Google Drive conectado" : "Conectar Google Drive"}
      >
        {isGoogleDriveConnected ? (
          <CheckCircle className="w-5 h-5" />
        ) : (
          <svg viewBox="0 0 24 24" className="w-5 h-5" fill="currentColor">
            <path d="M6.26 10.5l-3 5.2h6l3-5.2H6.26zM14.47 2H9.53L4.26 10.5h6.01L14.47 2zM16.74 6.24L12.47 2h6.01l4.27 7.39-3 5.2-3.01-8.35z" fill="#4285F4"/>
            <path d="M14.47 16.24h6.01l-4.27-7.39h-6.01l4.27 7.39z" fill="#34A853"/>
            <path d="M6.26 10.5H0.26l3-5.2h6l-3 5.2z" fill="#EA4335"/>
            <path d="M12.47 16.24l3.01-8.35h6.01l-3 5.2-6.02 3.15z" fill="#FBBC04"/>
          </svg>
        )}
        <span className="font-medium text-sm">
          {isGoogleDriveConnected ? "Conectado" : "Google Drive"}
        </span>
      </button>

      {/* Modal de Google Drive */}
      {showGoogleDriveModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Overlay */}
          <div 
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setShowGoogleDriveModal(false)}
          />
          
          {/* Modal Content */}
          <div className="relative bg-background border border-border rounded-xl shadow-2xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-hidden">
            {/* Header del modal */}
            <div className="flex items-center justify-between p-6 border-b border-border bg-card/50">
              <div className="flex items-center gap-3">
                <svg viewBox="0 0 24 24" className="w-8 h-8" fill="currentColor">
                  <path d="M6.26 10.5l-3 5.2h6l3-5.2H6.26zM14.47 2H9.53L4.26 10.5h6.01L14.47 2zM16.74 6.24L12.47 2h6.01l4.27 7.39-3 5.2-3.01-8.35z" fill="#4285F4"/>
                  <path d="M14.47 16.24h6.01l-4.27-7.39h-6.01l4.27 7.39z" fill="#34A853"/>
                  <path d="M6.26 10.5H0.26l3-5.2h6l-3 5.2z" fill="#EA4335"/>
                  <path d="M12.47 16.24l3.01-8.35h6.01l-3 5.2-6.02 3.15z" fill="#FBBC04"/>
                </svg>
                <div>
                  <h2 className="text-xl font-bold text-foreground">Google Drive</h2>
                  <p className="text-sm text-muted-foreground">Conecta tu Google Drive para importar documentos directamente</p>
                </div>
              </div>
              <button
                onClick={() => setShowGoogleDriveModal(false)}
                className="p-2 hover:bg-muted rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-muted-foreground" />
              </button>
            </div>

            {/* Contenido del modal */}
            <div className="p-6 max-h-[calc(90vh-100px)] overflow-y-auto">
              <div className="space-y-6">
                {/* Conector de Google Drive */}
                <GoogleDriveConnector 
                  onConnectionChange={setIsGoogleDriveConnected}
                />

                {/* Explorador de archivos */}
                {isGoogleDriveConnected && (
                  <>
                    {categories.length === 0 ? (
                      <div className="text-center py-12">
                        <FolderPlus className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-foreground mb-2">
                          No tienes categorías
                        </h3>
                        <p className="text-sm text-muted-foreground mb-6">
                          Crea al menos una categoría antes de importar documentos de Google Drive
                        </p>
                        <button
                          onClick={() => {
                            setShowGoogleDriveModal(false);
                            setActiveTab('categories');
                          }}
                          className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-100 rounded-lg transition-colors"
                        >
                          Crear Categorías
                        </button>
                      </div>
                    ) : (
                      <>
                        {/* Info de categoría seleccionada */}
                        {selectedCategory && (
                          <div 
                            className="p-4 border rounded-lg flex items-center gap-3"
                            style={{ borderColor: `${selectedCategory.color}50`, backgroundColor: `${selectedCategory.color}10` }}
                          >
                            <div 
                              className="w-12 h-12 rounded-lg flex items-center justify-center text-xl"
                              style={{ backgroundColor: `${selectedCategory.color}20`, color: selectedCategory.color }}
                            >
                              {selectedCategory.icon}
                            </div>
                            <div>
                              <h3 className="font-medium text-foreground">{selectedCategory.nombre}</h3>
                              {selectedCategory.descripcion && (
                                <p className="text-sm text-muted-foreground">{selectedCategory.descripcion}</p>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Selector de categoría y tipo de demanda */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-card border border-border rounded-lg">
                          <div>
                            <label className="block text-sm font-medium text-foreground mb-2">
                              Categoría de destino *
                            </label>
                            <select
                              value={selectedCategoryId}
                              onChange={(e) => setSelectedCategoryId(e.target.value)}
                              className="w-full p-3 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                            >
                              <option value="">Selecciona una categoría</option>
                              {categories.map(cat => (
                                <option key={cat.id} value={cat.id}>
                                  {cat.icon} {cat.nombre}
                                </option>
                              ))}
                            </select>
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-foreground mb-2">
                              Tipo de demanda *
                            </label>
                            <input
                              type="text"
                              value={tipoDemanda}
                              onChange={(e) => setTipoDemanda(e.target.value)}
                              placeholder="ej: Despido laboral, Accidente de trabajo..."
                              className="w-full p-3 bg-background border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                            />
                          </div>
                        </div>

                        {/* Explorador de Google Drive */}
                        <GoogleDriveExplorer
                          isConnected={isGoogleDriveConnected}
                          selectedCategoryId={selectedCategoryId}
                          selectedTipoDemanda={tipoDemanda}
                          onImportComplete={async (results) => {
                            console.log('📊 Import results received (modal):', results);
                            
                            // Almacenar los resultados para mostrar en el modal detallado
                            setImportResults(results);
                            setShowImportResults(true);
                            
                            // Invalidar queries para actualizar listas
                            queryClient.invalidateQueries({ queryKey: ['documents'] });
                            
                            // Cerrar modal principal de Google Drive
                            setShowGoogleDriveModal(false);
                            
                            // Si hay archivos exitosos, verificar después el procesamiento background
                            const immediate_successful = results.filter(r => r.success).length;
                            if (immediate_successful > 0) {
                              setTimeout(async () => {
                                try {
                                  await queryClient.invalidateQueries({ queryKey: ['documents'] });
                                  await queryClient.refetchQueries({ queryKey: ['documents'] });
                                  console.log('✅ Background processing verification complete');
                                } catch (error) {
                                  console.error('Error verificando resultados:', error);
                                }
                              }, 8000); // 8 segundos para que termine el procesamiento background
                            }
                          }}
                        />
                      </>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Notificación */}
      {notification && (
        <div className={cn(
          "m-4 p-3 rounded-lg text-sm font-medium transition-all duration-300",
          notification.type === 'success' 
            ? "bg-green-500/15 text-green-400 border border-green-500/30"
            : "bg-red-500/15 text-red-400 border border-red-500/30"
        )}>
          {notification.type === 'success' ? '✅' : '❌'} {notification.message}
        </div>
      )}

      {/* Header con tabs */}
      <div className="border-b border-border backdrop-blur-sm p-6" style={{ backgroundColor: '#212121' }}>
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-foreground mb-2">
            Entrenamiento Personalizado
          </h1>
          <p className="text-muted-foreground">
            Organiza y entrena tu IA con documentos legales específicos usando categorías personalizadas
          </p>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 bg-background rounded-lg p-1 overflow-x-auto">
          <button
            onClick={() => setActiveTab('upload')}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all whitespace-nowrap",
              activeTab === 'upload'
                ? "bg-gray-800 text-gray-100 shadow-sm"
                : "text-muted-foreground hover:text-gray-100 hover:bg-purple-600/80"
            )}
          >
            <FileText className="w-4 h-4" />
            Documentos
          </button>
          
          <button
            onClick={() => setActiveTab('categories')}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all whitespace-nowrap",
              activeTab === 'categories'
                ? "bg-gray-800 text-gray-100 shadow-sm"
                : "text-muted-foreground hover:text-gray-100 hover:bg-purple-600/80"
            )}
          >
            <Settings className="w-4 h-4" />
            Gestionar Categorías
          </button>

          <button
            onClick={() => setActiveTab('documents')}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all whitespace-nowrap",
              activeTab === 'documents'
                ? "bg-gray-800 text-gray-100 shadow-sm"
                : "text-muted-foreground hover:text-gray-100 hover:bg-purple-600/80"
            )}
          >
            <BookOpen className="w-4 h-4" />
            Documentos y Anotaciones
          </button>

          <button
            onClick={() => setActiveTab('templates')}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all whitespace-nowrap",
              activeTab === 'templates'
                ? "bg-gray-800 text-gray-100 shadow-sm"
                : "text-muted-foreground hover:text-gray-100 hover:bg-purple-600/80"
            )}
          >
            <MessageSquare className="w-4 h-4" />
            Plantillas
          </button>
        </div>
      </div>

      {/* Contenido de tabs */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'upload' && (
          <div className="max-w-6xl mx-auto space-y-6">
            {categories.length === 0 ? (
              <div className="text-center py-12">
                <FolderPlus className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">
                  No tienes categorías
                </h3>
                <p className="text-sm text-muted-foreground mb-6">
                  Crea al menos una categoría antes de agregar documentos
                </p>
                <button
                  onClick={() => setActiveTab('categories')}
                  className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-100 rounded-lg transition-colors"
                >
                  Crear Categorías
                </button>
              </div>
            ) : (
              <>
                {/* Header explicativo */}
                <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 mb-6">
                  <h2 className="text-lg font-semibold text-gray-100 mb-2">Agregar Documentos a tu Colección</h2>
                  <p className="text-gray-300 text-sm">
                    Configura la categoría y tipo de demanda para tus documentos, luego importa desde Google Drive o sube desde tu computadora.
                  </p>
                </div>

                {/* Configuración global */}
                <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-6 mb-6">
                  <h3 className="text-md font-semibold text-gray-100 mb-4 flex items-center gap-2">
                    <Settings className="w-4 h-4" />
                    Configuración de documentos
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-200 mb-2">
                        Categoría de destino *
                      </label>
                      <select
                        value={selectedCategoryId}
                        onChange={(e) => setSelectedCategoryId(e.target.value)}
                        className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        <option value="">Selecciona una categoría</option>
                        {categories.map(cat => (
                          <option key={cat.id} value={cat.id}>
                            {cat.icon} {cat.nombre}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-200 mb-2">
                        Tipo específico de demanda *
                      </label>
                      <input
                        type="text"
                        value={tipoDemanda}
                        onChange={(e) => setTipoDemanda(e.target.value)}
                        placeholder="ej: Despido laboral, Accidente de trabajo..."
                        className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                </div>

                {/* Google Drive - Componente principal */}
                <div className="bg-gray-900/30 border border-gray-700 rounded-lg p-6 mb-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-gray-700 rounded-lg">
                        <svg viewBox="0 0 24 24" className="w-5 h-5" fill="currentColor">
                          <path d="M6.26 10.5l-3 5.2h6l3-5.2H6.26zM14.47 2H9.53L4.26 10.5h6.01L14.47 2zM16.74 6.24L12.47 2h6.01l4.27 7.39-3 5.2-3.01-8.35z" fill="#4285F4"/>
                          <path d="M14.47 16.24h6.01l-4.27-7.39h-6.01l4.27 7.39z" fill="#34A853"/>
                          <path d="M6.26 10.5H0.26l3-5.2h6l-3 5.2z" fill="#EA4335"/>
                          <path d="M12.47 16.24l3.01-8.35h6.01l-3 5.2-6.02 3.15z" fill="#FBBC04"/>
                        </svg>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="text-lg font-semibold text-gray-100">Google Drive</h3>
                          {isGoogleDriveConnected && (
                            <span className="px-2 py-1 bg-green-900/50 text-green-400 text-xs rounded-full border border-green-700">
                              Conectado
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-400">Importa documentos directamente desde tu Drive</p>
                      </div>
                    </div>
                    
                    {/* Botón para mostrar subida local */}
                    <button
                      onClick={() => setShowLocalUpload(!showLocalUpload)}
                      className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 text-sm rounded-lg transition-colors border border-gray-600"
                    >
                      <Upload className="w-4 h-4" />
                      <span>Subir desde PC</span>
                      {showLocalUpload ? (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      )}
                    </button>
                  </div>

                  {!isGoogleDriveConnected ? (
                    <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center">
                      <Cloud className="w-12 h-12 text-gray-500 mx-auto mb-4" />
                      <h4 className="text-lg font-medium text-gray-200 mb-2">
                        Conecta Google Drive
                      </h4>
                      <p className="text-sm text-gray-400 mb-4">
                        Accede a tus documentos para importarlos sin descargar
                      </p>
                      <button
                        onClick={() => setShowGoogleDriveModal(true)}
                        className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-100 rounded-lg transition-colors border border-gray-600"
                      >
                        Conectar Google Drive
                      </button>
                    </div>
                  ) : (
                    <div className="border border-gray-600 rounded-lg overflow-hidden bg-gray-800/50">
                      <div className="p-4 bg-gray-800/80 border-b border-gray-600">
                        <h4 className="font-medium text-gray-100">Explorar documentos</h4>
                        <p className="text-sm text-gray-400">
                          Navega y selecciona archivos para importar
                        </p>
                      </div>
                      
                      <div className="max-h-96 overflow-y-auto">
                        <GoogleDriveExplorer
                          isConnected={isGoogleDriveConnected}
                          selectedCategoryId={selectedCategoryId}
                          selectedTipoDemanda={tipoDemanda}
                          onImportComplete={async (results) => {
                            console.log('📊 Import results received (compact):', results);
                            
                            // Almacenar los resultados para mostrar en el modal detallado
                            setImportResults(results);
                            setShowImportResults(true);
                            
                            // Invalidar queries para actualizar listas
                            queryClient.invalidateQueries({ queryKey: ['documents'] });
                            
                            // Si hay archivos exitosos, verificar después el procesamiento background
                            const immediate_successful = results.filter(r => r.success).length;
                            if (immediate_successful > 0) {
                              setTimeout(async () => {
                                try {
                                  await queryClient.invalidateQueries({ queryKey: ['documents'] });
                                  await queryClient.refetchQueries({ queryKey: ['documents'] });
                                  console.log('✅ Background processing verification complete (compact)');
                                } catch (error) {
                                  console.error('Error verificando resultados:', error);
                                }
                              }, 8000); // 8 segundos para que termine el procesamiento background
                            }
                          }}
                          compact={false}
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Subida local - Componente colapsible */}
                {showLocalUpload && (
                  <div className="bg-gray-900/30 border border-gray-700 rounded-lg p-6">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="p-2 bg-gray-700 rounded-lg">
                        <Upload className="w-5 h-5 text-gray-200" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-100">Subir desde computadora</h3>
                        <p className="text-sm text-gray-400">Arrastra archivos o selecciona desde tu dispositivo</p>
                      </div>
                    </div>
                    
                    <UploadZone
                      onFileUpload={handleFileUpload}
                      isUploading={isUploading}
                      categories={categories}
                      selectedCategoryId={selectedCategoryId}
                      onCategoryChange={setSelectedCategoryId}
                    />
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {activeTab === 'categories' && (
          <div className="max-w-4xl mx-auto">
            <CategoryManager 
              onCategorySelect={(category) => {
                if (category) {
                  setSelectedCategoryId(category.id);
                  setActiveTab('upload'); // Cambiar a upload después de seleccionar
                }
              }}
              selectedCategoryId={selectedCategoryId}
            />
          </div>
        )}

        {activeTab === 'documents' && (
          <DocumentLibrary
            onDocumentSelect={setSelectedDocument}
            selectedCategoryId={selectedCategoryId}
          />
        )}

        {activeTab === 'templates' && (
          <AnnotationTemplates
            templates={templates}
            onTemplateCreate={(templateData) => createTemplateMutation.mutate(templateData)}
            onTemplateUpdate={(template) => {
              if (template.id) {
                updateTemplateMutation.mutate({
                  templateId: template.id,
                  templateData: template
                });
              }
            }}
            onTemplateDelete={(templateId) => deleteTemplateMutation.mutate(templateId)}
            onTemplateUse={(template) => {
              // Usar plantilla para crear nueva anotación
              if (selectedDocument) {
                setEditingAnnotation({
                  id: '',
                  posicion_inicio: 0,
                  posicion_fin: 0,
                  contenido_seleccionado: '',
                  contenido_anotacion: template.contenido,
                  tipo: template.tipo,
                  etiquetas: template.etiquetas,
                  prioridad: template.prioridad_sugerida || 1,
                  created_at: new Date().toISOString(),
                  author: 'Usuario'
                });
                setShowAnnotationForm(true);
              } else {
                showNotification('error', 'Selecciona un documento primero');
              }
            }}
            isLoading={isLoadingTemplates}
            onCreateDefaults={() => createDefaultTemplatesMutation.mutate()}
          />
        )}
      </div>

      {/* Visor de documentos con anotaciones */}
      {selectedDocument && (
        <div className="fixed inset-0 z-50 flex">
          <DocumentViewer
            document={selectedDocument}
            annotations={annotations}
            onClose={() => setSelectedDocument(null)}
            onAnnotationCreate={(annotation) => {
              if (selectedDocument?.id) {
                createAnnotation(selectedDocument.id, annotation);
              }
            }}
            onAnnotationSelect={setSelectedAnnotation}
            showAnnotations={showAnnotationPanel}
            isLoading={isLoadingAnnotations}
          />
          
          {showAnnotationPanel && (
            <AnnotationPanel
              annotations={annotations}
              selectedAnnotationId={selectedAnnotation?.id}
              onAnnotationSelect={setSelectedAnnotation}
              onAnnotationEdit={(annotation) => {
                setEditingAnnotation(annotation);
                setShowAnnotationForm(true);
              }}
              onAnnotationDelete={(annotationId) => {
                deleteAnnotation(annotationId);
              }}
              isLoading={isLoadingAnnotations}
            />
          )}
        </div>
      )}

      {/* Formulario de anotaciones */}
      <AnnotationForm
        annotation={editingAnnotation}
        isOpen={showAnnotationForm}
        onClose={() => {
          setShowAnnotationForm(false);
          setEditingAnnotation(null);
        }}
        onSave={async (annotation) => {
          try {
            if (editingAnnotation?.id && selectedDocument?.id) {
              // Actualizar anotación existente
              await updateAnnotation(editingAnnotation.id, annotation);
            } else if (selectedDocument?.id) {
              // Crear nueva anotación
              await createAnnotation(selectedDocument.id, annotation);
            }
            setShowAnnotationForm(false);
            setEditingAnnotation(null);
          } catch (error) {
            showNotification('error', 'Error guardando anotación');
            console.error('Error saving annotation:', error);
          }
        }}
        templates={templates}
      />

      {/* Modal de resultados de importación */}
      <ImportResultsModal
        isOpen={showImportResults}
        onClose={() => setShowImportResults(false)}
        results={importResults}
        onRetry={(failedFiles) => {
          console.log('Retrying failed files:', failedFiles);
          setShowImportResults(false);
          showNotification('success', `Reintentando ${failedFiles.length} archivo(s)...`);
          // TODO: Implementar lógica de reintento
        }}
      />
    </div>
  );
} 