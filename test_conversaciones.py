#!/usr/bin/env python3
"""
Script de prueba para verificar que las conversaciones y mensajes se muestren correctamente
"""

import os
import sys
import asyncio
from datetime import datetime
from supabase import create_client, Client

# Configuración de Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("❌ Error: Variables de entorno SUPABASE_URL y SUPABASE_ANON_KEY no configuradas")
    sys.exit(1)

# Crear cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

async def test_conversaciones():
    """Prueba la carga de conversaciones y mensajes"""
    
    print("🔍 VERIFICANDO CONVERSACIONES EN SUPABASE")
    print("=" * 60)
    
    try:
        # 1. Verificar abogados
        print("\n1. 👥 ABOGADOS REGISTRADOS:")
        abogados_response = supabase.table('abogados').select('*').execute()
        abogados = abogados_response.data
        
        if not abogados:
            print("   ❌ No hay abogados registrados")
            return
        
        for i, abogado in enumerate(abogados[:5]):  # Mostrar solo los primeros 5
            print(f"   {i+1}. ID: {abogado['id']}")
            print(f"      Nombre: {abogado['nombre_completo']}")
            print(f"      Email: {abogado['email']}")
            print(f"      Matrícula: {abogado['matricula_profesional']}")
            print()
        
        # 2. Verificar carpetas
        print("2. 📁 CARPETAS:")
        carpetas_response = supabase.table('carpetas').select('*').execute()
        carpetas = carpetas_response.data
        
        if carpetas:
            for carpeta in carpetas:
                print(f"   📁 {carpeta['nombre']} (ID: {carpeta['id']})")
                print(f"      Abogado: {carpeta['abogado_id']}")
                print()
        else:
            print("   ❌ No hay carpetas registradas")
        
        # 3. Verificar sesiones de chat por abogado
        print("3. 💬 SESIONES DE CHAT:")
        for abogado in abogados[:2]:  # Solo los primeros 2 abogados
            print(f"\n   👤 Abogado: {abogado['nombre_completo']}")
            
            sesiones_response = supabase.table('chat_sesiones')\
                .select('*')\
                .eq('abogado_id', abogado['id'])\
                .order('updated_at', desc=True)\
                .execute()
            
            sesiones = sesiones_response.data
            
            if sesiones:
                print(f"      ✅ {len(sesiones)} sesiones encontradas:")
                
                # Agrupar por carpeta
                por_carpeta = {}
                sin_carpeta = []
                
                for sesion in sesiones:
                    if sesion['carpeta_id']:
                        if sesion['carpeta_id'] not in por_carpeta:
                            por_carpeta[sesion['carpeta_id']] = []
                        por_carpeta[sesion['carpeta_id']].append(sesion)
                    else:
                        sin_carpeta.append(sesion)
                
                # Mostrar sesiones sin carpeta
                if sin_carpeta:
                    print(f"      📄 Sin carpeta asignada: {len(sin_carpeta)} sesiones")
                    for sesion in sin_carpeta[:3]:  # Solo las primeras 3
                        print(f"         • {sesion['titulo']} (Session: {sesion['session_id'][:8]}...)")
                        print(f"           Fecha: {sesion['updated_at']}")
                
                # Mostrar sesiones por carpeta
                for carpeta_id, sesiones_carpeta in por_carpeta.items():
                    carpeta_nombre = next((c['nombre'] for c in carpetas if c['id'] == carpeta_id), 'Desconocida')
                    print(f"      📁 {carpeta_nombre}: {len(sesiones_carpeta)} sesiones")
                    for sesion in sesiones_carpeta[:2]:  # Solo las primeras 2
                        print(f"         • {sesion['titulo']} (Session: {sesion['session_id'][:8]}...)")
            else:
                print("      ❌ No hay sesiones")
        
        # 4. Verificar mensajes en algunas sesiones
        print("\n4. 📝 MENSAJES EN SESIONES:")
        
        # Obtener algunas sesiones para verificar mensajes
        sesiones_sample = supabase.table('chat_sesiones')\
            .select('*')\
            .limit(3)\
            .execute()
        
        if sesiones_sample.data:
            for sesion in sesiones_sample.data:
                print(f"\n   💬 Sesión: {sesion['titulo']}")
                print(f"      Session ID: {sesion['session_id']}")
                print(f"      DB ID: {sesion['id']}")
                
                # Buscar mensajes por el ID interno de la sesión
                mensajes_response = supabase.table('chat_mensajes')\
                    .select('*')\
                    .eq('sesion_id', sesion['id'])\
                    .order('created_at', desc=False)\
                    .execute()
                
                mensajes = mensajes_response.data
                
                if mensajes:
                    print(f"      ✅ {len(mensajes)} mensajes encontrados:")
                    for i, mensaje in enumerate(mensajes[:5]):  # Solo los primeros 5
                        print(f"         {i+1}. [{mensaje['tipo']}] {mensaje['mensaje'][:50]}...")
                        print(f"            Fecha: {mensaje['created_at']}")
                else:
                    print("      ❌ No hay mensajes en esta sesión")
        
        # 5. Resumen final
        print("\n" + "=" * 60)
        print("📊 RESUMEN:")
        print(f"   👥 Abogados: {len(abogados)}")
        print(f"   📁 Carpetas: {len(carpetas) if carpetas else 0}")
        
        total_sesiones = supabase.table('chat_sesiones').select('id').execute()
        print(f"   💬 Total sesiones: {len(total_sesiones.data) if total_sesiones.data else 0}")
        
        total_mensajes = supabase.table('chat_mensajes').select('id').execute()
        print(f"   📝 Total mensajes: {len(total_mensajes.data) if total_mensajes.data else 0}")
        
        print("\n✅ Verificación completada!")
        
        # 6. Sugerencias
        print("\n💡 SUGERENCIAS PARA EL FRONTEND:")
        print("   1. Verificar que el profile.id en AuthContext coincida con abogado_id")
        print("   2. Las sesiones sin carpeta_id deben mostrarse en 'Recientes'")
        print("   3. Al cargar mensajes, usar el session_id para buscar la sesión")
        print("   4. Luego usar el ID interno de la sesión para buscar mensajes")
        
    except Exception as e:
        print(f"❌ Error durante la verificación: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Ejecutar la prueba
    asyncio.run(test_conversaciones()) 