import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cn } from '@/lib/utils';
import { 
  Search, 
  Filter, 
  Download, 
  Eye, 
  FileText, 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  FileX,
  Loader2,
  MoreVertical,
  Calendar,
  Folder
} from 'lucide-react';
import { categoryAPI } from '@/lib/index.ts';
import { DocumentSkeleton } from '../ui/Skeleton';

interface Document {
  id: string;
  nombre_archivo: string;
  archivo_url: string;
  tipo_mime: string;
  tipo_demanda: string;
  estado_procesamiento: string;
  vectorizado: boolean;
  created_at: string;
  processed_at?: string;
  categoria?: {
    nombre: string;
    color: string;
    icon: string;
  };
  tamaño_bytes?: number;
  error_procesamiento?: string;
  total_anotaciones?: number;
  anotaciones_alta_prioridad?: number;
  anotaciones_precedentes?: number;
  anotaciones_estrategias?: number;
}

interface DocumentLibraryProps {
  onDocumentSelect?: (document: Document) => void;
  selectedCategoryId?: string;
}

export function DocumentLibrary({ onDocumentSelect, selectedCategoryId }: DocumentLibraryProps) {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [hasMore, setHasMore] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  // Query para cargar documentos
  const documentsQuery = useQuery({
    queryKey: ['documents', selectedCategoryId, statusFilter],
    queryFn: async () => {
      const response = await categoryAPI.obtenerDocumentos({
        categoria_id: selectedCategoryId || undefined,
        estado: statusFilter !== 'all' ? statusFilter : undefined,
        limit: 50,
        offset: 0
      });
      
      if (!response.success) {
        throw new Error('Error obteniendo documentos');
      }
      
      // Mapear documentos del backend al formato del frontend
      const mappedDocuments: Document[] = response.documents.map((doc: any) => ({
        id: doc.id,
        nombre_archivo: doc.nombre_archivo,
        archivo_url: doc.archivo_url,
        tipo_mime: doc.tipo_mime || 'application/pdf',
        tipo_demanda: doc.tipo_demanda,
        estado_procesamiento: doc.estado_procesamiento,
        vectorizado: doc.vectorizado,
        created_at: doc.created_at,
        processed_at: doc.processed_at,
        categoria: doc.categoria ? {
          nombre: doc.categoria.nombre,
          color: doc.categoria.color,
          icon: doc.categoria.icon
        } : undefined,
        tamaño_bytes: doc.tamaño_bytes,
        error_procesamiento: doc.error_procesamiento,
        total_anotaciones: doc.total_anotaciones || 0,
        anotaciones_alta_prioridad: doc.anotaciones_alta_prioridad || 0,
        anotaciones_precedentes: doc.anotaciones_precedentes || 0,
        anotaciones_estrategias: doc.anotaciones_estrategias || 0
      }));
      
      // Actualizar información de paginación
      if (response.pagination) {
        setHasMore(response.pagination.has_more);
      }
      
      // Log de performance si está disponible
      if (response.performance) {
        console.log(`📊 Documents loaded using: ${response.performance.method}`);
        if (response.performance.note) {
          console.log(`ℹ️ ${response.performance.note}`);
        }
      }
      
      return mappedDocuments;
    },
    staleTime: 2 * 60 * 1000, // 2 minutos
    retry: 2,
    retryDelay: 1000,
  });

  // Mutation para descargar documento
  const downloadMutation = useMutation({
    mutationFn: async (documentId: string) => {
      const response = await categoryAPI.obtenerUrlDescarga(documentId);
      if (!response.success || !response.download_url) {
        throw new Error('Error obteniendo URL de descarga');
      }
      return response.download_url;
    },
    onSuccess: (downloadUrl) => {
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = '';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },
    onError: (error) => {
      console.error('Error downloading document:', error);
      alert('Error descargando el documento. Intenta de nuevo.');
    }
  });

  const filterDocuments = () => {
    if (!documentsQuery.data) return [];
    
    let filtered = documentsQuery.data;

    // Filtro por búsqueda
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(doc =>
        doc.nombre_archivo.toLowerCase().includes(query) ||
        doc.tipo_demanda.toLowerCase().includes(query) ||
        doc.categoria?.nombre.toLowerCase().includes(query)
      );
    }

    return filtered;
  };

  const getStatusIcon = (estado: string) => {
    switch (estado) {
      case 'completado':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'procesando':
        return <Clock className="w-4 h-4 text-yellow-400 animate-spin" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      default:
        return <FileX className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusText = (estado: string) => {
    switch (estado) {
      case 'completado':
        return 'Procesado';
      case 'procesando':
        return 'Procesando...';
      case 'error':
        return 'Error';
      case 'pendiente':
        return 'Pendiente';
      default:
        return 'Desconocido';
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'N/A';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleDownload = async (document: Document) => {
    downloadMutation.mutate(document.id);
  };

  const filteredDocuments = filterDocuments();

  return (
    <div className="bg-card/50 border border-border rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-semibold text-foreground">Biblioteca de Documentos</h2>
        </div>
        
        <div className="text-sm text-muted-foreground">
          {documentsQuery.data ? `${filteredDocuments.length} de ${documentsQuery.data.length} documentos` : '--'}
        </div>
      </div>

      {/* Controles de búsqueda y filtros */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Buscar documentos..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        </div>
        
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          >
            <option value="all">Todos los estados</option>
            <option value="completado">Procesados</option>
            <option value="procesando">Procesando</option>
            <option value="pendiente">Pendientes</option>
            <option value="error">Con errores</option>
          </select>
        </div>
      </div>

      {/* Lista de documentos */}
      <div className="space-y-4">
        {documentsQuery.isLoading ? (
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, index) => (
              <DocumentSkeleton key={index} />
            ))}
          </div>
        ) : documentsQuery.error ? (
          <div className="text-center py-8">
            <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
            <p className="text-red-600 mb-4">Error cargando documentos</p>
            <button 
              onClick={() => documentsQuery.refetch()}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
            >
              Reintentar
            </button>
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="text-center py-8">
            <FileText className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-muted-foreground mb-2">
              {documentsQuery.data?.length === 0 
                ? 'No hay documentos aún' 
                : 'No se encontraron documentos'
              }
            </p>
            <p className="text-xs text-muted-foreground">
              {documentsQuery.data?.length === 0 
                ? 'Sube documentos para comenzar a entrenar el sistema'
                : 'Prueba con otros términos de búsqueda o filtros'
              }
            </p>
          </div>
        ) : (
          filteredDocuments.map((document) => (
            <div
              key={document.id}
              className="bg-background border border-border rounded-lg p-4 hover:bg-card/50 transition-colors cursor-pointer group"
              onClick={() => onDocumentSelect?.(document)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4 flex-1 min-w-0">
                  {/* Ícono de estado */}
                  <div className="flex-shrink-0 mt-1">
                    {getStatusIcon(document.estado_procesamiento)}
                  </div>
                  
                  {/* Información principal */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium text-foreground truncate" title={document.nombre_archivo}>
                        {document.nombre_archivo.length > 40 
                          ? document.nombre_archivo.substring(0, 40) + '...' 
                          : document.nombre_archivo
                        }
                      </h3>
                      
                      {document.categoria && (
                        <span 
                          className="px-2 py-1 rounded-md text-xs font-medium flex-shrink-0"
                          style={{ 
                            backgroundColor: `${document.categoria.color}20`, 
                            color: document.categoria.color 
                          }}
                        >
                          {document.categoria.icon} {document.categoria.nombre}
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm text-muted-foreground mb-2">
                      <span className="flex items-center gap-1">
                        {getStatusIcon(document.estado_procesamiento)}
                        {getStatusText(document.estado_procesamiento)}
                      </span>
                      
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {formatDate(document.created_at)}
                      </span>
                      
                      {document.tamaño_bytes && (
                        <span>
                          {formatFileSize(document.tamaño_bytes)}
                        </span>
                      )}
                    </div>
                    
                    {/* Estadísticas de anotaciones */}
                    {document.total_anotaciones && document.total_anotaciones > 0 && (
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
                          {document.total_anotaciones} anotaciones
                        </span>
                        {document.anotaciones_precedentes && document.anotaciones_precedentes > 0 && (
                          <span className="flex items-center gap-1">
                            <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                            {document.anotaciones_precedentes} precedentes
                          </span>
                        )}
                        {document.anotaciones_estrategias && document.anotaciones_estrategias > 0 && (
                          <span className="flex items-center gap-1">
                            <span className="w-2 h-2 bg-yellow-400 rounded-full"></span>
                            {document.anotaciones_estrategias} estrategias
                          </span>
                        )}
                      </div>
                    )}
                    
                    {/* Error si existe */}
                    {document.error_procesamiento && (
                      <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-600">
                        Error: {document.error_procesamiento}
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Acciones */}
                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDocumentSelect?.(document);
                    }}
                    className="p-2 text-muted-foreground hover:text-foreground hover:bg-background rounded-lg transition-colors"
                    title="Ver documento"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDownload(document);
                    }}
                    disabled={downloadMutation.isPending}
                    className="p-2 text-muted-foreground hover:text-foreground hover:bg-background rounded-lg transition-colors disabled:opacity-50"
                    title="Descargar"
                  >
                    {downloadMutation.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Download className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Información de carga adicional */}
      {hasMore && filteredDocuments.length > 0 && (
        <div className="mt-6 text-center">
          <p className="text-sm text-muted-foreground">
            Mostrando {filteredDocuments.length} documentos. 
            {hasMore && ' Hay más documentos disponibles.'}
          </p>
        </div>
      )}
    </div>
  );
} 