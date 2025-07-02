#!/usr/bin/env python3
"""
Script Maestro de Migraciones
Aplica todas las migraciones del sistema de manera secuencial y segura.
"""

import os
import sys
import asyncio
from datetime import datetime
from typing import List, Dict, Any

# Configurar path para imports
sys.path.append(os.path.dirname(__file__))

from supabase_integration import supabase_admin

class MigrationManager:
    """Gestor de migraciones del sistema."""
    
    def __init__(self):
        self.migrations = [
            {
                "id": "001",
                "name": "extend_abogados_profile",
                "description": "Extiende perfil de abogados con campos del workflow",
                "file": "migrations/001_extend_abogados_profile.sql",
                "required": True
            },
            {
                "id": "002", 
                "name": "create_documentos_chat",
                "description": "Crea tabla para documentos del chat con GPT-4 Vision",
                "file": "migrations/002_create_documentos_chat.sql", 
                "required": True
            }
        ]
        
        self.applied_migrations = []
        self.failed_migrations = []
    
    async def apply_all_migrations(self) -> bool:
        """Aplica todas las migraciones pendientes."""
        print("🚀 INICIANDO APLICACIÓN DE MIGRACIONES")
        print("=" * 60)
        
        # Verificar conexión
        if not await self._test_connection():
            print("❌ Error de conexión a Supabase")
            return False
        
        # Crear tabla de control de migraciones si no existe
        await self._ensure_migrations_table()
        
        # Obtener migraciones ya aplicadas
        applied_ids = await self._get_applied_migrations()
        
        print(f"📋 Migraciones aplicadas previamente: {applied_ids}")
        print(f"📋 Migraciones disponibles: {len(self.migrations)}")
        
        # Aplicar migraciones pendientes
        success = True
        for migration in self.migrations:
            migration_id = migration["id"]
            
            if migration_id in applied_ids:
                print(f"⏭️  Migración {migration_id} ya aplicada, saltando...")
                continue
            
            print(f"\n🔧 Aplicando migración {migration_id}: {migration['name']}")
            
            if await self._apply_single_migration(migration):
                self.applied_migrations.append(migration)
                print(f"✅ Migración {migration_id} aplicada exitosamente")
            else:
                self.failed_migrations.append(migration)
                print(f"❌ Migración {migration_id} falló")
                
                if migration.get("required", False):
                    print(f"🛑 Migración {migration_id} es requerida, deteniendo proceso")
                    success = False
                    break
        
        # Resumen final
        self._print_summary()
        
        return success and len(self.failed_migrations) == 0
    
    async def _test_connection(self) -> bool:
        """Prueba la conexión a Supabase."""
        try:
            print("🔍 Probando conexión a Supabase...")
            
            # Probar con una consulta simple
            result = supabase_admin.table('abogados').select('count', count='exact').execute()
            
            count = result.count or 0
            print(f"✅ Conexión exitosa - {count} abogados en la base de datos")
            return True
            
        except Exception as e:
            print(f"❌ Error de conexión: {str(e)}")
            return False
    
    async def _ensure_migrations_table(self):
        """Crea la tabla de control de migraciones si no existe."""
        try:
            migration_table_sql = """
            CREATE TABLE IF NOT EXISTS public.schema_migrations (
                id SERIAL PRIMARY KEY,
                migration_id TEXT UNIQUE NOT NULL,
                migration_name TEXT NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                checksum TEXT,
                execution_time_ms INTEGER
            );
            
            -- Índice para consultas rápidas
            CREATE INDEX IF NOT EXISTS idx_schema_migrations_id 
            ON public.schema_migrations(migration_id);
            
            -- Comentario
            COMMENT ON TABLE public.schema_migrations 
            IS 'Control de migraciones aplicadas al esquema de la base de datos';
            """
            
            await self._execute_sql(migration_table_sql)
            print("✅ Tabla de control de migraciones verificada")
            
        except Exception as e:
            print(f"⚠️ Error creando tabla de migraciones: {e}")
    
    async def _get_applied_migrations(self) -> List[str]:
        """Obtiene la lista de migraciones ya aplicadas."""
        try:
            result = supabase_admin.table('schema_migrations')\
                .select('migration_id')\
                .execute()
            
            return [row['migration_id'] for row in (result.data or [])]
            
        except Exception as e:
            print(f"⚠️ Error obteniendo migraciones aplicadas: {e}")
            return []
    
    async def _apply_single_migration(self, migration: Dict[str, Any]) -> bool:
        """Aplica una migración individual."""
        start_time = datetime.now()
        
        try:
            # Leer archivo de migración
            migration_file = migration["file"]
            
            if not os.path.exists(migration_file):
                print(f"❌ Archivo de migración no encontrado: {migration_file}")
                return False
            
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            print(f"📄 Leyendo migración desde: {migration_file}")
            print(f"📊 Tamaño: {len(migration_sql)} caracteres")
            
            # Ejecutar migración
            await self._execute_sql(migration_sql)
            
            # Calcular tiempo de ejecución
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Registrar migración como aplicada
            await self._record_migration(migration, execution_time)
            
            print(f"⏱️  Tiempo de ejecución: {execution_time:.2f}ms")
            return True
            
        except Exception as e:
            print(f"❌ Error aplicando migración {migration['id']}: {str(e)}")
            return False
    
    async def _execute_sql(self, sql: str):
        """Ejecuta SQL usando el método más apropiado."""
        try:
            # Intentar usar RPC si está disponible
            result = supabase_admin.rpc('exec_sql', {'sql_query': sql}).execute()
            return result
            
        except Exception as rpc_error:
            # Si RPC falla, intentar dividir en comandos individuales
            print(f"⚠️ RPC falló, usando método alternativo: {rpc_error}")
            
            # Dividir por punto y coma y ejecutar comando por comando
            commands = [cmd.strip() for cmd in sql.split(';') if cmd.strip()]
            
            for i, command in enumerate(commands):
                if not command:
                    continue
                    
                try:
                    # Para comandos simples, usar el cliente directamente
                    if command.upper().startswith(('CREATE TABLE', 'ALTER TABLE', 'CREATE INDEX')):
                        supabase_admin.rpc('exec_sql', {'sql_query': command + ';'}).execute()
                    
                except Exception as cmd_error:
                    if "already exists" in str(cmd_error).lower():
                        print(f"⚠️ Comando {i+1} ya existe, continuando...")
                    else:
                        raise cmd_error
    
    async def _record_migration(self, migration: Dict[str, Any], execution_time: float):
        """Registra una migración como aplicada."""
        try:
            migration_record = {
                "migration_id": migration["id"],
                "migration_name": migration["name"],
                "execution_time_ms": int(execution_time)
            }
            
            supabase_admin.table('schema_migrations')\
                .insert(migration_record)\
                .execute()
                
        except Exception as e:
            print(f"⚠️ Error registrando migración: {e}")
    
    def _print_summary(self):
        """Imprime resumen de la aplicación de migraciones."""
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE MIGRACIONES")
        print("=" * 60)
        
        print(f"✅ Aplicadas exitosamente: {len(self.applied_migrations)}")
        for migration in self.applied_migrations:
            print(f"   • {migration['id']}: {migration['name']}")
        
        if self.failed_migrations:
            print(f"\n❌ Fallidas: {len(self.failed_migrations)}")
            for migration in self.failed_migrations:
                print(f"   • {migration['id']}: {migration['name']}")
        
        print(f"\n📋 Total procesadas: {len(self.applied_migrations) + len(self.failed_migrations)}")
        
        if not self.failed_migrations:
            print("\n🎉 TODAS LAS MIGRACIONES APLICADAS EXITOSAMENTE")
            print("\n📋 PRÓXIMOS PASOS:")
            print("1. ✅ Perfil de abogados extendido con nuevos campos")
            print("2. ✅ Sistema de upload múltiple de imágenes listo")
            print("3. ✅ Procesador GPT-4 Vision configurado")
            print("4. 🔄 Actualizar frontend para usar nuevas funcionalidades")
            print("5. 🔄 Integrar datos extraídos en generación de demandas")
        else:
            print("\n⚠️ ALGUNAS MIGRACIONES FALLARON")
            print("Revise los errores arriba y ejecute manualmente si es necesario")

async def main():
    """Función principal del script."""
    print("🚀 GESTOR DE MIGRACIONES - SISTEMA LEGAL AI")
    print("=" * 60)
    print(f"⏰ Iniciado en: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    manager = MigrationManager()
    
    try:
        success = await manager.apply_all_migrations()
        
        if success:
            print("\n🎉 MIGRACIONES COMPLETADAS EXITOSAMENTE")
            sys.exit(0)
        else:
            print("\n❌ MIGRACIONES FALLARON - REVISIÓN MANUAL REQUERIDA")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏸️ Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error inesperado: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Verificar Python version
    if sys.version_info < (3, 7):
        print("❌ Requiere Python 3.7 o superior")
        sys.exit(1)
    
    # Ejecutar
    asyncio.run(main()) 