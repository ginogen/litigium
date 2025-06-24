import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cn } from '@/lib/utils';
import { 
  Cloud, 
  CheckCircle, 
  AlertCircle, 
  ExternalLink, 
  Loader2, 
  Unplug,
  RefreshCw,
  Shield,
  Calendar,
  Mail
} from 'lucide-react';
import { googleDriveAPI, ConnectionStatus, formatDate } from '@/lib/google-drive-api';

interface GoogleDriveConnectorProps {
  onConnectionChange?: (connected: boolean) => void;
}

export function GoogleDriveConnector({ onConnectionChange }: GoogleDriveConnectorProps) {
  const queryClient = useQueryClient();
  const [isConnecting, setIsConnecting] = useState(false);

  // Query para el estado de conexión
  const connectionQuery = useQuery({
    queryKey: ['google-drive-connection'],
    queryFn: async () => {
      const status = await googleDriveAPI.getConnectionStatus();
      console.log('📊 GoogleDriveConnector status:', status);
      return status;
    },
    staleTime: 2 * 60 * 1000, // 2 minutos
    retry: false, // Evitar loops de retry
    refetchOnWindowFocus: true,
  });

  // Mutation para iniciar conexión
  const connectMutation = useMutation({
    mutationFn: googleDriveAPI.initiateConnection,
    onSuccess: (authUrl) => {
      setIsConnecting(true);
      
      // Abrir ventana popup para OAuth
      const popup = window.open(
        authUrl, 
        'google-drive-auth', 
        'width=500,height=600,scrollbars=yes,resizable=yes'
      );

      // Monitorear el popup
      const checkClosed = setInterval(() => {
        if (popup?.closed) {
          clearInterval(checkClosed);
          setIsConnecting(false);
          
          // Invalidar query para refrescar estado
          setTimeout(() => {
            queryClient.invalidateQueries({ queryKey: ['google-drive-connection'] });
          }, 1000);
        }
      }, 1000);

      // Escuchar mensajes del popup
      const handleMessage = (event: MessageEvent) => {
        if (event.origin !== window.location.origin) return;
        
        if (event.data.type === 'google-drive-auth-success') {
          console.log('✅ Recibido mensaje de éxito desde popup');
          popup?.close();
          clearInterval(checkClosed);
          setIsConnecting(false);
          queryClient.invalidateQueries({ queryKey: ['google-drive-connection'] });
          window.removeEventListener('message', handleMessage);
        } else if (event.data.type === 'google-drive-auth-error') {
          console.error('❌ Error en autenticación:', event.data.error);
          popup?.close();
          clearInterval(checkClosed);
          setIsConnecting(false);
          window.removeEventListener('message', handleMessage);
        }
      };
      
      window.addEventListener('message', handleMessage);

      // Cleanup cuando el componente se desmonte
      return () => {
        clearInterval(checkClosed);
        window.removeEventListener('message', handleMessage);
        if (popup && !popup.closed) {
          popup.close();
        }
      };
    },
    onError: (error) => {
      setIsConnecting(false);
      console.error('Error connecting to Google Drive:', error);
    }
  });

  // Mutation para desconectar
  const disconnectMutation = useMutation({
    mutationFn: googleDriveAPI.disconnect,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['google-drive-connection'] });
      queryClient.removeQueries({ queryKey: ['google-drive-files'] }); // Limpiar caché de archivos
      onConnectionChange?.(false);
    }
  });

  // Efecto para notificar cambios de conexión
  useEffect(() => {
    if (connectionQuery.data) {
      onConnectionChange?.(connectionQuery.data.connected);
    }
  }, [connectionQuery.data, onConnectionChange]);

  const connectionStatus = connectionQuery.data;
  const isConnected = connectionStatus?.connected || false;

  return (
    <div className="bg-card border border-border rounded-lg p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={cn(
            "p-2 rounded-full",
            isConnected ? "bg-green-100 dark:bg-green-900/20" : "bg-blue-100 dark:bg-blue-900/20"
          )}>
            <Cloud className={cn(
              "w-6 h-6",
              isConnected ? "text-green-600 dark:text-green-400" : "text-blue-600 dark:text-blue-400"
            )} />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">Google Drive</h3>
            <p className="text-sm text-muted-foreground">
              Conecta tu Google Drive para importar documentos directamente
            </p>
          </div>
        </div>

        {/* Status Badge */}
        <div className={cn(
          "flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium",
          isConnected 
            ? "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400"
            : "bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400"
        )}>
          {isConnected ? (
            <>
              <CheckCircle className="w-4 h-4" />
              <span>Conectado</span>
            </>
          ) : (
            <>
              <AlertCircle className="w-4 h-4" />
              <span>No conectado</span>
            </>
          )}
        </div>
      </div>

      {/* Connection Details */}
      {isConnected && connectionStatus ? (
        <ConnectedView 
          connectionStatus={connectionStatus}
          onDisconnect={() => disconnectMutation.mutate()}
          isDisconnecting={disconnectMutation.isPending}
          queryClient={queryClient}
        />
      ) : (
        <DisconnectedView 
          onConnect={() => connectMutation.mutate()}
          isConnecting={isConnecting || connectMutation.isPending}
          error={connectMutation.error}
          queryClient={queryClient}
        />
      )}

      {/* Loading State */}
      {connectionQuery.isLoading && (
        <div className="flex items-center justify-center py-4">
          <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
          <span className="ml-2 text-sm text-muted-foreground">Verificando conexión...</span>
        </div>
      )}
    </div>
  );
}

