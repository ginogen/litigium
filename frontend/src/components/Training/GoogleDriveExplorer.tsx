import React, { useState, useCallback, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cn } from '@/lib/utils';
import { 
  Search, 
  ChevronRight, 
  Home, 
  FolderOpen, 
  FileText, 
  Download, 
  CheckSquare, 
  Square, 
  Loader2,
  AlertCircle,
  CheckCircle,
  RefreshCw,
  Filter,
  Upload,
  ArrowLeft,
  Cloud
} from 'lucide-react';
import { 
  googleDriveAPI, 
  GoogleDriveFile, 
  GoogleDriveBreadcrumb,
  ImportFilesRequest,
  formatFileSize, 
  formatDate, 
  getFileTypeIcon,
  isFileSupported 
} from '@/lib/google-drive-api';

interface GoogleDriveExplorerProps {
  isConnected: boolean;
  selectedCategoryId: string;
  selectedTipoDemanda: string;
  onImportComplete?: (results: any[]) => void;
  compact?: boolean;
}

export function GoogleDriveExplorer({ 
  isConnected, 
  selectedCategoryId, 
  selectedTipoDemanda,
  onImportComplete,
  compact = false
}: GoogleDriveExplorerProps) {
  const queryClient = useQueryClient();
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<GoogleDriveFile[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showOnlySupported, setShowOnlySupported] = useState(true);

  // Query para archivos de la carpeta actual
  const filesQuery = useQuery({
    queryKey: ['google-drive-files', currentFolderId, searchQuery],
    queryFn: () => googleDriveAPI.listFiles({
      folderId: currentFolderId || undefined,
      search: searchQuery || undefined,
      pageSize: 100
    }),
    enabled: isConnected,
    staleTime: 30 * 1000, // 30 segundos
    retry: 2,
  });

  // Mutation para importar archivos
  const importMutation = useMutation({
    mutationFn: async (request: ImportFilesRequest) => {
      const results = await googleDriveAPI.importMultipleFiles(request);
      return results;
    },
    onSuccess: (results) => {
      setSelectedFiles([]);
      onImportComplete?.(results);
      
      // Mostrar resultados
      const successful = results.filter(r => r.success).length;
      const failed = results.filter(r => !r.success).length;
      
      if (successful > 0 && failed === 0) {
        // Todo exitoso
        console.log(`✅ ${successful} archivo(s) importado(s) exitosamente`);
      } else if (successful > 0) {
        // Parcialmente exitoso
        console.log(`✅ ${successful} importados, ❌ ${failed} fallaron`);
      } else {
        // Todo falló
        console.log(`❌ Error importando ${failed} archivo(s)`);
      }
    }
  });

  // Archivos filtrados
  const filteredFiles = useMemo(() => {
    if (!filesQuery.data?.files) return [];
    
    let files = filesQuery.data.files;
    
    if (showOnlySupported) {
      files = files.filter(file => file.isFolder || file.isSupported);
    }
    
    return files;
  }, [filesQuery.data?.files, showOnlySupported]);

  // Archivos y carpetas separados
  const { folders, documents } = useMemo(() => {
    const folders = filteredFiles.filter(file => file.isFolder);
    const documents = filteredFiles.filter(file => !file.isFolder);
    
    return { folders, documents };
  }, [filteredFiles]);

  // Handlers
  const handleFileSelect = useCallback((file: GoogleDriveFile) => {
    if (file.isFolder) {
      setCurrentFolderId(file.id);
      setSelectedFiles([]);
      return;
    }

    if (!file.isSupported) return;

    setSelectedFiles(prev => {
      const isSelected = prev.some(f => f.id === file.id);
      if (isSelected) {
        return prev.filter(f => f.id !== file.id);
      } else {
        return [...prev, file];
      }
    });
  }, []);

  const handleSelectAll = useCallback(() => {
    const supportedDocs = documents.filter(file => file.isSupported);
    const allSelected = supportedDocs.every(file => 
      selectedFiles.some(selected => selected.id === file.id)
    );

    if (allSelected) {
      setSelectedFiles([]);
    } else {
      setSelectedFiles(supportedDocs);
    }
  }, [documents, selectedFiles]);

  const handleImport = useCallback(() => {
    if (selectedFiles.length === 0 || !selectedCategoryId || !selectedTipoDemanda) return;

    importMutation.mutate({
      files: selectedFiles,
      categoriaId: selectedCategoryId,
      tipoDemanda: selectedTipoDemanda
    });
  }, [selectedFiles, selectedCategoryId, selectedTipoDemanda, importMutation]);

  const handleBreadcrumbClick = useCallback((folderId: string) => {
    setCurrentFolderId(folderId === 'root' ? null : folderId);
    setSelectedFiles([]);
  }, []);

  const canImport = selectedFiles.length > 0 && selectedCategoryId && selectedTipoDemanda;

  if (!isConnected) {
    return (
      <div className="text-center py-8 text-gray-400">
        <Cloud className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>Conecta tu Google Drive para explorar archivos</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Search bar - Sticky positioning */}
      <div className="sticky top-0 z-10 bg-gray-800 border-b border-gray-600 shrink-0">
        <div className="flex gap-2 p-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar archivos..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm border border-gray-600 rounded-md bg-gray-700 text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div className="flex items-center gap-2">
            {/* Filtro de archivos compatibles */}
            <label className="flex items-center space-x-2 text-sm text-gray-300 whitespace-nowrap">
              <input
                type="checkbox"
                checked={showOnlySupported}
                onChange={(e) => setShowOnlySupported(e.target.checked)}
                className="rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500"
              />
              <span>Solo compatibles</span>
            </label>
            
            <button
              onClick={() => filesQuery.refetch()}
              disabled={filesQuery.isRefetching}
              className="p-2 text-gray-400 hover:text-gray-200 disabled:opacity-50 rounded-md hover:bg-gray-700"
              title="Actualizar archivos"
            >
              <RefreshCw className={cn("w-4 h-4", filesQuery.isRefetching && "animate-spin")} />
            </button>
          </div>
        </div>
      </div>

      {/* Contenido scrolleable */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 space-y-4">
          {/* Breadcrumb */}
          {filesQuery.data?.breadcrumb && filesQuery.data.breadcrumb.length > 1 && (
            <div className="flex items-center space-x-2 text-sm text-gray-400">
              {filesQuery.data.breadcrumb.map((item, index) => (
                <React.Fragment key={item.id}>
                  {index > 0 && <ChevronRight className="w-4 h-4" />}
                  <button
                    onClick={() => handleBreadcrumbClick(item.id)}
                    className="hover:text-gray-200 transition-colors"
                  >
                    {index === 0 ? <Home className="w-4 h-4" /> : item.name}
                  </button>
                </React.Fragment>
              ))}
            </div>
          )}

          {/* Botón de retroceso para carpetas */}
          {currentFolderId && (
            <button
              onClick={() => setCurrentFolderId(null)}
              className="flex items-center space-x-2 text-sm text-gray-400 hover:text-gray-200"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Volver a Mi unidad</span>
            </button>
          )}

          {/* Loading state */}
          {filesQuery.isLoading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              <span className="ml-2 text-gray-400">Cargando archivos...</span>
            </div>
          )}

          {/* Error state */}
          {filesQuery.error && (
            <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-5 h-5 text-red-400" />
                <p className="text-red-200">
                  Error cargando archivos: {(filesQuery.error as Error).message}
                </p>
              </div>
            </div>
          )}

          {/* Files list */}
          {filesQuery.data && (
            <>
              {/* Actions bar */}
              {documents.length > 0 && (
                <div className="flex items-center justify-between bg-gray-800/50 rounded-lg p-3">
                  <div className="flex items-center space-x-4">
                    <button
                      onClick={handleSelectAll}
                      className="flex items-center space-x-2 text-sm text-gray-400 hover:text-gray-200"
                    >
                      {documents.filter(f => f.isSupported).every(file => 
                        selectedFiles.some(selected => selected.id === file.id)
                      ) ? (
                        <CheckSquare className="w-4 h-4" />
                      ) : (
                        <Square className="w-4 h-4" />
                      )}
                      <span>Seleccionar todos</span>
                    </button>

                    {selectedFiles.length > 0 && (
                      <span className="text-sm text-gray-400">
                        {selectedFiles.length} archivo(s) seleccionado(s)
                      </span>
                    )}
                  </div>

                  {canImport && (
                    <button
                      onClick={handleImport}
                      disabled={importMutation.isPending}
                      className={cn(
                        "flex items-center space-x-2 px-4 py-2 text-sm font-medium rounded-md",
                        "text-white bg-gray-700 hover:bg-gray-600 border border-gray-600",
                        "disabled:opacity-50 disabled:cursor-not-allowed"
                      )}
                    >
                      {importMutation.isPending ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Upload className="w-4 h-4" />
                      )}
                      <span>
                        {importMutation.isPending 
                          ? `Importando ${selectedFiles.length} archivo(s)...`
                          : `Importar ${selectedFiles.length} archivo(s)`
                        }
                      </span>
                    </button>
                  )}
                </div>
              )}

              {/* Files grid */}
              <div className="space-y-2">
                {/* Folders first */}
                {folders.map(folder => (
                  <FileItem
                    key={folder.id}
                    file={folder}
                    isSelected={false}
                    onSelect={handleFileSelect}
                    selectable={false}
                  />
                ))}

                {/* Then documents */}
                {documents.map(file => (
                  <FileItem
                    key={file.id}
                    file={file}
                    isSelected={selectedFiles.some(f => f.id === file.id)}
                    onSelect={handleFileSelect}
                    selectable={file.isSupported}
                  />
                ))}
              </div>

              {/* Empty state */}
              {filteredFiles.length === 0 && (
                <div className="text-center py-8 text-gray-400">
                  <FolderOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>
                    {searchQuery 
                      ? `No se encontraron archivos para "${searchQuery}"`
                      : "Esta carpeta está vacía"
                    }
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

interface FileItemProps {
  file: GoogleDriveFile;
  isSelected: boolean;
  onSelect: (file: GoogleDriveFile) => void;
  selectable: boolean;
}

function FileItem({ file, isSelected, onSelect, selectable }: FileItemProps) {
  const icon = getFileTypeIcon(file.mimeType);

  return (
    <div
      onClick={() => onSelect(file)}
      className={cn(
        "flex items-center space-x-3 p-3 border border-gray-600 rounded-lg transition-colors cursor-pointer",
        "hover:bg-gray-700/50",
        isSelected && "bg-gray-700/70 border-gray-500",
        !file.isSupported && !file.isFolder && "opacity-60",
        !selectable && !file.isFolder && "cursor-default"
      )}
    >
      {/* Selection checkbox (only for selectable files) */}
      {selectable && !file.isFolder && (
        <div className="flex-shrink-0">
          {isSelected ? (
            <CheckSquare className="w-5 h-5 text-gray-200" />
          ) : (
            <Square className="w-5 h-5 text-gray-400" />
          )}
        </div>
      )}

      {/* File icon */}
      <div className="flex-shrink-0 text-lg">
        {file.isFolder ? (
          <FolderOpen className="w-5 h-5 text-blue-400" />
        ) : (
          <span>{icon}</span>
        )}
      </div>

      {/* File info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center space-x-2">
          <p className="text-sm font-medium text-gray-100 truncate">
            {file.name}
          </p>
          
          {file.needsConversion && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-900/40 text-blue-300 border border-blue-700">
              Se convertirá
            </span>
          )}
          
          {!file.isSupported && !file.isFolder && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-800/40 text-gray-400 border border-gray-600">
              No compatible
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-4 text-xs text-gray-400 mt-1">
          <span>{formatFileSize(file.size)}</span>
          <span>{formatDate(file.modifiedTime)}</span>
        </div>
      </div>

      {/* Arrow for folders */}
      {file.isFolder && (
        <ChevronRight className="w-4 h-4 text-gray-400" />
      )}
    </div>
  );
} 