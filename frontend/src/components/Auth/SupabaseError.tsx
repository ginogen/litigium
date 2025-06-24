import React from 'react';
import { AlertTriangle, ExternalLink } from 'lucide-react';

export function SupabaseError() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-md">
        <div className="bg-card border border-border rounded-lg shadow-lg p-8">
          {/* Header */}
          <div className="text-center mb-6">
            <AlertTriangle className="w-12 h-12 text-destructive mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-foreground mb-2">
              Configuración Requerida
            </h1>
            <p className="text-sm text-muted-foreground">
              Necesitas configurar Supabase para usar la aplicación
            </p>
          </div>

          {/* Instructions */}
          <div className="space-y-4">
            <div className="bg-destructive/10 border border-destructive/20 rounded-md p-4">
              <h3 className="text-sm font-medium text-destructive mb-2">
                Paso 1: Crear archivo .env
              </h3>
              <p className="text-xs text-muted-foreground mb-2">
                Crea un archivo <code className="bg-background/50 px-1 rounded">.env</code> en la carpeta <code className="bg-background/50 px-1 rounded">frontend/</code>
              </p>
              <div className="bg-background/50 p-3 rounded text-xs font-mono">
                <div>VITE_SUPABASE_URL=https://tu-proyecto.supabase.co</div>
                <div>VITE_SUPABASE_ANON_KEY=tu_clave_anonima</div>
              </div>
            </div>

            <div className="bg-blue-500/10 border border-blue-500/20 rounded-md p-4">
              <h3 className="text-sm font-medium text-blue-400 mb-2">
                Paso 2: Obtener credenciales
              </h3>
              <p className="text-xs text-muted-foreground mb-3">
                Ve a tu proyecto de Supabase → Settings → API
              </p>
              <a
                href="https://supabase.com/dashboard"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-xs text-blue-400 hover:text-blue-300 transition-colors"
              >
                <ExternalLink className="w-3 h-3" />
                Abrir Dashboard de Supabase
              </a>
            </div>

            <div className="bg-green-500/10 border border-green-500/20 rounded-md p-4">
              <h3 className="text-sm font-medium text-green-400 mb-2">
                Paso 3: Reiniciar servidor
              </h3>
              <p className="text-xs text-muted-foreground">
                Después de crear el archivo .env, reinicia el servidor de desarrollo:
              </p>
              <div className="bg-background/50 p-2 rounded text-xs font-mono mt-2">
                npm run dev
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="mt-6 pt-4 border-t border-border">
            <p className="text-xs text-muted-foreground text-center">
              ¿Necesitas ayuda? Consulta la{' '}
              <a
                href="https://supabase.com/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:text-primary/80 transition-colors"
              >
                documentación de Supabase
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
} 