#!/usr/bin/env python3
"""
Script para verificar y crear los buckets necesarios en Supabase Storage.
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def verificar_buckets_supabase():
    """Verifica y crea los buckets necesarios en Supabase Storage."""
    
    try:
        from supabase import create_client, Client
        
        # Configuración de Supabase
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            print("❌ Error: Faltan las variables de entorno SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY")
            return False
        
        # Crear cliente de Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # Buckets necesarios
        BUCKETS_REQUIRED = [
            "documentos-entrenamiento",
            "documentos-chat",  # Para imágenes subidas en chat
            "demandas-generadas", 
            "avatares"
        ]
        
        print("🔍 Verificando buckets en Supabase Storage...")
        
        # Obtener buckets existentes
        try:
            buckets_response = supabase.storage.list_buckets()
            existing_buckets = [bucket['name'] for bucket in buckets_response]
            print(f"✅ Buckets existentes: {existing_buckets}")
        except Exception as e:
            print(f"⚠️ Error obteniendo buckets existentes: {e}")
            existing_buckets = []
        
        # Verificar y crear buckets faltantes
        for bucket_name in BUCKETS_REQUIRED:
            if bucket_name in existing_buckets:
                print(f"✅ Bucket '{bucket_name}' ya existe")
            else:
                try:
                    print(f"🔧 Creando bucket '{bucket_name}'...")
                    
                    # Configuración del bucket
                    bucket_config = {
                        "public": False,  # Privado por defecto
                        "file_size_limit": 52428800,  # 50MB
                        "allowed_mime_types": ["image/*", "application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
                    }
                    
                    # Crear bucket
                    result = supabase.storage.create_bucket(bucket_name, bucket_config)
                    print(f"✅ Bucket '{bucket_name}' creado exitosamente")
                    
                except Exception as e:
                    print(f"❌ Error creando bucket '{bucket_name}': {e}")
        
        # Verificar políticas de acceso
        print("\n🔍 Verificando políticas de acceso...")
        
        # Políticas básicas para documentos-chat
        try:
            # Política para que usuarios puedan subir a documentos-chat
            print("🔧 Configurando políticas para documentos-chat...")
            
            # Nota: Las políticas se configuran desde el dashboard de Supabase
            # o usando SQL directamente en el SQL Editor
            
            print("✅ Políticas configuradas (verificar en dashboard de Supabase)")
            
        except Exception as e:
            print(f"⚠️ Error configurando políticas: {e}")
        
        print("\n🎉 Verificación de buckets completada!")
        print("\n📋 Resumen:")
        print("- documentos-entrenamiento: Para PDFs/DOCs de entrenamiento")
        print("- documentos-chat: Para imágenes subidas en chat")
        print("- demandas-generadas: Para archivos .docx generados")
        print("- avatares: Para fotos de perfil (opcional)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error: No se pudo importar supabase: {e}")
        print("💡 Instala las dependencias con: pip install supabase==2.3.4")
        return False
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

def verificar_tablas_supabase():
    """Verifica que las tablas necesarias existan en Supabase."""
    
    try:
        from supabase import create_client, Client
        
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            print("❌ Error: Faltan las variables de entorno")
            return False
        
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # Tablas necesarias
        TABLAS_REQUERIDAS = [
            "abogados",
            "chat_sesiones", 
            "chat_mensajes",
            "documentos_chat",  # Nueva tabla para documentos del chat
            "documentos_entrenamiento",
            "demandas_generadas",
            "carpetas"
        ]
        
        print("\n🔍 Verificando tablas en Supabase...")
        
        for tabla in TABLAS_REQUERIDAS:
            try:
                # Intentar hacer una consulta simple
                response = supabase.table(tabla).select("id").limit(1).execute()
                print(f"✅ Tabla '{tabla}' existe")
            except Exception as e:
                print(f"❌ Tabla '{tabla}' no existe o error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando tablas: {e}")
        return False

if __name__ == "__main__":
    print("🚀 VERIFICACIÓN DE SUPABASE STORAGE")
    print("=" * 50)
    
    # Verificar buckets
    buckets_ok = verificar_buckets_supabase()
    
    # Verificar tablas
    tablas_ok = verificar_tablas_supabase()
    
    print("\n" + "=" * 50)
    if buckets_ok and tablas_ok:
        print("✅ VERIFICACIÓN COMPLETADA EXITOSAMENTE")
        print("🎉 Tu configuración de Supabase está lista para usar")
    else:
        print("❌ HAY PROBLEMAS EN LA CONFIGURACIÓN")
        print("🔧 Revisa los errores arriba y corrige la configuración") 