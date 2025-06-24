import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { 
  BookTemplate,
  Plus,
  Edit,
  Trash2,
  Save,
  X,
  MessageCircle,
  BookOpen,
  Target,
  AlertTriangle,
  Copy,
  Star,
  Tag,
  Loader2
} from 'lucide-react';
import { TemplateSkeleton } from '../ui/Skeleton';

interface AnnotationTemplate {
  id?: string;
  nombre: string;
  tipo: 'comentario' | 'precedente' | 'estrategia' | 'problema';
  contenido: string;
  etiquetas: string[];
  prioridad_sugerida?: number;
  is_default?: boolean;
  created_at?: string;
}

interface AnnotationTemplatesProps {
  templates: AnnotationTemplate[];
  onTemplateCreate?: (template: AnnotationTemplate) => void;
  onTemplateUpdate?: (template: AnnotationTemplate) => void;
  onTemplateDelete?: (templateId: string) => void;
  onTemplateUse?: (template: AnnotationTemplate) => void;
  isLoading?: boolean;
  onCreateDefaults?: () => void;
}

export function AnnotationTemplates({
  templates,
  onTemplateCreate,
  onTemplateUpdate,
  onTemplateDelete,
  onTemplateUse,
  isLoading = false,
  onCreateDefaults
}: AnnotationTemplatesProps) {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<AnnotationTemplate | null>(null);
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

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
        return <BookTemplate className="w-4 h-4 text-gray-500" />;
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

  // NUEVO: Solo usar plantillas del backend, no hardcodeadas
  const allTemplates = templates;

  const filteredTemplates = allTemplates.filter(template => {
    const matchesType = typeFilter === 'all' || template.tipo === typeFilter;
    const matchesSearch = !searchQuery.trim() || 
      template.nombre.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.contenido.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.etiquetas.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
    return matchesType && matchesSearch;
  });

  const handleCreateTemplate = () => {
    setEditingTemplate(null);
    setIsFormOpen(true);
  };

  const handleEditTemplate = (template: AnnotationTemplate) => {
    // NUEVO: Permitir editar todas las plantillas (incluidas las predeterminadas)
    setEditingTemplate(template);
    setIsFormOpen(true);
  };

  const handleDeleteTemplate = (templateId: string) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar esta plantilla?')) {
      onTemplateDelete?.(templateId);
    }
  };

  const handleUseTemplate = (template: AnnotationTemplate) => {
    onTemplateUse?.(template);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookTemplate className="w-6 h-6 text-primary" />
          <h2 className="text-xl font-semibold text-foreground">Plantillas de Anotaciones</h2>
        </div>
        <div className="flex gap-2">
          {onCreateDefaults && (
            <button
              onClick={onCreateDefaults}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              <Star className="w-4 h-4" />
              Crear Predeterminadas
            </button>
          )}
          <button
            onClick={handleCreateTemplate}
            disabled={isLoading}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-100 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
            Nueva Plantilla
          </button>
        </div>
      </div>

      {/* Filtros */}
      <div className="flex gap-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Buscar plantillas..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full p-3 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        </div>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="p-3 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
        >
          <option value="all">Todos los tipos</option>
          <option value="comentario">Comentarios</option>
          <option value="precedente">Precedentes</option>
          <option value="estrategia">Estrategias</option>
          <option value="problema">Problemas</option>
        </select>
      </div>

      {/* Lista de plantillas */}
      <div className="grid gap-4">
        {isLoading ? (
          <div className="space-y-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <TemplateSkeleton key={index} />
            ))}
          </div>
        ) : filteredTemplates.length === 0 ? (
          <div className="text-center py-12">
            <BookTemplate className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              No se encontraron plantillas
            </h3>
            <p className="text-sm text-muted-foreground">
              {allTemplates.length === 0 
                ? 'Crea tu primera plantilla para acelerar la creación de anotaciones'
                : 'Prueba con otros términos de búsqueda o filtros'
              }
            </p>
          </div>
        ) : (
          filteredTemplates.map((template) => (
            <div
              key={template.id}
              className="bg-card border border-border rounded-lg p-4 hover:bg-card/80 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  {getTypeIcon(template.tipo)}
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-foreground truncate">
                      {template.nombre}
                      {template.is_default && (
                        <span className="ml-2 px-2 py-1 bg-primary/10 text-primary rounded text-xs">
                          Por defecto
                        </span>
                      )}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={cn(
                        "px-2 py-1 rounded-md text-xs font-medium border",
                        getTypeColor(template.tipo)
                      )}>
                        {getTypeLabel(template.tipo)}
                      </span>
                      {template.prioridad_sugerida && (
                        <div className="flex items-center gap-1">
                          <Star className="w-3 h-3 text-yellow-500" />
                          <span className="text-xs text-muted-foreground">
                            {template.prioridad_sugerida}/10
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleUseTemplate(template)}
                    className="p-2 text-muted-foreground hover:text-foreground hover:bg-background rounded-lg transition-colors"
                    title="Usar plantilla"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                  {!template.is_default && (
                    <>
                      <button
                        onClick={() => handleEditTemplate(template)}
                        className="p-2 text-muted-foreground hover:text-foreground hover:bg-background rounded-lg transition-colors"
                        title="Editar"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteTemplate(template.id!)}
                        className="p-2 text-muted-foreground hover:text-red-400 hover:bg-background rounded-lg transition-colors"
                        title="Eliminar"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* Contenido preview */}
              <div className="mb-3">
                <p className="text-sm text-foreground line-clamp-3">
                  {template.contenido}
                </p>
              </div>

              {/* Etiquetas */}
              {template.etiquetas.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {template.etiquetas.map((tag, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-secondary text-secondary-foreground rounded-md text-xs flex items-center gap-1"
                    >
                      <Tag className="w-3 h-3" />
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Formulario de plantilla */}
      {isFormOpen && (
        <TemplateForm
          template={editingTemplate}
          onSave={(template) => {
            if (editingTemplate) {
              onTemplateUpdate?.(template);
            } else {
              onTemplateCreate?.(template);
            }
            setIsFormOpen(false);
          }}
          onCancel={() => setIsFormOpen(false)}
        />
      )}
    </div>
  );
}

// Componente del formulario de plantilla
interface TemplateFormProps {
  template?: AnnotationTemplate | null;
  onSave: (template: AnnotationTemplate) => void;
  onCancel: () => void;
}

function TemplateForm({ template, onSave, onCancel }: TemplateFormProps) {
  const [formData, setFormData] = useState<AnnotationTemplate>({
    nombre: '',
    tipo: 'comentario',
    contenido: '',
    etiquetas: [],
    prioridad_sugerida: 5
  });
  const [newTag, setNewTag] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (template) {
      setFormData(template);
    }
  }, [template]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.nombre.trim()) {
      newErrors.nombre = 'El nombre es obligatorio';
    }

    if (!formData.contenido.trim()) {
      newErrors.contenido = 'El contenido es obligatorio';
    }

    if (formData.contenido.length > 2000) {
      newErrors.contenido = 'El contenido no puede superar los 2000 caracteres';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (!validateForm()) return;
    onSave(formData);
  };

  const addTag = () => {
    if (newTag.trim() && !formData.etiquetas.includes(newTag.trim())) {
      setFormData(prev => ({
        ...prev,
        etiquetas: [...prev.etiquetas, newTag.trim()]
      }));
      setNewTag('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      etiquetas: prev.etiquetas.filter(tag => tag !== tagToRemove)
    }));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-background border border-border rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h3 className="text-lg font-semibold text-foreground">
            {template ? 'Editar Plantilla' : 'Nueva Plantilla'}
          </h3>
          <button
            onClick={onCancel}
            className="p-2 text-muted-foreground hover:text-foreground hover:bg-background rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Contenido */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          <div className="space-y-4">
            {/* Nombre */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Nombre de la plantilla *
              </label>
              <input
                type="text"
                value={formData.nombre}
                onChange={(e) => setFormData(prev => ({ ...prev, nombre: e.target.value }))}
                placeholder="Ej: Análisis de precedente laboral"
                className={cn(
                  "w-full p-3 bg-background border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent",
                  errors.nombre ? "border-red-500" : "border-border"
                )}
              />
              {errors.nombre && (
                <p className="mt-1 text-sm text-red-500">{errors.nombre}</p>
              )}
            </div>

            {/* Tipo */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Tipo de anotación
              </label>
              <select
                value={formData.tipo}
                onChange={(e) => setFormData(prev => ({ ...prev, tipo: e.target.value as any }))}
                className="w-full p-3 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="comentario">💬 Comentario</option>
                <option value="precedente">📚 Precedente</option>
                <option value="estrategia">🎯 Estrategia</option>
                <option value="problema">⚠️ Problema</option>
              </select>
            </div>

            {/* Contenido */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Contenido de la plantilla *
              </label>
              <textarea
                value={formData.contenido}
                onChange={(e) => setFormData(prev => ({ ...prev, contenido: e.target.value }))}
                placeholder="Contenido de la plantilla. Puedes usar [placeholders] para campos variables..."
                rows={8}
                className={cn(
                  "w-full p-3 bg-background border rounded-lg text-foreground resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent",
                  errors.contenido ? "border-red-500" : "border-border"
                )}
              />
              {errors.contenido && (
                <p className="mt-1 text-sm text-red-500">{errors.contenido}</p>
              )}
              <div className="mt-1 text-xs text-muted-foreground text-right">
                {formData.contenido.length}/2000 caracteres
              </div>
            </div>

            {/* Etiquetas */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Etiquetas sugeridas
              </label>
              <div className="space-y-3">
                {formData.etiquetas.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {formData.etiquetas.map((tag, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center gap-1 px-3 py-1 bg-secondary text-secondary-foreground rounded-md text-sm"
                      >
                        <Tag className="w-3 h-3" />
                        {tag}
                        <button
                          type="button"
                          onClick={() => removeTag(tag)}
                          className="ml-1 p-0.5 hover:bg-secondary-foreground/20 rounded"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                )}

                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addTag();
                      }
                    }}
                    placeholder="Nueva etiqueta..."
                    className="flex-1 p-2 bg-background border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                  <button
                    type="button"
                    onClick={addTag}
                    disabled={!newTag.trim()}
                    className="px-3 py-2 bg-secondary hover:bg-secondary/80 text-secondary-foreground rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Prioridad sugerida */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Prioridad sugerida (1-10)
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={formData.prioridad_sugerida || 5}
                  onChange={(e) => setFormData(prev => ({ ...prev, prioridad_sugerida: parseInt(e.target.value) }))}
                  className="flex-1"
                />
                <div className="flex items-center gap-1 min-w-[3rem]">
                  <Star className="w-4 h-4 text-yellow-500" />
                  <span className="text-sm font-medium text-foreground">
                    {formData.prioridad_sugerida || 5}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-border">
          <button
            onClick={onCancel}
            className="px-4 py-2 border border-border rounded-lg text-foreground hover:bg-background transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-100 rounded-lg transition-colors flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            Guardar Plantilla
          </button>
        </div>
      </div>
    </div>
  );
} 