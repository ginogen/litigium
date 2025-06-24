import React, { useState, useEffect } from 'react';
import { cn } from '../../lib/utils';
import { googleDriveAPI, GoogleDriveFile, GoogleDriveBreadcrumb } from '../../lib/google-drive-api';
import { Folder, ChevronRight, Home, Plus, X, ArrowLeft, Check, Search } from 'lucide-react';

interface GoogleDriveFolderPickerProps {
  isOpen: boolean;
  onClose: () => void;
  onFolderSelect: (folderId: string | null, folderName: string) => void;
  title?: string;
}

export function GoogleDriveFolderPicker({ 
  isOpen, 
  onClose, 
  onFolderSelect, 
  title = "Seleccionar Carpeta de Google Drive" 
}: GoogleDriveFolderPickerProps) {
  const [folders, setFolders] = useState<GoogleDriveFile[]>([]);
  const [breadcrumb, setBreadcrumb] = useState<GoogleDriveBreadcrumb[]>([]);
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null);
  const [selectedFolderName, setSelectedFolderName] = useState<string>('');
  const [showNewFolderForm, setShowNewFolderForm] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  // Load folders when opening or navigating
  useEffect(() => {
    if (isOpen) {
      loadFolders(currentFolderId, searchQuery);
    }
  }, [isOpen, currentFolderId]);

  // Search with debounce
  useEffect(() => {
    if (!isOpen) return;
    
    const timeoutId = setTimeout(() => {
      setIsSearching(true);
      loadFolders(currentFolderId, searchQuery).finally(() => setIsSearching(false));
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, currentFolderId, isOpen]);

  const loadFolders = async (parentId: string | null, search?: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await googleDriveAPI.getFolders(parentId || undefined, search);
      setFolders(response.folders);
      setBreadcrumb(response.breadcrumb);
    } catch (error: any) {
      console.error('Error loading folders:', error);
      setError('Error cargando carpetas de Google Drive');
    } finally {
      setIsLoading(false);
    }
  };

  const navigateToFolder = (folderId: string | null) => {
    setCurrentFolderId(folderId);
    setSelectedFolderId(folderId);
    setSelectedFolderName(
      folderId === null ? 'Mi unidad' : 
      breadcrumb.find(b => b.id === folderId)?.name || 'Carpeta seleccionada'
    );
  };

  const handleFolderClick = (folder: GoogleDriveFile) => {
    navigateToFolder(folder.id);
  };

  const handleBreadcrumbClick = (breadcrumbItem: GoogleDriveBreadcrumb) => {
    navigateToFolder(breadcrumbItem.id === 'root' ? null : breadcrumbItem.id);
  };

  const handleSelectCurrent = () => {
    const folderName = currentFolderId === null ? 'Mi unidad' : 
      breadcrumb.find(b => b.id === currentFolderId)?.name || 'Carpeta seleccionada';
    
    onFolderSelect(currentFolderId, folderName);
    onClose();
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;
    
    setIsCreatingFolder(true);
    try {
      await googleDriveAPI.createFolder({
        folder_name: newFolderName.trim(),
        parent_folder_id: currentFolderId || undefined
      });
      
      // Reload folders to show the new one
      await loadFolders(currentFolderId, searchQuery);
      setNewFolderName('');
      setShowNewFolderForm(false);
    } catch (error: any) {
      console.error('Error creating folder:', error);
      setError('Error creando carpeta');
    } finally {
      setIsCreatingFolder(false);
    }
  };

  const handleClose = () => {
    setCurrentFolderId(null);
    setSelectedFolderId(null);
    setSelectedFolderName('');
    setShowNewFolderForm(false);
    setNewFolderName('');
    setSearchQuery('');
    setError(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {title}
          </h2>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Breadcrumb */}
        <div className="flex items-center gap-2 p-4 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
          <Home className="w-4 h-4 text-gray-500" />
          {breadcrumb.map((item, index) => (
            <React.Fragment key={item.id}>
              <button
                onClick={() => handleBreadcrumbClick(item)}
                className="text-sm text-blue-600 hover:text-blue-800 transition-colors"
              >
                {item.name}
              </button>
              {index < breadcrumb.length - 1 && (
                <ChevronRight className="w-4 h-4 text-gray-400" />
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Current folder selection */}
        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border-b border-blue-200 dark:border-blue-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Folder className="w-5 h-5 text-blue-600" />
              <div>
                <div className="font-medium text-blue-900 dark:text-blue-100">
                  Carpeta actual: {currentFolderId === null ? 'Mi unidad' : breadcrumb[breadcrumb.length - 1]?.name}
                </div>
                <div className="text-sm text-blue-700 dark:text-blue-300">
                  La demanda se guardará en esta carpeta
                </div>
              </div>
            </div>
            <button
              onClick={handleSelectCurrent}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Check className="w-4 h-4" />
              Seleccionar
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          )}

          {/* New folder form */}
          {showNewFolderForm && (
            <div className="mb-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h4 className="text-sm font-medium mb-2">Nueva Carpeta</h4>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  placeholder="Nombre de la carpeta"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleCreateFolder();
                    } else if (e.key === 'Escape') {
                      setShowNewFolderForm(false);
                      setNewFolderName('');
                    }
                  }}
                />
                <button
                  onClick={handleCreateFolder}
                  disabled={!newFolderName.trim() || isCreatingFolder}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isCreatingFolder ? 'Creando...' : 'Crear'}
                </button>
                <button
                  onClick={() => {
                    setShowNewFolderForm(false);
                    setNewFolderName('');
                  }}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}

          {/* Search bar */}
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Buscar carpetas..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              />
              {isSearching && (
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                </div>
              )}
            </div>
            {searchQuery && (
              <div className="mt-2 text-xs text-gray-600">
                Buscando "{searchQuery}" en {currentFolderId === null ? 'Mi unidad' : breadcrumb[breadcrumb.length - 1]?.name}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-2 mb-4">
            <button
              onClick={() => setShowNewFolderForm(true)}
              className="flex items-center gap-2 px-3 py-2 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Nueva Carpeta
            </button>
          </div>

          {/* Folders list */}
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="flex flex-col items-center gap-4">
                <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                <div className="text-sm text-gray-600">Cargando carpetas...</div>
              </div>
            </div>
          ) : folders.length === 0 ? (
            <div className="text-center py-12">
              <Folder className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <div className="text-gray-600">No hay carpetas en esta ubicación</div>
              <div className="text-sm text-gray-500 mt-1">
                Puedes crear una nueva carpeta o seleccionar la carpeta actual
              </div>
            </div>
          ) : (
            <div className="space-y-1">
              {folders.map((folder) => (
                <button
                  key={folder.id}
                  onClick={() => handleFolderClick(folder)}
                  className={cn(
                    "w-full flex items-center gap-3 p-3 rounded-lg transition-colors text-left",
                    "hover:bg-gray-100 dark:hover:bg-gray-700",
                    selectedFolderId === folder.id && "bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800"
                  )}
                >
                  <Folder className="w-5 h-5 text-blue-600 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900 dark:text-white truncate">
                      {folder.name}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {folder.modifiedTime ? (
                        <>
                          Modificado: {new Date(folder.modifiedTime).toLocaleDateString('es-ES', {
                            day: '2-digit',
                            month: 'short',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </>
                      ) : (
                        folder.createdTime && (
                          <>
                            Creado: {new Date(folder.createdTime).toLocaleDateString('es-ES', {
                              day: '2-digit',
                              month: 'short',
                              year: 'numeric'
                            })}
                          </>
                        )
                      )}
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {folders.length} carpeta{folders.length !== 1 ? 's' : ''} encontrada{folders.length !== 1 ? 's' : ''}
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleClose}
              className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Cancelar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
} 