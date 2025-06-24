import React, { useEffect, useState } from 'react';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import { googleDriveAPI } from '@/lib/google-drive-api';

export function GoogleCallback() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Extraer el código de autorización de la URL
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const error = urlParams.get('error');

        if (error) {
          throw new Error(`OAuth error: ${error}`);
        }

        if (!code) {
          throw new Error('No authorization code received');
        }

        // Completar la conexión
        await googleDriveAPI.completeConnection(code);
        
        setStatus('success');
        setMessage('¡Google Drive conectado exitosamente!');
        
        // Enviar mensaje al padre para cerrar popup
        if (window.opener) {
          window.opener.postMessage({
            type: 'google-drive-auth-success',
            success: true
          }, window.location.origin);
          
          // Cerrar ventana después de un momento
          setTimeout(() => {
            window.close();
          }, 2000);
        } else {
          // Si no es popup, redirigir a la sección de training
          setTimeout(() => {
            window.location.href = '/#training';
          }, 2000);
        }

      } catch (error) {
        console.error('Error in Google callback:', error);
        setStatus('error');
        setMessage(error instanceof Error ? error.message : 'Error desconocido');
        
        // Enviar mensaje de error al padre
        if (window.opener) {
          window.opener.postMessage({
            type: 'google-drive-auth-error',
            success: false,
            error: error instanceof Error ? error.message : 'Error desconocido'
          }, window.location.origin);
          
          setTimeout(() => {
            window.close();
          }, 3000);
        }
      }
    };

    handleCallback();
  }, []);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-lg p-8 max-w-md w-full text-center">
        {status === 'loading' && (
          <>
            <Loader2 className="w-12 h-12 animate-spin text-blue-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-foreground mb-2">
              Conectando Google Drive...
            </h2>
            <p className="text-muted-foreground">
              Por favor espera mientras completamos la conexión.
            </p>
          </>
        )}

        {status === 'success' && (
          <>
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-foreground mb-2">
              ¡Éxito!
            </h2>
            <p className="text-muted-foreground mb-4">
              {message}
            </p>
            <p className="text-sm text-muted-foreground">
              Esta ventana se cerrará automáticamente...
            </p>
          </>
        )}

        {status === 'error' && (
          <>
            <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-foreground mb-2">
              Error
            </h2>
            <p className="text-muted-foreground mb-4">
              {message}
            </p>
            <p className="text-sm text-muted-foreground">
              Esta ventana se cerrará automáticamente...
            </p>
          </>
        )}
      </div>
    </div>
  );
} 