import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { categoryAPI, Category, CategoryCreate, CategoryUpdate, CategoryStats } from '@/lib';
import { cn } from '@/lib/utils';
import { Plus, Edit, Trash2, Search, Folder, Users, FileText, Settings, Target, AlertCircle } from 'lucide-react';
import { CategorySkeleton } from '../ui/Skeleton';

interface CategoryManagerProps {
  onCategorySelect?: (category: Category | null) => void;
  selectedCategoryId?: string;
  showCreateButton?: boolean;
}

interface CategoryFormData {
  nombre: string;
  descripcion: string;
  color: string;
  icon: string;
}

export function CategoryManager({ onCategorySelect, selectedCategoryId, showCreateButton = true }: CategoryManagerProps) {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const [formData, setFormData] = useState<CategoryFormData>({
    nombre: '',
    descripcion: '',
    color: '#6366f1',
    icon: '📁'
  });

  const defaultIcons = ['📁', '⚖️', '📋', '🔒', '💼', '👨‍👩‍👧‍👦', '🏠', '💰', '📑', '⚡'];
  const defaultColors = [
    '#6366f1', // Indigo
    '#3b82f6', // Blue
    '#8b5cf6', // Purple
    '#ef4444', // Red
    '#10b981', // Green
    '#16a34a', // Green alternative
    '#ec4899', // Pink
    '#6b7280', // Gray
    '#84cc16', // Lime
    '#06b6d4'  // Cyan
  ];

  // Query para cargar categorías
  const categoriesQuery = useQuery({
    queryKey: ['categories', searchTerm],
    queryFn: async () => {
      const response = await categoryAPI.obtenerCategorias(searchTerm);
      if (!response.success) {
        throw new Error('Error obteniendo categorías');
      }
      return response.categories;
    },
    staleTime: 5 * 60 * 1000, // 5 minutos
    retry: 2,
    retryDelay: 1000,
  });

  // Query para estadísticas
  const statisticsQuery = useQuery({
    queryKey: ['category-statistics'],
    queryFn: async () => {
      const response = await categoryAPI.obtenerEstadisticasCategorias();
      if (!response.success) {
        throw new Error('Error obteniendo estadísticas');
      }
      return response.categories;
    },
    staleTime: 2 * 60 * 1000, // 2 minutos
    retry: 1,
  });

  // Mutation para crear categoría
  const createCategoryMutation = useMutation({
    mutationFn: async (data: CategoryFormData) => {
      const response = await categoryAPI.crearCategoria(data);
      if (!response.success) {
        throw new Error('Error creando categoría');
      }
      return response;
    },
    onSuccess: () => {
      showNotification('success', 'Categoría creada exitosamente');
      resetForm();
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      queryClient.invalidateQueries({ queryKey: ['category-statistics'] });
    },
    onError: (error: any) => {
      showNotification('error', error.response?.data?.detail || 'Error creando categoría');
    }
  });

  // Mutation para actualizar categoría
  const updateCategoryMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: CategoryFormData }) => {
      const response = await categoryAPI.actualizarCategoria(id, data);
      if (!response.success) {
        throw new Error('Error actualizando categoría');
      }
      return response;
    },
    onSuccess: () => {
      showNotification('success', 'Categoría actualizada exitosamente');
      resetForm();
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      queryClient.invalidateQueries({ queryKey: ['category-statistics'] });
    },
    onError: (error: any) => {
      showNotification('error', error.response?.data?.detail || 'Error actualizando categoría');
    }
  });

  // Mutation para eliminar categoría
  const deleteCategoryMutation = useMutation({
    mutationFn: async (categoryId: string) => {
      const response = await categoryAPI.eliminarCategoria(categoryId);
      if (!response.success) {
        throw new Error('Error eliminando categoría');
      }
      return response;
    },
    onSuccess: () => {
      showNotification('success', 'Categoría eliminada exitosamente');
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      queryClient.invalidateQueries({ queryKey: ['category-statistics'] });
    },
    onError: (error: any) => {
      showNotification('error', error.response?.data?.detail || 'Error eliminando categoría');
    }
  });

  // Mutation para crear categorías por defecto
  const createDefaultCategoriesMutation = useMutation({
    mutationFn: async () => {
      const response = await categoryAPI.crearCategoriasDefecto();
      if (!response.success) {
        throw new Error('Error creando categorías por defecto');
      }
      return response;
    },
    onSuccess: (response) => {
      showNotification('success', response.message);
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      queryClient.invalidateQueries({ queryKey: ['category-statistics'] });
    },
    onError: (error: any) => {
      showNotification('error', error.response?.data?.detail || 'Error creando categorías por defecto');
    }
  });

  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 3000);
  };

  const resetForm = () => {
    setFormData({
      nombre: '',
      descripcion: '',
      color: '#6366f1',
      icon: '📁'
    });
    setEditingCategory(null);
    setShowCreateForm(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.nombre.trim()) {
      showNotification('error', 'El nombre es requerido');
      return;
    }

    if (editingCategory) {
      updateCategoryMutation.mutate({ id: editingCategory.id, data: formData });
    } else {
      createCategoryMutation.mutate(formData);
    }
  };

  const handleEdit = (category: Category) => {
    setFormData({
      nombre: category.nombre,
      descripcion: category.descripcion || '',
      color: category.color,
      icon: category.icon
    });
    setEditingCategory(category);
    setShowCreateForm(true);
  };

  const handleDelete = async (categoryId: string) => {
    if (!confirm('¿Estás seguro de que quieres eliminar esta categoría?')) {
      return;
    }

    deleteCategoryMutation.mutate(categoryId);

    // Si era la categoría seleccionada, deseleccionar
    if (selectedCategoryId === categoryId && onCategorySelect) {
      onCategorySelect(null);
    }
  };

  const handleCreateDefault = async () => {
    createDefaultCategoriesMutation.mutate();
  };

  const getStatisticsForCategory = (categoryId: string) => {
    return statisticsQuery.data?.find(stat => stat.categoria_id === categoryId);
  };

  const categories = categoriesQuery.data || [];
  const isLoading = categoriesQuery.isLoading || createCategoryMutation.isPending || 
                   updateCategoryMutation.isPending || deleteCategoryMutation.isPending ||
                   createDefaultCategoriesMutation.isPending;

  // Refetch when search term changes
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      categoriesQuery.refetch();
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchTerm]);

  return (
    <div className="bg-card/50 border border-border rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Folder className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-semibold text-foreground">Gestión de Categorías</h2>
        </div>
        
        {showCreateButton && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleCreateDefault}
              disabled={isLoading}
              className="px-3 py-2 text-sm bg-secondary hover:bg-secondary/80 text-secondary-foreground rounded-lg transition-colors disabled:opacity-50"
            >
              Crear por defecto
            </button>
            <button
              onClick={() => setShowCreateForm(true)}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-100 rounded-lg transition-colors disabled:opacity-50"
            >
              <Plus className="w-4 h-4" />
              Nueva categoría
            </button>
          </div>
        )}
      </div>

      {/* Notificación */}
      {notification && (
        <div className={cn(
          "mb-4 p-3 rounded-lg border",
          notification.type === 'success' 
            ? "bg-green-50 border-green-200 text-green-800" 
            : "bg-red-50 border-red-200 text-red-800"
        )}>
          {notification.message}
        </div>
      )}

      {/* Búsqueda */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Buscar categorías..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
        />
      </div>

      {/* Lista de categorías */}
      <div className="space-y-3">
        {categoriesQuery.isLoading ? (
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, index) => (
              <CategorySkeleton key={index} />
            ))}
          </div>
        ) : categoriesQuery.error ? (
          <div className="text-center py-8">
            <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
            <p className="text-red-600 mb-4">Error cargando categorías</p>
            <button 
              onClick={() => categoriesQuery.refetch()}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
            >
              Reintentar
            </button>
          </div>
        ) : categories.length === 0 ? (
          <div className="text-center py-8">
            <Folder className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-muted-foreground mb-4">
              {searchTerm ? 'No se encontraron categorías' : 'No hay categorías creadas'}
            </p>
            {!searchTerm && (
              <button
                onClick={handleCreateDefault}
                disabled={isLoading}
                className="px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg transition-colors disabled:opacity-50"
              >
                Crear categorías por defecto
              </button>
            )}
          </div>
        ) : (
          categories.map((category) => {
            const stats = getStatisticsForCategory(category.id);
            const isSelected = selectedCategoryId === category.id;
            
            return (
              <div
                key={category.id}
                className={cn(
                  "p-4 border rounded-lg cursor-pointer transition-all hover:bg-card/80",
                  isSelected 
                    ? "border-primary bg-primary/5 shadow-sm" 
                    : "border-border bg-background"
                )}
                onClick={() => onCategorySelect?.(category)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <div 
                      className="w-10 h-10 rounded-lg flex items-center justify-center text-lg"
                      style={{ backgroundColor: `${category.color}20`, color: category.color }}
                    >
                      {category.icon}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <h3 
                        className="font-medium text-foreground mb-1 truncate"
                        style={{ color: isSelected ? category.color : undefined }}
                      >
                        {category.nombre}
                      </h3>
                      {category.descripcion && (
                        <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                          {category.descripcion}
                        </p>
                      )}
                      
                      {/* Estadísticas */}
                      {stats && (
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <FileText className="w-3 h-3" />
                            <span>{stats.total_documentos} docs</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Target className="w-3 h-3" />
                            <span>{stats.documentos_procesados} procesados</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            <span>{stats.total_anotaciones} anotaciones</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-1 ml-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEdit(category);
                      }}
                      disabled={isLoading}
                      className="p-2 text-muted-foreground hover:text-foreground hover:bg-background rounded-lg transition-colors disabled:opacity-50"
                      title="Editar categoría"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(category.id);
                      }}
                      disabled={isLoading}
                      className="p-2 text-muted-foreground hover:text-red-400 hover:bg-background rounded-lg transition-colors disabled:opacity-50"
                      title="Eliminar categoría"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Formulario de creación/edición */}
      {showCreateForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-background border border-border rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-foreground mb-4">
              {editingCategory ? 'Editar Categoría' : 'Nueva Categoría'}
            </h3>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Nombre *
                </label>
                <input
                  type="text"
                  value={formData.nombre}
                  onChange={(e) => setFormData(prev => ({ ...prev, nombre: e.target.value }))}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  placeholder="Nombre de la categoría"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Descripción
                </label>
                <textarea
                  value={formData.descripcion}
                  onChange={(e) => setFormData(prev => ({ ...prev, descripcion: e.target.value }))}
                  rows={3}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  placeholder="Descripción opcional..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Icono
                </label>
                <div className="grid grid-cols-5 gap-2">
                  {defaultIcons.map((icon) => (
                    <button
                      key={icon}
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, icon }))}
                      className={cn(
                        "p-2 text-lg border rounded-lg transition-colors",
                        formData.icon === icon 
                          ? "border-primary bg-primary/10" 
                          : "border-border hover:bg-card/50"
                      )}
                    >
                      {icon}
                    </button>
                  ))}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Color
                </label>
                <div className="grid grid-cols-5 gap-2">
                  {defaultColors.map((color) => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, color }))}
                      className={cn(
                        "w-8 h-8 rounded-lg border-2 transition-all",
                        formData.color === color 
                          ? "border-foreground scale-110" 
                          : "border-border hover:border-foreground/50"
                      )}
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
              </div>
              
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={resetForm}
                  className="flex-1 px-4 py-2 bg-secondary hover:bg-secondary/80 text-secondary-foreground rounded-lg transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="flex-1 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-100 rounded-lg transition-colors disabled:opacity-50"
                >
                  {editingCategory ? 'Actualizar' : 'Crear'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}