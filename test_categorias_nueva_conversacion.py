#!/usr/bin/env python3
"""
Script de prueba para verificar que las categorías se muestran correctamente
al iniciar una nueva conversación cuando el abogado tiene categorías creadas.
"""

import asyncio
import sys
import os
from datetime import datetime

# Agregar el directorio backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_categorias_internas():
    """Prueba la lógica interna de categorías sin autenticación."""
    
    print("🧪 PRUEBA: Lógica Interna de Categorías")
    print("=" * 60)
    
    try:
        # Importar módulos del backend
        from core.category_manager import CategoryManager
        from supabase_integration import supabase_admin
        
        # Instanciar el manager de categorías
        category_manager = CategoryManager()
        
        # Usuario de prueba
        user_id = "ae35cd1f-cf86-40b3-9c0d-eb7b6109f413"
        
        print(f"\n📊 PASO 1: Verificando categorías para usuario {user_id}...")
        
        # Obtener categorías del usuario
        categories = category_manager.get_user_categories(user_id)
        print(f"✅ Categorías encontradas: {len(categories)}")
        
        for cat in categories:
            print(f"   📁 {cat.get('nombre')} - {cat.get('descripcion', 'Sin descripción')}")
            print(f"      🎨 Color: {cat.get('color', '#6366f1')}")
            print(f"      🔖 Icono: {cat.get('icon', '📁')}")
            print(f"      ✅ Activo: {cat.get('activo', True)}")
        
        # Verificar estadísticas
        print(f"\n📈 PASO 2: Verificando estadísticas de categorías...")
        
        stats = category_manager.get_category_statistics(user_id)
        print(f"📊 Estadísticas:")
        print(f"   📁 Total categorías: {stats.get('total_categorias', 0)}")
        print(f"   📄 Total documentos: {stats.get('total_documentos', 0)}")
        print(f"   ✅ Documentos procesados: {stats.get('documentos_procesados', 0)}")
        
        # Verificar categorías con documentos procesados
        print(f"\n🔍 PASO 3: Verificando categorías con documentos procesados...")
        
        categorias_con_docs = []
        for cat in categories:
            if cat.get('activo', True):
                # Verificar documentos procesados para esta categoría
                try:
                    result = supabase_admin.table("documentos_entrenamiento")\
                        .select("id,estado_procesamiento")\
                        .eq("categoria_id", cat['id'])\
                        .eq("estado_procesamiento", "completado")\
                        .execute()
                    
                    docs_procesados = len(result.data) if result.data else 0
                    if docs_procesados > 0:
                        categorias_con_docs.append({
                            'nombre': cat['nombre'],
                            'docs_procesados': docs_procesados
                        })
                        print(f"   ✅ {cat['nombre']}: {docs_procesados} documentos procesados")
                    else:
                        print(f"   ⚠️ {cat['nombre']}: 0 documentos procesados")
                except Exception as e:
                    print(f"   ❌ Error verificando {cat['nombre']}: {e}")
        
        print(f"\n📋 RESUMEN:")
        print(f"   📁 Categorías totales: {len(categories)}")
        print(f"   ✅ Categorías con documentos: {len(categorias_con_docs)}")
        
        if len(categorias_con_docs) > 0:
            print(f"\n✅ CORRECTO: El usuario tiene categorías con documentos procesados")
            print(f"   Las categorías se mostrarán al iniciar una nueva conversación")
        else:
            print(f"\n⚠️ ATENCIÓN: El usuario no tiene categorías con documentos procesados")
            print(f"   Se mostrará el mensaje para configurar categorías")
        
        # Simular verificación de chat
        print(f"\n🚀 PASO 4: Simulando verificación para chat...")
        
        try:
            # Verificar si puede crear conversación
            categorias_validas = []
            for cat in categories:
                if cat.get('activo', True):
                    result = supabase_admin.table("documentos_entrenamiento")\
                        .select("id")\
                        .eq("categoria_id", cat['id'])\
                        .eq("estado_procesamiento", "completado")\
                        .execute()
                    
                    if result.data and len(result.data) > 0:
                        categorias_validas.append(cat['nombre'])
            
            print(f"✅ Categorías válidas para chat: {categorias_validas}")
            
            if len(categorias_validas) > 0:
                print(f"✅ El usuario PUEDE crear conversaciones")
                print(f"   Se mostrarán las categorías: {', '.join(categorias_validas)}")
            else:
                print(f"❌ El usuario NO puede crear conversaciones")
                print(f"   Se mostrará mensaje de configuración")
                
        except Exception as e:
            print(f"❌ Error en verificación de chat: {e}")
        
        print("\n" + "=" * 60)
        print("✅ PRUEBA COMPLETADA")
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(f"🕐 Iniciando prueba: {datetime.now().strftime('%H:%M:%S')}")
    asyncio.run(test_categorias_internas()) 