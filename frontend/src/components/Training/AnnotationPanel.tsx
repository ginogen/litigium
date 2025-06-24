import React, { useState } from 'react';
import { cn } from '@/utils';
import { 
  MessageSquare, 
  Edit, 
  Trash2, 
  Calendar,
  Tag,
  User,
  ChevronDown,
  ChevronRight,
  Filter,
  Search,
  BookOpen,
  Target,
  AlertTriangle,
  MessageCircle,
  Loader2
} from 'lucide-react';
import { AnnotationSkeleton } from '../ui/Skeleton';

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
}

interface AnnotationPanelProps {
  annotations: Annotation[];
  onAnnotationSelect?: (annotation: Annotation) => void;
  onAnnotationEdit?: (annotation: Annotation) => void;
  onAnnotationDelete?: (annotationId: string) => void;
  selectedAnnotationId?: string;
  isLoading?: boolean;
}

export function AnnotationPanel({ 
  annotations, 
  onAnnotationSelect,
  onAnnotationEdit,
  onAnnotationDelete,
  selectedAnnotationId,
  isLoading = false
}: AnnotationPanelProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [expandedAnnotations, setExpandedAnnotations] = useState<Set<string>>(new Set());
  const [sortBy, setSortBy] = useState<'created' | 'type' | 'priority'>('created');

  const getTypeIcon = (tipo: string) => {
    switch (tipo) {
      case 'comentario':
        return <MessageCircle className="w-4 h-4 text-blue-500" />;
      case 'precedente':
        return <BookOpen className="w-4 h-4 text-green-500" />;
      case 'estrategia':
        return <Target className="w-4 h-4 text-yellow-500" />;
      case 'problema':
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      default:
        return <MessageSquare className="w-4 h-4 text-gray-500" />;
    }
  };

  const getTypeLabel = (tipo: string) => {
    switch (tipo) {
      case 'comentario':
        return 'Comentario';
      case 'precedente':
        return 'Precedente';
      case 'estrategia':
        return 'Estrategia';
      case 'problema':
        return 'Problema';
      default:
        return 'Desconocido';
    }
  };

  const getTypeColor = (tipo: string) => {
    switch (tipo) {
      case 'comentario':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'precedente':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'estrategia':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'problema':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getPriorityColor = (prioridad?: number) => {
    if (!prioridad) return 'bg-gray-200';
    if (prioridad >= 8) return 'bg-red-500';
    if (prioridad >= 5) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const toggleExpanded = (annotationId: string) => {
    const newExpanded = new Set(expandedAnnotations);
    if (newExpanded.has(annotationId)) {
      newExpanded.delete(annotationId);
    } else {
      newExpanded.add(annotationId);
    }
    setExpandedAnnotations(newExpanded);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Filtrar y ordenar anotaciones
  const filteredAnnotations = annotations
    .filter(annotation => {
      // Filtro por búsqueda
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        return (
          annotation.contenido_anotacion.toLowerCase().includes(query) ||
          annotation.contenido_seleccionado.toLowerCase().includes(query) ||
          annotation.etiquetas?.some(tag => tag.toLowerCase().includes(query))
        );
      }
      return true;
    })
    .filter(annotation => {
      // Filtro por tipo
      if (typeFilter !== 'all') {
        return annotation.tipo === typeFilter;
      }
      return true;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'type':
          return a.tipo.localeCompare(b.tipo);
        case 'priority':
          return (b.prioridad || 0) - (a.prioridad || 0);
        case 'created':
        default:
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
    });

  const annotationsByType = annotations.reduce((acc, annotation) => {
    acc[annotation.tipo] = (acc[annotation.tipo] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="w-80 h-full border-l border-border bg-card/50 backdrop-blur-sm flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-foreground flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            Anotaciones
          </h3>
          <span className="text-sm text-muted-foreground">
            {filteredAnnotations.length} de {annotations.length}
          </span>
        </div>

        {/* Búsqueda */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Buscar anotaciones..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        </div>

        {/* Filtros */}
        <div className="flex gap-2 mb-3">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="flex-1 p-2 bg-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          >
            <option value="all">Todos los tipos</option>
            <option value="comentario">Comentarios</option>
            <option value="precedente">Precedentes</option>
            <option value="estrategia">Estrategias</option>
            <option value="problema">Problemas</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="flex-1 p-2 bg-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          >
            <option value="created">Por fecha</option>
            <option value="type">Por tipo</option>
            <option value="priority">Por prioridad</option>
          </select>
        </div>

        {/* Estadísticas rápidas */}
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(annotationsByType).map(([tipo, count]) => (
            <div key={tipo} className="flex items-center gap-2 text-xs">
              {getTypeIcon(tipo)}
              <span className="text-muted-foreground">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Lista de anotaciones */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-2 space-y-2">
            {Array.from({ length: 3 }).map((_, index) => (
              <AnnotationSkeleton key={index} />
            ))}
          </div>
        ) : filteredAnnotations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full p-6 text-center">
            <MessageSquare className="w-12 h-12 text-muted-foreground mb-3" />
            <p className="text-muted-foreground mb-2">
              {annotations.length === 0 ? 'No hay anotaciones' : 'No se encontraron anotaciones'}
            </p>
            <p className="text-xs text-muted-foreground">
              {annotations.length === 0 
                ? 'Selecciona texto en el documento para crear anotaciones'
                : 'Prueba con otros términos de búsqueda'
              }
            </p>
          </div>
        ) : (
          <div className="p-2 space-y-2">
            {filteredAnnotations.map((annotation) => {
              const isExpanded = expandedAnnotations.has(annotation.id);
              const isSelected = selectedAnnotationId === annotation.id;

              return (
                <div
                  key={annotation.id}
                  className={cn(
                    "border rounded-lg p-3 transition-all cursor-pointer",
                    isSelected 
                      ? "border-primary bg-primary/5 shadow-sm" 
                      : "border-border bg-background hover:bg-card/50"
                  )}
                  onClick={() => onAnnotationSelect?.(annotation)}
                >
                  {/* Header de la anotación */}
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      {getTypeIcon(annotation.tipo)}
                      <span className={cn(
                        "px-2 py-1 rounded-md text-xs font-medium border",
                        getTypeColor(annotation.tipo)
                      )}>
                        {getTypeLabel(annotation.tipo)}
                      </span>
                      
                      {annotation.prioridad && (
                        <div 
                          className={cn(
                            "w-2 h-2 rounded-full",
                            getPriorityColor(annotation.prioridad)
                          )}
                          title={`Prioridad: ${annotation.prioridad}/10`}
                        />
                      )}
                    </div>

                    <div className="flex items-center gap-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onAnnotationEdit?.(annotation);
                        }}
                        className="p-1 text-muted-foreground hover:text-foreground rounded transition-colors"
                        title="Editar"
                      >
                        <Edit className="w-3 h-3" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onAnnotationDelete?.(annotation.id);
                        }}
                        className="p-1 text-muted-foreground hover:text-red-400 rounded transition-colors"
                        title="Eliminar"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleExpanded(annotation.id);
                        }}
                        className="p-1 text-muted-foreground hover:text-foreground rounded transition-colors"
                        title={isExpanded ? "Contraer" : "Expandir"}
                      >
                        {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                      </button>
                    </div>
                  </div>

                  {/* Contenido seleccionado (preview) */}
                  <div className="mb-2">
                    <div className="text-xs text-muted-foreground mb-1">Texto seleccionado:</div>
                    <div className="text-sm text-foreground bg-background border border-border rounded p-2 line-clamp-2">
                      "{annotation.contenido_seleccionado}"
                    </div>
                  </div>

                  {/* Anotación (preview o completa) */}
                  <div className="mb-3">
                    <div className="text-xs text-muted-foreground mb-1">Anotación:</div>
                    <div className={cn(
                      "text-sm text-foreground",
                      !isExpanded && "line-clamp-3"
                    )}>
                      {annotation.contenido_anotacion}
                    </div>
                  </div>

                  {/* Información adicional expandida */}
                  {isExpanded && (
                    <div className="space-y-2 pt-2 border-t border-border">
                      {/* Etiquetas */}
                      {annotation.etiquetas && annotation.etiquetas.length > 0 && (
                        <div>
                          <div className="text-xs text-muted-foreground mb-1">Etiquetas:</div>
                          <div className="flex flex-wrap gap-1">
                            {annotation.etiquetas.map((tag, index) => (
                              <span 
                                key={index}
                                className="px-2 py-1 bg-secondary text-secondary-foreground rounded-md text-xs"
                              >
                                #{tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Metadatos */}
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {formatDate(annotation.created_at)}
                        </div>
                        {annotation.author && (
                          <div className="flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {annotation.author}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Fecha (cuando no está expandido) */}
                  {!isExpanded && (
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Calendar className="w-3 h-3" />
                      {formatDate(annotation.created_at)}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
} 