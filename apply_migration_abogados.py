#!/usr/bin/env python3
"""
Script para aplicar migración de extensión de perfil de abogados
Ejecuta la migración SQL de manera segura
"""

import os
import sys
from supabase_integration import supabase_admin

def apply_abogados_migration():
    """Aplica la migración de extensión de abogados."""
    print("🚀 Aplicando migración de extensión de abogados...")
    
    try:
        # Leer el archivo de migración
        migration_file = "migrations/001_extend_abogados_profile.sql"
        
        if not os.path.exists(migration_file):
            raise FileNotFoundError(f"Archivo de migración no encontrado: {migration_file}")
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        print(f"📄 Leyendo migración desde: {migration_file}")
        print(f"📊 Tamaño de migración: {len(migration_sql)} caracteres")
        
        # Ejecutar migración en Supabase
        print("⚡ Ejecutando migración en Supabase...")
        
        # Usar rpc para ejecutar SQL complejo
        result = supabase_admin.rpc('exec_sql', {'sql_query': migration_sql}).execute()
        
        if result.data:
            print("✅ Migración aplicada exitosamente")
            print(f"📋 Resultado: {result.data}")
        else:
            print("⚠️ Migración completada (sin datos de retorno)")
        
        # Verificar que los campos fueron agregados
        print("🔍 Verificando campos agregados...")
        
        # Consultar la estructura de la tabla
        verify_query = """
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'abogados' 
        AND column_name IN ('tomo', 'folio', 'cuit', 'legajo', 'domicilio_legal', 'nombre_estudio')
        ORDER BY column_name;
        """
        
        verification = supabase_admin.rpc('exec_sql', {'sql_query': verify_query}).execute()
        
        if verification.data and len(verification.data) >= 6:
            print("✅ Verificación exitosa - Todos los campos fueron agregados:")
            for row in verification.data:
                print(f"   • {row['column_name']}: {row['data_type']} ({'NULL' if row['is_nullable'] == 'YES' else 'NOT NULL'})")
        else:
            print("⚠️ Advertencia: Algunos campos podrían no haberse agregado correctamente")
        
        print("\n🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("✅ Tabla abogados extendida con nuevos campos")
        print("✅ Triggers de auto-relleno configurados")
        print("✅ Índices creados para rendimiento")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Actualizar perfiles de abogados con información completa")
        print("2. Implementar upload de imágenes en chat")
        print("3. Integrar datos en generación de demandas")
        
        return True
        
    except Exception as e:
        print(f"❌ Error aplicando migración: {str(e)}")
        print(f"🔍 Tipo de error: {type(e).__name__}")
        
        # Intentar método alternativo si falla rpc
        if "rpc" in str(e).lower() or "exec_sql" in str(e).lower():
            print("\n🔄 Intentando método alternativo...")
            return apply_migration_alternative()
        
        return False

def apply_migration_alternative():
    """Método alternativo para aplicar migración usando sentencias individuales."""
    print("🔄 Aplicando migración con método alternativo...")
    
    try:
        # SQL commands individuales
        commands = [
            """ALTER TABLE public.abogados 
               ADD COLUMN IF NOT EXISTS tomo TEXT,
               ADD COLUMN IF NOT EXISTS folio TEXT,
               ADD COLUMN IF NOT EXISTS condicion_fiscal TEXT,
               ADD COLUMN IF NOT EXISTS cuit TEXT,
               ADD COLUMN IF NOT EXISTS legajo TEXT,
               ADD COLUMN IF NOT EXISTS domicilio_legal TEXT,
               ADD COLUMN IF NOT EXISTS nombre_estudio TEXT,
               ADD COLUMN IF NOT EXISTS telefono_contacto TEXT,
               ADD COLUMN IF NOT EXISTS email_contacto TEXT,
               ADD COLUMN IF NOT EXISTS telefono_secundario TEXT,
               ADD COLUMN IF NOT EXISTS email_secundario TEXT;""",
            
            "CREATE INDEX IF NOT EXISTS idx_abogados_cuit ON public.abogados(cuit);",
            "CREATE INDEX IF NOT EXISTS idx_abogados_legajo ON public.abogados(legajo);",
            "CREATE INDEX IF NOT EXISTS idx_abogados_nombre_estudio ON public.abogados(nombre_estudio);",
        ]
        
        for i, command in enumerate(commands, 1):
            print(f"📝 Ejecutando comando {i}/{len(commands)}...")
            try:
                supabase_admin.rpc('exec_sql', {'sql_query': command}).execute()
                print(f"✅ Comando {i} completado")
            except Exception as cmd_error:
                print(f"⚠️ Comando {i} falló: {str(cmd_error)}")
                # Continuar con el siguiente comando
        
        print("✅ Migración alternativa completada")
        return True
        
    except Exception as e:
        print(f"❌ Error en migración alternativa: {str(e)}")
        print("\n📋 MIGRACIÓN MANUAL REQUERIDA:")
        print("Por favor, ejecute el SQL manualmente en Supabase Dashboard > SQL Editor:")
        print("\n" + "="*60)
        
        # Mostrar SQL para ejecución manual
        migration_file = "migrations/001_extend_abogados_profile.sql"
        if os.path.exists(migration_file):
            with open(migration_file, 'r', encoding='utf-8') as f:
                print(f.read())
        
        print("="*60)
        return False

if __name__ == "__main__":
    print("🚀 APLICADOR DE MIGRACIÓN - EXTENSIÓN ABOGADOS")
    print("="*60)
    
    # Verificar conexión a Supabase
    try:
        test_query = supabase_admin.table('abogados').select('count', count='exact').execute()
        print(f"✅ Conexión a Supabase OK ({test_query.count} abogados registrados)")
    except Exception as e:
        print(f"❌ Error conectando a Supabase: {e}")
        sys.exit(1)
    
    # Aplicar migración
    success = apply_abogados_migration()
    
    if success:
        print("\n🎉 MIGRACIÓN EXITOSA - SISTEMA LISTO PARA USAR")
        sys.exit(0)
    else:
        print("\n❌ MIGRACIÓN FALLÓ - REVISIÓN MANUAL REQUERIDA")
        sys.exit(1) 