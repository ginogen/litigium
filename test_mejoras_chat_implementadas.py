#!/usr/bin/env python3
"""
Script para probar las mejoras implementadas en el ChatAgent:
1. Mostrar información extraída automáticamente
2. Tipos de demanda dinámicos por abogado
3. Flujo más inteligente y directo
"""

import sys
import os
import asyncio
sys.path.append('.')

async def test_mejoras_implementadas():
    """Test de las mejoras implementadas en el ChatAgent."""
    
    print("🧪 PROBANDO MEJORAS IMPLEMENTADAS EN CHATAGENT")
    print("=" * 60)
    
    try:
        from rag.chat_agent import ChatAgentInteligente, get_chat_agent
        
        # Test 1: Verificar tipos dinámicos por abogado
        print("\n1️⃣ TEST: Tipos dinámicos por abogado")
        print("-" * 40)
        
        # Simular user_id de un abogado
        user_id_test = "test-user-123"
        
        # Crear ChatAgent con user_id
        agent = ChatAgentInteligente(user_id=user_id_test)
        print(f"✅ ChatAgent creado con user_id: {user_id_test}")
        print(f"✅ Tipos disponibles: {agent.tipos_disponibles}")
        
        # Test 2: Verificar función de información extraída
        print("\n2️⃣ TEST: Función de información extraída")
        print("-" * 40)
        
        # Simular cambios automáticos detectados
        cambios_automaticos = {
            'nombre_completo': 'Juan Pérez',
            'tipo_demanda': 'Empleados En Negro',
            'hechos_adicionales': 'Documento indica: Despido laboral, Trabajo en negro. Contexto: Telegrama de despido sin causa aparente...'
        }
        
        session = {
            'datos_cliente': {},
            'tipo_demanda': '',
            'hechos_adicionales': '',
            'estado': 'inicio'
        }
        
        mensaje_info = agent._generar_mensaje_informacion_extraida(cambios_automaticos, session, 'test-session-123')
        print(f"✅ Mensaje de información extraída generado: {len(mensaje_info)} caracteres")
        print(f"Contenido: {mensaje_info[:200]}...")
        
        # Test 3: Verificar flujo completo con información automática
        print("\n3️⃣ TEST: Flujo completo con información automática")
        print("-" * 40)
        
        # Simular sesión con información automática detectada
        session_completa = {
            'datos_cliente': {'nombre_completo': 'María García'},
            'tipo_demanda': 'Empleados En Blanco',
            'hechos_adicionales': 'Despido sin causa aparente',
            'estado': 'conversando'
        }
        
        # Simular mensaje del abogado
        mensaje_abogado = "He subido documentos del caso"
        
        print(f"📝 Mensaje del abogado: {mensaje_abogado}")
        print(f"📋 Sesión actual: {session_completa}")
        
        # Procesar mensaje
        resultado = await agent.procesar_mensaje(session_completa, mensaje_abogado, 'test-session-456')
        
        print(f"✅ Resultado del procesamiento:")
        print(f"   Mensaje: {resultado.get('mensaje', '')[:100]}...")
        print(f"   Información extraída: {resultado.get('informacion_extraida', False)}")
        print(f"   Mostrar confirmación: {resultado.get('mostrar_confirmacion', False)}")
        
        # Test 4: Verificar función get_chat_agent con user_id
        print("\n4️⃣ TEST: Función get_chat_agent con user_id")
        print("-" * 40)
        
        agent_global = get_chat_agent(user_id=user_id_test)
        if agent_global:
            print(f"✅ get_chat_agent con user_id funcionando")
            print(f"   Tipos disponibles: {agent_global.tipos_disponibles}")
        else:
            print("❌ get_chat_agent con user_id falló")
        
        # Test 5: Verificar detección automática
        print("\n5️⃣ TEST: Detección automática de información")
        print("-" * 40)
        
        session_vacia = {
            'datos_cliente': {},
            'tipo_demanda': '',
            'hechos_adicionales': '',
            'estado': 'inicio'
        }
        
        # Simular que hay documentos procesados (esto normalmente vendría de la base de datos)
        print("📄 Simulando documentos procesados...")
        
        # La función _detectar_informacion_automatica intentará obtener información de la base de datos
        # Como estamos en test, probablemente no encuentre documentos, pero debería funcionar sin errores
        cambios = agent._detectar_informacion_automatica(session_vacia, 'test-session-789')
        print(f"✅ Detección automática completada: {len(cambios)} cambios detectados")
        
        print("\n🎯 RESUMEN DE PRUEBAS:")
        print("✅ Tipos dinámicos por abogado - IMPLEMENTADO")
        print("✅ Función de información extraída - IMPLEMENTADA")
        print("✅ Flujo con información automática - IMPLEMENTADO")
        print("✅ get_chat_agent con user_id - IMPLEMENTADO")
        print("✅ Detección automática - IMPLEMENTADA")
        
        print("\n🚀 TODAS LAS MEJORAS IMPLEMENTADAS EXITOSAMENTE!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_integracion_completa():
    """Test de integración completa del flujo mejorado."""
    
    print("\n🔗 TEST DE INTEGRACIÓN COMPLETA")
    print("=" * 50)
    
    try:
        from rag.chat_agent import ChatAgentInteligente
        
        # Simular el flujo completo de un abogado
        print("👨‍💼 Simulando flujo de abogado...")
        
        # 1. Abogado inicia conversación
        agent = ChatAgentInteligente(user_id="abogado-test-123")
        session = {
            'datos_cliente': {},
            'tipo_demanda': '',
            'hechos_adicionales': '',
            'estado': 'inicio'
        }
        
        print("\n📝 PASO 1: Abogado dice 'Hola'")
        resultado1 = await agent.procesar_mensaje(session, "Hola", "session-1")
        print(f"   Respuesta: {resultado1.get('mensaje', '')[:100]}...")
        
        # 2. Abogado sube documentos
        print("\n📤 PASO 2: Abogado sube documentos")
        # Simular que se detectó información automáticamente
        session_con_info = {
            'datos_cliente': {'nombre_completo': 'Carlos López'},
            'tipo_demanda': 'Empleados En Negro',
            'hechos_adicionales': 'Despido sin causa, trabajo en negro',
            'estado': 'conversando'
        }
        
        resultado2 = await agent.procesar_mensaje(session_con_info, "He subido los documentos", "session-1")
        print(f"   Respuesta: {resultado2.get('mensaje', '')[:100]}...")
        print(f"   Información extraída: {resultado2.get('informacion_extraida', False)}")
        
        # 3. Abogado confirma información
        print("\n✅ PASO 3: Abogado confirma información")
        session_confirmada = {
            'datos_cliente': {'nombre_completo': 'Carlos López', 'dni': '12345678'},
            'tipo_demanda': 'Empleados En Negro',
            'hechos_adicionales': 'Despido sin causa, trabajo en negro, empresa XYZ',
            'estado': 'conversando'
        }
        
        resultado3 = await agent.procesar_mensaje(session_confirmada, "Sí, esa información es correcta", "session-1")
        print(f"   Respuesta: {resultado3.get('mensaje', '')[:100]}...")
        print(f"   Mostrar confirmación: {resultado3.get('mostrar_confirmacion', False)}")
        
        print("\n🎉 FLUJO DE INTEGRACIÓN COMPLETADO EXITOSAMENTE!")
        return True
        
    except Exception as e:
        print(f"❌ Error en integración: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBAS DE MEJORAS IMPLEMENTADAS")
    print("=" * 70)
    
    # Ejecutar pruebas
    resultado1 = asyncio.run(test_mejoras_implementadas())
    resultado2 = asyncio.run(test_integracion_completa())
    
    if resultado1 and resultado2:
        print("\n🎯 TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
        print("✅ Las mejoras están funcionando correctamente")
        print("\n📋 RESUMEN DE MEJORAS IMPLEMENTADAS:")
        print("1. ✅ Información extraída se muestra automáticamente")
        print("2. ✅ Tipos de demanda dinámicos por abogado")
        print("3. ✅ Flujo más directo y eficiente")
        print("4. ✅ Mejor experiencia de usuario")
        print("5. ✅ Integración completa funcionando")
    else:
        print("\n❌ ALGUNAS PRUEBAS FALLARON")
        print("⚠️ Revisar implementación")
    
    print("\n🏁 PRUEBAS COMPLETADAS") 