function ConnectedView({ 
  connectionStatus, 
  onDisconnect, 
  isDisconnecting,
  queryClient
}: { 
  connectionStatus: ConnectionStatus;
  onDisconnect: () => void;
  isDisconnecting: boolean;
  queryClient: any;
}) {
  return (
    <div className="space-y-4">
      {/* Connection Info */}
      <div className="bg-muted/50 rounded-lg p-4 space-y-3">
        <div className="flex items-center space-x-2">
          <Mail className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-medium">Email:</span>
          <span className="text-sm text-muted-foreground">{connectionStatus.google_email}</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <Calendar className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-medium">Conectado:</span>
          <span className="text-sm text-muted-foreground">
            {formatDate(connectionStatus.connected_at)}
          </span>
        </div>

        {connectionStatus.last_sync_at && (
          <div className="flex items-center space-x-2">
            <RefreshCw className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium">Última sincronización:</span>
            <span className="text-sm text-muted-foreground">
              {formatDate(connectionStatus.last_sync_at)}
            </span>
          </div>
        )}

        {connectionStatus.needs_refresh && (
          <div className="flex items-center space-x-2 text-yellow-600 dark:text-yellow-400">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm font-medium">Token necesita renovación</span>
          </div>
        )}
      </div>

      {/* Benefits */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-foreground">Beneficios activos:</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-muted-foreground">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span>Conversión automática de .doc</span>
          </div>
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span>OCR automático en PDFs</span>
          </div>
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span>Google Docs → Word</span>
          </div>
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span>Importación directa</span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end space-x-3 pt-4 border-t">
        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ['google-drive-connection'] })}
          className={cn(
            "flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-md",
            "text-gray-700 bg-gray-50 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700",
            "border border-gray-200 dark:border-gray-600"
          )}
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refrescar</span>
        </button>
        
        <button
          onClick={onDisconnect}
          disabled={isDisconnecting}
          className={cn(
            "flex items-center space-x-2 px-4 py-2 text-sm font-medium rounded-md",
            "text-red-700 bg-red-50 hover:bg-red-100 dark:text-red-400 dark:bg-red-900/20 dark:hover:bg-red-900/30",
            "disabled:opacity-50 disabled:cursor-not-allowed"
          )}
        >
          {isDisconnecting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Unplug className="w-4 h-4" />
          )}
          <span>Desconectar</span>
        </button>
      </div>
    </div>
  );
}

function DisconnectedView({ 
  onConnect, 
  isConnecting, 
  error,
  queryClient
}: { 
  onConnect: () => void;
  isConnecting: boolean;
  error: any;
  queryClient: any;
}) {
  return (
    <div className="space-y-4">
      {/* Description */}
      <div className="text-sm text-muted-foreground space-y-2">
        <p>
          Conecta tu Google Drive para acceder directamente a tus documentos sin necesidad 
          de descargar y subir archivos.
        </p>
        
        {/* Features */}
        <div className="space-y-1">
          <p className="font-medium text-foreground">¿Qué podrás hacer?</p>
          <ul className="list-disc list-inside space-y-1 text-sm">
            <li>Explorar tus archivos de Google Drive</li>
            <li>Importar documentos directamente para entrenamiento</li>
            <li>Conversión automática de formatos problemáticos (.doc)</li>
            <li>OCR automático en PDFs escaneados</li>
            <li>Soporte para Google Docs, Sheets y más</li>
          </ul>
        </div>
      </div>

      {/* Security Note */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
        <div className="flex items-start space-x-2">
          <Shield className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium text-blue-900 dark:text-blue-200">Seguridad garantizada</p>
            <p className="text-blue-700 dark:text-blue-300">
              Solo solicitamos permisos de lectura. Tus documentos permanecen seguros en tu Google Drive.
            </p>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
          <div className="flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400 mt-0.5" />
            <div className="text-sm">
              <p className="font-medium text-red-900 dark:text-red-200">Error de conexión</p>
              <p className="text-red-700 dark:text-red-300">
                {error.message || 'No se pudo conectar con Google Drive'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Connect Button */}
      <div className="flex justify-center gap-3 pt-4 border-t">
        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ['google-drive-connection'] })}
          className={cn(
            "flex items-center space-x-2 px-4 py-2 text-sm font-medium rounded-md",
            "text-gray-700 bg-gray-100 hover:bg-gray-200 dark:text-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600",
            "border border-gray-300 dark:border-gray-600 transition-colors duration-200"
          )}
          title="Refrescar el estado de conexión"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refrescar estado</span>
        </button>
        
        <button
          onClick={onConnect}
          disabled={isConnecting}
          className={cn(
            "flex items-center space-x-2 px-6 py-3 text-sm font-medium rounded-md",
            "text-white bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            "transition-colors duration-200"
          )}
        >
          {isConnecting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <ExternalLink className="w-4 h-4" />
          )}
          <span>
            {isConnecting ? 'Conectando...' : 'Conectar Google Drive'}
          </span>
        </button>
      </div>
    </div>
  );
} 