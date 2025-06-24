import React, { useState, useEffect } from 'react';
import { cn } from '../../lib/utils';
import { 
  X,
  Save,
  Plus,
  Tag,
  Star,
  MessageCircle,
  BookOpen,
  Target,
  AlertTriangle,
  Loader2,
  Hash
} from 'lucide-react';

interface Annotation {
  id?: string;
  posicion_inicio?: number;
  posicion_fin?: number;
  contenido_seleccionado?: string;
  contenido_anotacion: string;
  tipo: 'comentario' | 'precedente' | 'estrategia' | 'problema';
  etiquetas?: string[];
  prioridad?: number;
  created_at?: string;
  author?: string;
}

interface AnnotationFormProps {
  annotation?: Annotation | null;
  selectedText?: string;
  isOpen: boolean;
  onClose: () => void;
  onSave: (annotation: Annotation) => void;
  templates?: { tipo: string; contenido: string; etiquetas: string[] }[];
}

export function AnnotationForm({ 
  annotation, 
  selectedText, 
  isOpen, 
  onClose, 
  onSave,
  templates = []
}: AnnotationFormProps) {
  const [formData, setFormData] = useState<Annotation>({
    contenido_anotacion: '',
    tipo: 'comentario',
    etiquetas: [],
    prioridad: 5
  });
  const [newTag, setNewTag] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (isOpen) {
      if (annotation) {
        // Modo edición
        setFormData({
          ...annotation,
          etiquetas: annotation.etiquetas || []
        });
      } else {
        // Modo creación
        setFormData({
          contenido_anotacion: '',
          tipo: 'comentario',
          etiquetas: [],
          prioridad: 5,
          contenido_seleccionado: selectedText || ''
        });
      }
      setErrors({});
    }
  }, [isOpen, annotation, selectedText]);

  const getTypeConfig = (tipo: string) => {
    switch (tipo) {
      case 'comentario':
        return {
          icon: <MessageCircle className="w-4 h-4" />,
          label: 'Comentario',
          color: 'bg-blue-100 text-blue-800 border-blue-200',
          description: 'Observaciones generales sobre el texto'
        };
      case 'precedente':
        return {
          icon: <BookOpen className="w-4 h-4" />,
          label: 'Precedente',
          color: 'bg-green-100 text-green-800 border-green-200',
          description: 'Referencias a casos o jurisprudencia similar'
        };
      case 'estrategia':
        return {
          icon: <Target className="w-4 h-4" />,
          label: 'Estrategia',
          color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
          description: 'Enfoque o táctica legal recomendada'
        };
      case 'problema':
        return {
          icon: <AlertTriangle className="w-4 h-4" />,
          label: 'Problema',
          color: 'bg-red-100 text-red-800 border-red-200',
          description: 'Dificultades o riesgos identificados'
        };
      default:
        return {
          icon: <MessageCircle className="w-4 h-4" />,
          label: 'Desconocido',
          color: 'bg-gray-100 text-gray-800 border-gray-200',
          description: ''
        };
    }
  };

  const handleTipoChange = (tipo: 'comentario' | 'precedente' | 'estrategia' | 'problema') => {
    setFormData(prev => ({ ...prev, tipo }));
    
    // Aplicar plantilla si existe
    const template = templates.find(t => t.tipo === tipo);
    if (template && !formData.contenido_anotacion.trim()) {
      setFormData(prev => ({
        ...prev,
        contenido_anotacion: template.contenido,
        etiquetas: [...(prev.etiquetas || []), ...template.etiquetas]
      }));
    }
  };

  const addTag = () => {
    if (newTag.trim() && !formData.etiquetas?.includes(newTag.trim())) {
      setFormData(prev => ({
        ...prev,
        etiquetas: [...(prev.etiquetas || []), newTag.trim()]
      }));
      setNewTag('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      etiquetas: prev.etiquetas?.filter(tag => tag !== tagToRemove) || []
    }));
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.contenido_anotacion.trim()) {
      newErrors.contenido_anotacion = 'La anotación es obligatoria';
    }

    if (formData.contenido_anotacion.length > 1000) {
      newErrors.contenido_anotacion = 'La anotación no puede superar los 1000 caracteres';
    }

    if (formData.prioridad && (formData.prioridad < 1 || formData.prioridad > 10)) {
      newErrors.prioridad = 'La prioridad debe estar entre 1 y 10';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) return;

    setIsSaving(true);
    try {
      const annotationToSave: Annotation = {
        ...formData,
        created_at: annotation?.created_at || new Date().toISOString(),
        id: annotation?.id || undefined
      };

      await onSave(annotationToSave);
      onClose();
    } catch (error) {
      console.error('Error saving annotation:', error);
      setErrors({ general: 'Error al guardar la anotación' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSave();
    }
  };

  const currentTypeConfig = getTypeConfig(formData.tipo);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div 
        className="bg-background border border-border rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden"
        onKeyDown={handleKeyDown}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
            {currentTypeConfig.icon}
            {annotation ? 'Editar Anotación' : 'Nueva Anotación'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-muted-foreground hover:text-foreground hover:bg-background rounded-lg transition-colors"
            title="Cerrar (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Contenido */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          <div className="space-y-6">
            {/* Texto seleccionado (solo en modo creación) */}
            {!annotation && selectedText && (
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Texto seleccionado:
                </label>
                <div className="p-3 bg-secondary/50 border border-border rounded-lg text-sm text-foreground">
                  "{selectedText}"
                </div>
              </div>
            )}

            {/* Tipo de anotación */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-3">
                Tipo de anotación:
              </label>
              <div className="grid grid-cols-2 gap-3">
                {(['comentario', 'precedente', 'estrategia', 'problema'] as const).map(tipo => {
                  const config = getTypeConfig(tipo);
                  return (
                    <button
                      key={tipo}
                      type="button"
                      onClick={() => handleTipoChange(tipo)}
                      className={cn(
                        "p-3 border rounded-lg text-left transition-all",
                        formData.tipo === tipo
                          ? "border-primary bg-primary/5 shadow-sm"
                          : "border-border hover:bg-card/50"
                      )}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        {config.icon}
                        <span className="font-medium text-foreground">{config.label}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">{config.description}</p>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Contenido de la anotación */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Anotación *
              </label>
              <textarea
                value={formData.contenido_anotacion}
                onChange={(e) => setFormData(prev => ({ ...prev, contenido_anotacion: e.target.value }))}
                placeholder={`Escribe tu ${currentTypeConfig.label.toLowerCase()} aquí...`}
                rows={6}
                className={cn(
                  "w-full p-3 bg-background border rounded-lg text-foreground resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent",
                  errors.contenido_anotacion ? "border-red-500" : "border-border"
                )}
              />
              {errors.contenido_anotacion && (
                <p className="mt-1 text-sm text-red-500">{errors.contenido_anotacion}</p>
              )}
              <div className="mt-1 text-xs text-muted-foreground text-right">
                {formData.contenido_anotacion.length}/1000 caracteres
              </div>
            </div>

            {/* Etiquetas */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Etiquetas
              </label>
              <div className="space-y-3">
                {/* Etiquetas existentes */}
                {formData.etiquetas && formData.etiquetas.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {formData.etiquetas.map((tag, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center gap-1 px-3 py-1 bg-secondary text-secondary-foreground rounded-md text-sm"
                      >
                        <Hash className="w-3 h-3" />
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

                {/* Agregar nueva etiqueta */}
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

            {/* Prioridad */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Prioridad (1-10)
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={formData.prioridad || 5}
                  onChange={(e) => setFormData(prev => ({ ...prev, prioridad: parseInt(e.target.value) }))}
                  className="flex-1"
                />
                <div className="flex items-center gap-1 min-w-[3rem]">
                  <Star className={cn(
                    "w-4 h-4",
                    (formData.prioridad || 0) >= 8 ? "text-red-500" :
                    (formData.prioridad || 0) >= 5 ? "text-yellow-500" :
                    "text-green-500"
                  )} />
                  <span className="text-sm font-medium text-foreground">
                    {formData.prioridad || 5}
                  </span>
                </div>
              </div>
              {errors.prioridad && (
                <p className="mt-1 text-sm text-red-500">{errors.prioridad}</p>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-border bg-card/50">
          {errors.general && (
            <p className="text-sm text-red-500">{errors.general}</p>
          )}
          
          <div className="flex gap-3 ml-auto">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-border rounded-lg text-foreground hover:bg-background transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isSaving ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              {isSaving ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </div>

        {/* Shortcuts */}
        <div className="px-6 pb-4">
          <p className="text-xs text-muted-foreground">
            <kbd className="px-1 py-0.5 bg-secondary rounded text-xs">Ctrl+Enter</kbd> para guardar, 
            <kbd className="px-1 py-0.5 bg-secondary rounded text-xs ml-2">Esc</kbd> para cancelar
          </p>
        </div>
      </div>
    </div>
  );
} 