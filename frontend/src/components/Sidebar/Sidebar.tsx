import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useChat } from '../../contexts/ChatContext';
import { useAuth } from '../../contexts/AuthContext';
import { useChatStorage, ChatFolder, ChatSession } from '../../contexts/ChatStorageContext';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronRight, Plus, FolderOpen, Folder, MessageSquare, Upload, User, Menu, X, FileText, Calendar, LogOut, Pencil, Trash2, FolderPlus, MoreVertical, Move, Check, Square, CheckSquare } from 'lucide-react';
import { SidebarSkeleton } from '../ui/Skeleton';
import type { AppSection } from '../../App';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  activeSection: AppSection;
  onSectionChange: (section: AppSection) => void;
}

interface ChatFolderUI {
  id: string;
  name: string;
  isOpen: boolean;
  chats: ChatItem[];
}

interface ChatItem {
  id: string;
  session_id: string;
  title: string;
  date: string;
  preview: string;
}

export function Sidebar({ isOpen, onToggle, activeSection, onSectionChange }: SidebarProps) {
  const { clear, initialize, loadMessages, state } = useChat();
  const { profile, signOut } = useAuth();
  const { getFolders, getSessions, createSession, updateSession, deleteSession, deleteSessionsBulk, moveSession, createFolder, deleteFolder } = useChatStorage();
  const [folders, setFolders] = useState<ChatFolder[]>([]);
  const [sessions, setSessions] = useState<{ [folderId: string]: ChatItem[] }>({});
  const [unassignedSessions, setUnassignedSessions] = useState<ChatItem[]>([]);
  const [openFolders, setOpenFolders] = useState<Set<string>>(new Set(['unassigned']));
  const [isLoading, setIsLoading] = useState(false);
  const [editingSession, setEditingSession] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  
  // Estados para modales y menús
  const [showCreateFolderModal, setShowCreateFolderModal] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [newFolderColor, setNewFolderColor] = useState('#3B82F6');
  
  // Estados para menús contextuales
  const [activeContextMenu, setActiveContextMenu] = useState<{type: 'session' | 'folder', id: string} | null>(null);
  const [showMoveModal, setShowMoveModal] = useState<{sessionId: string, currentFolderId?: string} | null>(null);
  
  // Estados para selección múltiple
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedSessions, setSelectedSessions] = useState<Set<string>>(new Set());
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);

  const queryClient = useQueryClient();

  // Query para cargar carpetas
  const foldersQuery = useQuery({
    queryKey: ['folders', profile?.id],
    queryFn: async () => {
      if (!profile?.id) return [];
      
      console.log('🔍 Cargando carpetas...');
      const folders = await getFolders();
      console.log(`📁 Carpetas cargadas: ${folders.length}`);
      return folders;
    },
    enabled: !!profile?.id,
    staleTime: 3 * 60 * 1000, // 3 minutos
    retry: 2,
    retryDelay: 1000,
  });

  // Query para cargar sesiones
  const sessionsQuery = useQuery({
    queryKey: ['sessions', profile?.id],
    queryFn: async () => {
      if (!profile?.id) return [];
      
      console.log('💬 Cargando sesiones...');
      const sessions = await getSessions();
      console.log(`💬 Sesiones cargadas: ${sessions.length}`);
      
      return sessions;
    },
    enabled: !!profile?.id,
    staleTime: 1 * 60 * 1000, // 1 minuto para sesiones
    retry: 2,
    retryDelay: 1000,
  });

  // Mutation para crear carpeta
  const createFolderMutation = useMutation({
    mutationFn: async (folderData: { name: string; color?: string }) => {
      if (!profile?.id) throw new Error('Usuario no autenticado');
      return await createFolder(folderData.name, folderData.color);
    },
    onSuccess: () => {
      setNewFolderName('');
      setShowCreateFolderModal(false);
      queryClient.invalidateQueries({ queryKey: ['folders'] });
    },
    onError: (error) => {
      console.error('Error creating folder:', error);
      alert('Error creando carpeta. Intenta de nuevo.');
    }
  });

  // Mutation para eliminar carpeta
  const deleteFolderMutation = useMutation({
    mutationFn: async (folderId: string) => {
      return await deleteFolder(folderId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['folders'] });
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    },
    onError: (error) => {
      console.error('Error deleting folder:', error);
      alert('Error eliminando carpeta. Intenta de nuevo.');
    }
  });

  // Mutation para crear sesión
  const createSessionMutation = useMutation({
    mutationFn: async (folderId?: string) => {
      return await createSession('Nueva conversación', folderId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      queryClient.invalidateQueries({ queryKey: ['folders'] });
    },
    onError: (error) => {
      console.error('Error creating session:', error);
      alert('Error creando nueva conversación. Intenta de nuevo.');
    }
  });

  // Mutation para eliminar sesión
  const deleteSessionMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      return await deleteSession(sessionId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      queryClient.invalidateQueries({ queryKey: ['folders'] });
    },
    onError: (error) => {
      console.error('Error deleting session:', error);
      alert('Error eliminando conversación. Intenta de nuevo.');
    }
  });

  // Cargar datos al montar el componente y cuando cambie la sección
  useEffect(() => {
    let isMounted = true;
    
    if (activeSection === 'chats' || isOpen) {
      loadFoldersAndSessions();
    }
    
    // Cleanup function para evitar race conditions
    return () => {
      isMounted = false;
      setIsLoading(false);
    };
  }, [activeSection, isOpen]);

  const loadFoldersAndSessions = async () => {
    setIsLoading(true);
    try {
      console.log('🔍 Cargando carpetas y sesiones...');
      
      // Cargar todas las carpetas
      const foldersData = await getFolders();
      console.log('📁 Carpetas encontradas:', foldersData.length);
      setFolders(foldersData);

      // Cargar todas las sesiones (sin filtro de carpeta)
      const allSessions = await getSessions();
      console.log('💬 Total de sesiones encontradas:', allSessions.length);

      // Separar sesiones por carpetas y sin asignar
      const sessionsData: { [folderId: string]: ChatItem[] } = {};
      const unassigned: ChatItem[] = [];

      // Inicializar arrays para cada carpeta
      foldersData.forEach(folder => {
        sessionsData[folder.id] = [];
      });

      // Distribuir sesiones
      allSessions.forEach(session => {
        const chatItem: ChatItem = {
          id: session.id,
          session_id: session.session_id,
          title: session.titulo || 'Nueva consulta',
          date: formatRelativeDate(session.updated_at),
          preview: session.hechos_adicionales || session.cliente_nombre || 'Nueva consulta'
        };

        if (session.carpeta_id && sessionsData[session.carpeta_id]) {
          sessionsData[session.carpeta_id].push(chatItem);
        } else {
          unassigned.push(chatItem);
        }
      });

      console.log('📊 Distribución de sesiones:');
      console.log('- Sin asignar:', unassigned.length);
      foldersData.forEach(folder => {
        console.log(`- ${folder.nombre}:`, sessionsData[folder.id]?.length || 0);
      });

      setSessions(sessionsData);
      setUnassignedSessions(unassigned);
    } catch (error) {
      console.error('❌ Error loading folders and sessions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatRelativeDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Ahora';
    if (diffInHours < 24) return `${diffInHours}h`;
    if (diffInHours < 48) return 'Ayer';
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d`;
    return `${Math.floor(diffInHours / 168)}sem`;
  };

  const toggleFolder = (folderId: string) => {
    setOpenFolders(prev => {
      const newSet = new Set(prev);
      if (newSet.has(folderId)) {
        newSet.delete(folderId);
      } else {
        newSet.add(folderId);
      }
      return newSet;
    });
  };

  const handleNewChat = async () => {
    try {
      console.log('🆕 Verificando requisitos para nueva consulta...');
      
      // Importar API de verificación
      const { chatAPI } = await import('@/lib/api');
      
      // Verificar si hay categorías disponibles
      const verificacion = await chatAPI.verificarCategorias();
      console.log('📊 Verificación de categorías:', verificacion);
      
      if (!verificacion.puede_crear_conversacion) {
        // Mostrar modal explicativo
        const mensaje = verificacion.total_categorias === 0 
          ? '🚫 **No puedes crear conversaciones aún**\n\n**Primero necesitas:**\n\n1️⃣ **Crear categorías** en "Entrenar" → "Gestionar Categorías"\n2️⃣ **Subir documentos** para entrenar el sistema\n3️⃣ **Procesar los documentos** (se hace automáticamente)\n\n**¿Quieres ir a Entrenar ahora?**'
          : `🚫 **No puedes crear conversaciones aún**\n\n**Tienes ${verificacion.total_categorias} categorías pero ninguna tiene documentos procesados:**\n\n• Ve a "Entrenar" → "Subir Documentos"\n• Sube archivos .doc, .pdf o .txt\n• Espera a que se procesen automáticamente\n\n**¿Quieres ir a Entrenar ahora?**`;
        
        if (confirm(mensaje)) {
          onSectionChange('training');
        }
        return;
      }
      
      // Si todo está bien, proceder con la conversación
      console.log('✅ Requisitos cumplidos, iniciando nueva consulta...');
      console.log(`📋 Categorías disponibles: ${verificacion.categorias_disponibles.map(c => c.nombre).join(', ')}`);
      
      // Limpiar chat actual para empezar limpio
      clear();
      onSectionChange('chats');
      
      // NO inicializar automáticamente - esperar a que el usuario escriba
      console.log('✅ Listo para nueva consulta (se iniciará cuando el usuario escriba)');
    } catch (error) {
      console.error('❌ Error verificando requisitos:', error);
      alert('Error verificando los requisitos para crear conversación. Intenta más tarde.');
    }
  };

  const handleSelectChat = async (sessionId: string) => {
    try {
      console.log('📖 Cargando conversación:', sessionId);
      
      // Indicar visualmente que se está cargando esta conversación
      // (El estado de loading se maneja en el contexto)
      
      // Cargar mensajes de la conversación seleccionada
      await loadMessages(sessionId);
      onSectionChange('chats');
      
      // En móvil, cerrar la sidebar
      if (window.innerWidth < 1024) {
        onToggle();
      }
    } catch (error) {
      console.error('❌ Error loading chat:', error);
    }
  };

  const handleEditTitle = async (sessionId: string, newTitle: string) => {
    try {
      await updateSession(sessionId, { titulo: newTitle });
      setEditingSession(null);
      setEditingTitle('');
      await loadFoldersAndSessions();
    } catch (error) {
      console.error('❌ Error updating title:', error);
    }
  };

  const startEditingTitle = (sessionId: string, currentTitle: string) => {
    setEditingSession(sessionId);
    setEditingTitle(currentTitle);
  };

  const cancelEditingTitle = () => {
    setEditingSession(null);
    setEditingTitle('');
  };

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (error) {
      console.error('❌ Error signing out:', error);
    }
  };

  // Funciones para gestión de carpetas
  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;
    
    try {
      await createFolder(newFolderName.trim(), newFolderColor);
      setNewFolderName('');
      setNewFolderColor('#3B82F6');
      setShowCreateFolderModal(false);
      await loadFoldersAndSessions();
    } catch (error) {
      console.error('❌ Error creating folder:', error);
    }
  };

  const handleDeleteFolder = async (folderId: string) => {
    if (!confirm('¿Estás seguro de que quieres eliminar esta carpeta? Las conversaciones se moverán a "Recientes".')) {
      return;
    }
    
    try {
      await deleteFolder(folderId);
      await loadFoldersAndSessions();
    } catch (error) {
      console.error('❌ Error deleting folder:', error);
    }
  };

  // Funciones para gestión de conversaciones
  const handleDeleteSession = async (sessionId: string) => {
    if (!confirm('¿Estás seguro de que quieres eliminar esta conversación? Esta acción no se puede deshacer.')) {
      return;
    }
    
    try {
      await deleteSession(sessionId);
      await loadFoldersAndSessions();
    } catch (error) {
      console.error('❌ Error deleting session:', error);
    }
  };

  const handleMoveSession = async (sessionId: string, targetFolderId: string | null) => {
    try {
      await moveSession(sessionId, targetFolderId);
      setShowMoveModal(null);
      await loadFoldersAndSessions();
    } catch (error) {
      console.error('❌ Error moving session:', error);
    }
  };

  const colores = [
    '#3B82F6', '#EF4444', '#10B981', '#F59E0B', 
    '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'
  ];

  // Funciones para selección múltiple
  const toggleSelectionMode = () => {
    setSelectionMode(!selectionMode);
    setSelectedSessions(new Set());
  };

  const toggleSessionSelection = (sessionId: string) => {
    const newSelected = new Set(selectedSessions);
    if (newSelected.has(sessionId)) {
      newSelected.delete(sessionId);
    } else {
      newSelected.add(sessionId);
    }
    setSelectedSessions(newSelected);
  };

  const selectAllSessions = () => {
    const allSessionIds = new Set<string>();
    
    // Agregar sesiones sin asignar
    unassignedSessions.forEach(session => {
      allSessionIds.add(session.session_id);
    });
    
    // Agregar sesiones de carpetas
    Object.values(sessions).forEach(folderSessions => {
      folderSessions.forEach(session => {
        allSessionIds.add(session.session_id);
      });
    });
    
    setSelectedSessions(allSessionIds);
  };

  const deselectAllSessions = () => {
    setSelectedSessions(new Set());
  };

  const handleBulkDelete = async () => {
    if (selectedSessions.size === 0) return;
    
    try {
      console.log(`🗑️ Eliminando ${selectedSessions.size} conversaciones...`);
      
      // Usar eliminación masiva optimizada
      await deleteSessionsBulk(Array.from(selectedSessions));
      
      // Limpiar selección y salir del modo selección
      setSelectedSessions(new Set());
      setSelectionMode(false);
      setShowBulkDeleteConfirm(false);
      
      // Recargar datos
      await loadFoldersAndSessions();
      
      console.log(`✅ ${selectedSessions.size} conversaciones eliminadas exitosamente`);
    } catch (error) {
      console.error('❌ Error en eliminación masiva:', error);
    }
  };

  const getTotalSelectedCount = () => selectedSessions.size;
  const getAllSessionsCount = () => {
    return unassignedSessions.length + Object.values(sessions).reduce((total, folderSessions) => total + folderSessions.length, 0);
  };

  const renderChatItem = (chat: ChatItem) => {
    const isSelected = selectedSessions.has(chat.session_id);
    const isActiveChat = state.sessionId === chat.session_id;
    const isLoadingThis = state.isLoadingMessages && isActiveChat;
    
    // Truncar el preview muy agresivamente para evitar scroll horizontal
    const truncatedPreview = chat.preview.length > 25 ? chat.preview.substring(0, 25) + '...' : chat.preview;
    
    return (
      <div key={chat.id} className="group relative">
        <div className="flex items-center gap-2">
          {/* Checkbox para selección múltiple */}
          {selectionMode && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleSessionSelection(chat.session_id);
              }}
              className="p-1 rounded hover:bg-gray-600 transition-colors flex-shrink-0"
              title={isSelected ? "Deseleccionar" : "Seleccionar"}
            >
              {isSelected ? (
                <CheckSquare className="w-4 h-4 text-purple-400" />
              ) : (
                <Square className="w-4 h-4 text-gray-400" />
              )}
            </button>
          )}
          
          <div
            onClick={() => selectionMode ? toggleSessionSelection(chat.session_id) : handleSelectChat(chat.session_id)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                selectionMode ? toggleSessionSelection(chat.session_id) : handleSelectChat(chat.session_id);
              }
            }}
            role="button"
            tabIndex={0}
            className={cn(
              "flex items-start gap-2 flex-1 px-2 py-2 rounded-md transition-colors text-left cursor-pointer",
              isSelected && selectionMode 
                ? "bg-purple-500/20 border border-purple-500/40" 
                : isActiveChat
                ? "bg-blue-500/15 border-l-2 border-blue-400"
                : "hover:bg-gray-500/10",
              isLoadingThis && "animate-pulse bg-blue-500/25"
            )}
          >
            <MessageSquare className={cn(
              "w-3.5 h-3.5 mt-0.5 flex-shrink-0",
              isActiveChat ? "text-blue-400" : "text-gray-500"
            )} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                {editingSession === chat.id ? (
                  <input
                    type="text"
                    value={editingTitle}
                    onChange={(e) => setEditingTitle(e.target.value)}
                    onBlur={() => handleEditTitle(chat.id, editingTitle)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleEditTitle(chat.id, editingTitle);
                      } else if (e.key === 'Escape') {
                        cancelEditingTitle();
                      }
                    }}
                    className="text-xs text-gray-200 bg-gray-700 px-1 py-0.5 rounded border-none outline-none focus:ring-1 focus:ring-purple-500 flex-1"
                    autoFocus
                    onClick={(e) => e.stopPropagation()}
                  />
                ) : (
                  <div className="flex items-center flex-1 min-w-0 group/title">
                    <span className={cn(
                      "text-xs truncate flex-1 font-medium",
                      isActiveChat ? "text-blue-200" : "text-gray-200"
                    )}>
                      {chat.title}
                    </span>
                    {!selectionMode && (
                      <div className="flex items-center gap-1 opacity-0 group-hover/title:opacity-100 transition-opacity ml-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            startEditingTitle(chat.id, chat.title);
                          }}
                          className="p-0.5 rounded hover:bg-gray-600 transition-colors"
                          title="Editar nombre"
                        >
                          <Pencil className="w-2.5 h-2.5 text-gray-400 hover:text-gray-200" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setShowMoveModal({sessionId: chat.session_id});
                          }}
                          className="p-0.5 rounded hover:bg-gray-600 transition-colors"
                          title="Mover a carpeta"
                        >
                          <Move className="w-2.5 h-2.5 text-gray-400 hover:text-gray-200" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteSession(chat.session_id);
                          }}
                          className="p-0.5 rounded hover:bg-red-600 transition-colors"
                          title="Eliminar conversación"
                        >
                          <Trash2 className="w-2.5 h-2.5 text-gray-400 hover:text-red-200" />
                        </button>
                      </div>
                    )}
                  </div>
                )}
                <span className="text-xs text-gray-500 ml-1 flex-shrink-0">{chat.date}</span>
              </div>
              <p className={cn(
                "text-xs mt-0.5 truncate",
                isActiveChat ? "text-gray-400" : "text-gray-500"
              )}>
                {truncatedPreview}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <>
      {/* Overlay para móvil */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div className={cn(
        "fixed lg:relative flex flex-col transition-all duration-300 h-full z-50",
        isOpen ? "w-[280px]" : "w-0 lg:w-[60px]"
      )}
      style={{ backgroundColor: '#181818' }}>
        {isOpen ? (
          <div className="flex flex-col h-full">
            {/* Header */}
            <div className="border-b border-gray-700 p-4">
              <div className="flex items-center justify-between">
                <h1 className="text-xl font-bold text-purple-400">
                  LITIGIUM
                </h1>
                <div className="flex items-center gap-2">
                  <button
                    onClick={onToggle}
                    className="p-1.5 hover:bg-gray-700 rounded-md transition-colors"
                  >
                    <Menu className="w-5 h-5 text-gray-400 hover:text-white" />
                  </button>
                  <button
                    onClick={onToggle}
                    className="p-1.5 hover:bg-gray-700 rounded-md transition-colors lg:hidden"
                  >
                    <X className="w-5 h-5 text-gray-400" />
                  </button>
                </div>
              </div>
            </div>

            {/* Navegación principal */}
            <div className="flex flex-col">
              {/* Perfil */}
              <button
                onClick={() => onSectionChange('profile')}
                className={cn(
                  "flex items-center gap-3 w-full px-4 py-3 text-sm font-medium transition-colors border-b border-gray-700/50",
                  activeSection === 'profile' 
                    ? "bg-gray-800 text-gray-100" 
                    : "text-gray-300 hover:text-gray-100 hover:bg-gray-700/30"
                )}
              >
                <User className="w-4 h-4" />
                Perfil
              </button>

              {/* Entrenar */}
              <button
                onClick={() => onSectionChange('training')}
                className={cn(
                  "flex items-center gap-3 w-full px-4 py-3 text-sm font-medium transition-colors border-b border-gray-700",
                  activeSection === 'training' 
                    ? "bg-gray-800 text-gray-100" 
                    : "text-gray-300 hover:text-gray-100 hover:bg-gray-700/30"
                )}
              >
                <Upload className="w-4 h-4" />
                Entrenar
              </button>
            </div>

            {/* Sección de Chats */}
            <div className="flex-1 flex flex-col min-h-0">
              <div className="p-3 border-b border-gray-700/50">
                <button
                  onClick={() => onSectionChange('chats')}
                  className={cn(
                    "flex items-center gap-2 text-sm font-medium text-gray-300 hover:text-white transition-colors",
                    activeSection === 'chats' && "text-white"
                  )}
                >
                  <MessageSquare className="w-4 h-4" />
                  Conversaciones
                </button>
              </div>

              {/* Contenido de chats */}
              <div className="flex-1 flex flex-col min-h-0">
                {/* Botones de acción */}
                <div className="p-3 space-y-2">
                  <button
                    onClick={handleNewChat}
                    className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg border border-white/20 hover:bg-gray-500/10 transition-colors text-sm text-white group"
                  >
                    <Plus className="w-4 h-4 group-hover:rotate-90 transition-transform" />
                    Nueva consulta
                  </button>
                  
                  <button
                    onClick={() => setShowCreateFolderModal(true)}
                    className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg border border-purple-500/20 hover:bg-purple-500/10 transition-colors text-sm text-purple-300 group"
                  >
                    <FolderPlus className="w-4 h-4 group-hover:scale-110 transition-transform" />
                    Nueva carpeta
                  </button>
                </div>

                {/* Barra de herramientas para selección múltiple */}
                <div className="px-3 pb-3">
                  {!selectionMode ? (
                    <button
                      onClick={toggleSelectionMode}
                      className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg border border-orange-500/20 hover:bg-orange-500/10 transition-colors text-sm text-orange-300 group"
                      disabled={getAllSessionsCount() === 0}
                    >
                      <CheckSquare className="w-4 h-4 group-hover:scale-110 transition-transform" />
                      Seleccionar conversaciones
                    </button>
                  ) : (
                    <div className="space-y-2">
                      {/* Contador y acciones */}
                      <div className="flex items-center justify-between text-sm text-gray-300 bg-purple-500/10 px-3 py-2 rounded-lg border border-purple-500/20">
                        <span>
                          {getTotalSelectedCount()} de {getAllSessionsCount()} seleccionadas
                        </span>
                      </div>
                      
                      {/* Botones de acción masiva */}
                      <div className="flex gap-2">
                        <button
                          onClick={selectAllSessions}
                          className="flex-1 px-3 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded-lg transition-colors"
                          disabled={getTotalSelectedCount() === getAllSessionsCount()}
                        >
                          Todas
                        </button>
                        <button
                          onClick={deselectAllSessions}
                          className="flex-1 px-3 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded-lg transition-colors"
                          disabled={getTotalSelectedCount() === 0}
                        >
                          Ninguna
                        </button>
                      </div>
                      
                      {/* Botones principales */}
                      <div className="flex gap-2">
                        <button
                          onClick={toggleSelectionMode}
                          className="flex-1 px-3 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded-lg transition-colors"
                        >
                          Cancelar
                        </button>
                        <button
                          onClick={() => setShowBulkDeleteConfirm(true)}
                          disabled={getTotalSelectedCount() === 0}
                          className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white text-sm rounded-lg transition-colors"
                        >
                          Eliminar ({getTotalSelectedCount()})
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Lista de conversaciones */}
                <div className="flex-1 overflow-y-auto px-3 pb-3">
                  {/* Loading state con skeleton */}
                  {isLoading ? (
                    <SidebarSkeleton />
                  ) : (
                    <>
                  {/* Conversaciones sin asignar */}
                  {unassignedSessions.length > 0 && (
                    <div className="mb-2">
                      <button
                        onClick={() => toggleFolder('unassigned')}
                        className="flex items-center gap-2 w-full px-2 py-2 rounded-md hover:bg-gray-500/10 transition-colors text-sm text-gray-300 group"
                      >
                        {openFolders.has('unassigned') ? (
                          <>
                            <ChevronDown className="w-4 h-4 text-gray-500" />
                            <FolderOpen className="w-4 h-4 text-gray-400" />
                          </>
                        ) : (
                          <>
                            <ChevronRight className="w-4 h-4 text-gray-500" />
                            <Folder className="w-4 h-4 text-gray-400" />
                          </>
                        )}
                        <span className="flex-1 text-left font-medium">Recientes</span>
                        <span className="text-xs text-gray-500">{unassignedSessions.length}</span>
                      </button>

                      {openFolders.has('unassigned') && (
                        <div className="ml-6 mt-1 space-y-1">
                          {unassignedSessions.map(renderChatItem)}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Carpetas con sesiones */}
                  {folders.map(folder => {
                    const folderSessions = sessions[folder.id] || [];
                    const isOpen = openFolders.has(folder.id);
                    
                    return (
                      <div key={folder.id} className="mb-2">
                        <div className="flex items-center group/folder">
                          <button
                            onClick={() => toggleFolder(folder.id)}
                            className="flex items-center gap-2 flex-1 px-2 py-2 rounded-md hover:bg-gray-500/10 transition-colors text-sm text-gray-300"
                          >
                            {isOpen ? (
                              <>
                                <ChevronDown className="w-4 h-4 text-gray-500" />
                                <FolderOpen className="w-4 h-4 text-gray-400" />
                              </>
                            ) : (
                              <>
                                <ChevronRight className="w-4 h-4 text-gray-500" />
                                <Folder className="w-4 h-4 text-gray-400" />
                              </>
                            )}
                            <span className="flex-1 text-left font-medium" style={{ color: folder.color }}>{folder.nombre}</span>
                            <span className="text-xs text-gray-500">{folderSessions.length}</span>
                          </button>
                          
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteFolder(folder.id);
                            }}
                            className="p-1 rounded hover:bg-red-600 transition-colors opacity-0 group-hover/folder:opacity-100"
                            title="Eliminar carpeta"
                          >
                            <Trash2 className="w-3 h-3 text-gray-400 hover:text-red-200" />
                          </button>
                        </div>

                        {isOpen && (
                          <div className="ml-6 mt-1 space-y-1">
                            {folderSessions.length > 0 ? (
                              folderSessions.map(renderChatItem)
                            ) : (
                              <div className="text-xs text-gray-500 px-2 py-1">
                                No hay conversaciones
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}

                    {/* Mensaje si no hay conversaciones */}
                    {!isLoading && unassignedSessions.length === 0 && folders.every(f => (sessions[f.id] || []).length === 0) && (
                      <div className="text-center py-8 text-gray-500 text-sm">
                        <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        No hay conversaciones aún
                        <br />
                        <span className="text-xs">Crea una nueva consulta para empezar</span>
                      </div>
                    )}
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="border-t border-gray-700 p-3">
              <div className="flex items-center gap-3 text-sm text-gray-400 mb-3">
                <Calendar className="w-4 h-4" />
                <span>{new Date().toLocaleDateString('es-ES', { 
                  weekday: 'long', 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}</span>
              </div>
              
              {/* Botón de cerrar sesión */}
              <button
                onClick={handleSignOut}
                className="w-full flex items-center justify-center gap-2 py-2 px-3 bg-red-600 hover:bg-red-700 text-white font-medium rounded-md transition-colors text-sm"
              >
                <LogOut className="w-4 h-4" />
                Cerrar sesión
              </button>
            </div>
          </div>
        ) : (
          /* Sidebar colapsada - solo iconos */
          <div className="hidden lg:flex flex-col h-full items-center justify-start py-4 w-full">
            <div className="flex flex-col items-center w-full">
              <button
                onClick={onToggle}
                className="p-3 hover:bg-gray-700 rounded-md transition-colors mb-6 flex items-center justify-center"
              >
                <Menu className="w-5 h-5 text-gray-400" />
              </button>

              <div className="space-y-4 flex flex-col items-center w-full">
                <button
                  onClick={() => { onSectionChange('profile'); onToggle(); }}
                  className={cn(
                    "w-10 h-10 rounded-md transition-colors flex items-center justify-center",
                    activeSection === 'profile' 
                      ? "bg-gray-800 text-gray-100" 
                      : "text-gray-400 hover:text-gray-100 hover:bg-gray-700"
                  )}
                  title="Perfil"
                >
                  <User className="w-5 h-5" />
                </button>

                <button
                  onClick={() => { onSectionChange('training'); onToggle(); }}
                  className={cn(
                    "w-10 h-10 rounded-md transition-colors flex items-center justify-center",
                    activeSection === 'training' 
                      ? "bg-gray-800 text-gray-100" 
                      : "text-gray-400 hover:text-gray-100 hover:bg-gray-700"
                  )}
                  title="Entrenamiento"
                >
                  <Upload className="w-5 h-5" />
                </button>

                <button
                  onClick={() => { onSectionChange('chats'); onToggle(); }}
                  className={cn(
                    "w-10 h-10 rounded-md transition-colors flex items-center justify-center",
                    activeSection === 'chats' 
                      ? "bg-gray-700 text-white" 
                      : "text-gray-400 hover:text-white hover:bg-gray-700"
                  )}
                  title="Conversaciones"
                >
                  <MessageSquare className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Botón flotante para móvil */}
      <button
        onClick={onToggle}
        className={cn(
          "fixed top-4 left-4 z-40 p-2 bg-gray-800 rounded-md shadow-lg lg:hidden",
          "hover:bg-gray-700 transition-colors",
          isOpen && "hidden"
        )}
      >
        <Menu className="w-5 h-5 text-white" />
      </button>

      {/* Modal para crear carpeta */}
      {showCreateFolderModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-white mb-4">Nueva Carpeta</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Nombre de la carpeta
                </label>
                <input
                  type="text"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="Ej: Casos Laborales"
                  autoFocus
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Color
                </label>
                <div className="flex gap-2">
                  {colores.map((color) => (
                    <button
                      key={color}
                      onClick={() => setNewFolderColor(color)}
                      className={cn(
                        "w-8 h-8 rounded-full border-2 transition-all",
                        newFolderColor === color 
                          ? "border-white scale-110" 
                          : "border-gray-600 hover:border-gray-400"
                      )}
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateFolderModal(false);
                  setNewFolderName('');
                  setNewFolderColor('#3B82F6');
                }}
                className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleCreateFolder}
                disabled={!newFolderName.trim()}
                className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-md transition-colors"
              >
                Crear
              </button>
            </div>
          </div>
        </div>
      )}

             {/* Modal para mover conversación */}
       {showMoveModal && (
         <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
           <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
             <h3 className="text-lg font-semibold text-white mb-4">Mover Conversación</h3>
             
             <div className="space-y-2 max-h-60 overflow-y-auto">
               <button
                 onClick={() => handleMoveSession(showMoveModal.sessionId, null)}
                 className="w-full text-left px-3 py-2 rounded-md hover:bg-gray-700 transition-colors text-gray-300"
               >
                 <div className="flex items-center gap-2">
                   <FolderOpen className="w-4 h-4 text-gray-400" />
                   <span>Recientes (sin carpeta)</span>
                 </div>
               </button>
               
               {folders.map((folder) => (
                 <button
                   key={folder.id}
                   onClick={() => handleMoveSession(showMoveModal.sessionId, folder.id)}
                   className="w-full text-left px-3 py-2 rounded-md hover:bg-gray-700 transition-colors text-gray-300"
                 >
                   <div className="flex items-center gap-2">
                     <Folder className="w-4 h-4" style={{ color: folder.color }} />
                     <span>{folder.nombre}</span>
                   </div>
                 </button>
               ))}
             </div>
             
             <div className="flex gap-3 mt-6">
               <button
                 onClick={() => setShowMoveModal(null)}
                 className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
               >
                 Cancelar
               </button>
             </div>
           </div>
         </div>
       )}

       {/* Modal de confirmación para eliminación masiva */}
       {showBulkDeleteConfirm && (
         <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
           <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
             <div className="flex items-center gap-3 mb-4">
               <div className="p-2 bg-red-500/20 rounded-full">
                 <Trash2 className="w-6 h-6 text-red-400" />
               </div>
               <div>
                 <h3 className="text-lg font-semibold text-white">Eliminar Conversaciones</h3>
                 <p className="text-sm text-gray-400">Esta acción no se puede deshacer</p>
               </div>
             </div>
             
             <div className="bg-gray-700/50 rounded-lg p-4 mb-6">
               <p className="text-gray-300 text-sm mb-2">
                 Estás a punto de eliminar <strong className="text-white">{getTotalSelectedCount()}</strong> conversaciones:
               </p>
               
               <div className="max-h-32 overflow-y-auto space-y-1">
                 {Array.from(selectedSessions).slice(0, 5).map((sessionId) => {
                   // Buscar el título de la sesión
                   let sessionTitle = 'Conversación';
                   const allSessions = [...unassignedSessions, ...Object.values(sessions).flat()];
                   const session = allSessions.find(s => s.session_id === sessionId);
                   if (session) {
                     sessionTitle = session.title;
                   }
                   
                   return (
                     <div key={sessionId} className="text-xs text-gray-400 flex items-center gap-2">
                       <MessageSquare className="w-3 h-3 flex-shrink-0" />
                       <span className="truncate">{sessionTitle}</span>
                     </div>
                   );
                 })}
                 
                 {getTotalSelectedCount() > 5 && (
                   <div className="text-xs text-gray-500 italic">
                     ... y {getTotalSelectedCount() - 5} más
                   </div>
                 )}
               </div>
             </div>
             
             <div className="flex gap-3">
               <button
                 onClick={() => setShowBulkDeleteConfirm(false)}
                 className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
               >
                 Cancelar
               </button>
               <button
                 onClick={handleBulkDelete}
                 className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors font-medium"
               >
                 Eliminar {getTotalSelectedCount()}
               </button>
             </div>
           </div>
         </div>
       )}
    </>
  );
} 