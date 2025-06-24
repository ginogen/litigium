import React, { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './contexts/AuthContext.tsx';
import { ChatProvider } from './contexts/ChatContext.tsx';
import { ChatStorageProvider } from './contexts/ChatStorageContext.tsx';
import { CanvasProvider } from './contexts/CanvasContext.tsx';
import { TextSelectionProvider } from './contexts/TextSelectionContext.tsx';
import { ChatContainer } from './components/Chat/ChatContainer.tsx';
import { Sidebar } from './components/Sidebar/Sidebar.tsx';
import { CanvasPanel } from './components/Canvas/CanvasPanel.tsx';
import { AuthForm } from './components/Auth/AuthForm.tsx';
import { TrainingSection } from './components/Training/TrainingSection.tsx';
import { ProfileSection } from './components/Profile/ProfileSection.tsx';
import { GoogleCallback } from './components/Auth/GoogleCallback.tsx';
import { useCanvas } from './contexts/CanvasContext.tsx';
import { Loader2 } from 'lucide-react';

// Configurar QueryClient con configuraciones optimizadas
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Configuraciones por defecto para todas las queries
      staleTime: 5 * 60 * 1000, // 5 minutos
      gcTime: 10 * 60 * 1000, // 10 minutos (antes era cacheTime)
      retry: (failureCount: number, error: any) => {
        // Solo reintentar errores de red, no errores del servidor
        if (failureCount >= 3) return false;
        if (error?.response?.status >= 400 && error?.response?.status < 500) return false;
        return error?.message?.includes('timeout') || error?.message?.includes('network') || !error?.response;
      },
      retryDelay: (attemptIndex: number) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: false, // No refetch automático al cambiar de ventana
      refetchOnReconnect: true, // Sí refetch al reconectar
    },
    mutations: {
      retry: false, // No reintentar mutations por defecto
    },
  },
});

// Función para obtener la ruta actual
function getCurrentRoute(): string {
  if (typeof window === 'undefined') return '/';
  return window.location.pathname;
}

// Tipo para las secciones
export type AppSection = 'chats' | 'training' | 'profile';

// Componente interno que usa los contexts
function AppContent() {
  const { state: canvasState } = useCanvas();
  const { isAuthenticated, isLoading } = useAuth();
  
  // Estado para la sección activa
  const [activeSection, setActiveSection] = useState<AppSection>(() => {
    // Detectar sección inicial desde el hash
    if (typeof window !== 'undefined') {
      const hash = window.location.hash.slice(1); // Remover #
      if (hash === 'training' || hash === 'profile') {
        return hash as AppSection;
      }
    }
    return 'chats';
  });
  
  // Estado inicial basado en el tamaño de la pantalla
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    // En desktop (lg y superior) la sidebar empieza abierta
    if (typeof window !== 'undefined') {
      return window.innerWidth >= 1024;
    }
    return true;
  });

  // Verificar si estamos en la ruta del callback de Google
  const currentRoute = getCurrentRoute();
  const isGoogleCallback = currentRoute === '/auth/google/callback';

  // Si estamos en el callback de Google, mostrar el componente especial
  if (isGoogleCallback) {
    return <GoogleCallback />;
  }

  // NO inicializar automáticamente - solo cuando el usuario haga clic en "Nueva consulta"
  // useEffect(() => {
  //   if (isAuthenticated && activeSection === 'chats') {
  //     initialize().catch(console.error);
  //   }
  // }, [initialize, isAuthenticated, activeSection]);

  // Manejar cambios de tamaño de ventana
  useEffect(() => {
    const handleResize = () => {
      // En móvil, cerrar la sidebar automáticamente
      if (window.innerWidth < 1024 && sidebarOpen) {
        setSidebarOpen(false);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [sidebarOpen]);

  // Auto-colapsar sidebar cuando se abra Canvas
  useEffect(() => {
    if (canvasState.isOpen && sidebarOpen) {
      setSidebarOpen(false);
    }
  }, [canvasState.isOpen, sidebarOpen]);

  // Escuchar cambios en el hash para navegación
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1);
      if (hash === 'training' || hash === 'profile' || hash === 'chats') {
        setActiveSection(hash as AppSection);
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

  // Función para cambiar de sección
  const handleSectionChange = (section: AppSection) => {
    // Si cambiamos de sección, logear para debug
    if (section !== activeSection) {
      console.log(`🔄 Cambiando de sección: ${activeSection} → ${section}`);
      
      // Reset global de estados que podrían estar colgados
      // Esto ayuda a evitar que estados de loading de una sección
      // se mantengan activos al cambiar a otra sección
      setTimeout(() => {
        // Dispatch de un evento global para que los componentes
        // puedan escuchar y resetear sus estados si es necesario
        const resetEvent = new CustomEvent('sectionChange', { 
          detail: { from: activeSection, to: section } 
        });
        window.dispatchEvent(resetEvent);
      }, 100);
    }
    
    setActiveSection(section);
    
    // En móvil, cerrar la sidebar al cambiar de sección
    if (window.innerWidth < 1024) {
      setSidebarOpen(false);
    }
  };

  // Mostrar loading mientras se verifica la autenticación
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-background">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Cargando...</p>
        </div>
      </div>
    );
  }

  // Mostrar formulario de autenticación si no está autenticado
  if (!isAuthenticated) {
    return <AuthForm />;
  }

  // Función para renderizar la sección activa
  const renderActiveSection = () => {
    switch (activeSection) {
      case 'chats':
        return (
          <div className={`flex-1 flex overflow-hidden ${canvasState.isOpen ? 'w-1/2' : 'w-full'}`}>
            <div className="flex-1">
              <ChatContainer />
            </div>
            {canvasState.isOpen && <CanvasPanel />}
          </div>
        );
      case 'training':
        return (
          <div className="flex-1 overflow-hidden">
            <TrainingSection />
          </div>
        );
      case 'profile':
        return (
          <div className="flex-1 overflow-hidden">
            <ProfileSection />
          </div>
        );
      default:
        return null;
    }
  };

  // Mostrar la aplicación principal si está autenticado
  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar */}
      <Sidebar 
        isOpen={sidebarOpen} 
        onToggle={toggleSidebar}
        activeSection={activeSection}
        onSectionChange={handleSectionChange}
      />

      {/* Main content area */}
      {renderActiveSection()}
    </div>
  );
}

// Componente principal con providers
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ChatStorageProvider>
          <ChatProvider>
            <CanvasProvider>
              <TextSelectionProvider>
                <AppContent />
              </TextSelectionProvider>
            </CanvasProvider>
          </ChatProvider>
        </ChatStorageProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
