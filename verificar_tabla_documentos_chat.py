#!/usr/bin/env python3
"""
Script para verificar y crear la tabla documentos_chat en Supabase.
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def verificar_tabla_documentos_chat():
    """Verifica y crea la tabla documentos_chat si no existe."""
    
    try:
        from supabase import create_client, Client
        
        # Configuración de Supabase
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            print("❌ Error: Faltan las variables de entorno SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY")
            return False
        
        # Crear cliente de Supabase admin
        supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        print("🔍 Verificando tabla documentos_chat...")
        
        # Verificar si la tabla existe
        try:
            # Intentar hacer una consulta simple
            response = supabase_admin.table('documentos_chat').select('count', count='exact').limit(1).execute()
            print("✅ Tabla documentos_chat ya existe")
            return True
        except Exception as e:
            if "relation" in str(e).lower() and "does not exist" in str(e).lower():
                print("⚠️ Tabla documentos_chat no existe, creándola...")
                
                # SQL para crear la tabla
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS documentos_chat (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    abogado_id UUID NOT NULL REFERENCES abogados(id) ON DELETE CASCADE,
                    archivo_url TEXT NOT NULL,
                    nombre_archivo TEXT NOT NULL,
                    tipo_documento TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    tamaño_bytes INTEGER NOT NULL,
                    texto_extraido TEXT,
                    datos_estructurados JSONB,
                    metadatos_ocr JSONB,
                    procesado BOOLEAN DEFAULT FALSE,
                    fecha_procesamiento TIMESTAMP WITH TIME ZONE,
                    error_procesamiento TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                
                -- Crear índices para mejorar rendimiento
                CREATE INDEX IF NOT EXISTS idx_documentos_chat_session_id ON documentos_chat(session_id);
                CREATE INDEX IF NOT EXISTS idx_documentos_chat_abogado_id ON documentos_chat(abogado_id);
                CREATE INDEX IF NOT EXISTS idx_documentos_chat_procesado ON documentos_chat(procesado);
                CREATE INDEX IF NOT EXISTS idx_documentos_chat_created_at ON documentos_chat(created_at);
                
                -- Crear función para actualizar updated_at automáticamente
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
                
                -- Crear trigger para actualizar updated_at
                DROP TRIGGER IF EXISTS update_documentos_chat_updated_at ON documentos_chat;
                CREATE TRIGGER update_documentos_chat_updated_at
                    BEFORE UPDATE ON documentos_chat
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
                """
                
                # Ejecutar SQL
                try:
                    # Nota: En Supabase, las tablas se crean desde el dashboard SQL Editor
                    # Este script solo verifica la existencia
                    print("📝 Para crear la tabla, ejecuta el siguiente SQL en el SQL Editor de Supabase:")
                    print("=" * 80)
                    print(create_table_sql)
                    print("=" * 80)
                    
                    print("💡 Instrucciones:")
                    print("1. Ve al dashboard de Supabase")
                    print("2. Abre el SQL Editor")
                    print("3. Copia y pega el SQL de arriba")
                    print("4. Ejecuta el script")
                    print("5. Vuelve a ejecutar este script para verificar")
                    
                    return False
                    
                except Exception as create_error:
                    print(f"❌ Error creando tabla: {create_error}")
                    return False
            else:
                print(f"❌ Error verificando tabla: {e}")
                return False
        
    except ImportError as e:
        print(f"❌ Error: No se pudo importar supabase: {e}")
        print("💡 Instala las dependencias con: pip install supabase==2.3.4")
        return False
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

if __name__ == "__main__":
    success = verificar_tabla_documentos_chat()
    if success:
        print("\n🎉 Verificación completada exitosamente!")
    else:
        print("\n⚠️ Verificación completada con advertencias.")
        sys.exit(1) 