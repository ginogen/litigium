#!/usr/bin/env python3
"""
Script de prueba para verificar que el ChatAgent funciona correctamente
con las mejoras implementadas para hacerlo más fluido y conversacional.
"""

import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag.chat_agent import ChatAgentInteligente

async def test_chat_agent():
    """Prueba el ChatAgent con diferentes tipos de mensajes."""
    
    print("🧪 INICIANDO PRUEBAS DEL CHATAGENT FLUIDO")
    print("=" * 50)
    
    # Crear instancia del ChatAgent
    chat_agent = ChatAgentInteligente()
    
    # Simular una sesión
    session = {
        "datos_cliente": {},
        "tipo_demanda": "",
        "hechos_adicionales": "",
        "notas_abogado": "",
        "estado": "conversando",
        "user_id": "test_user"
    }
    
    session_id = "test_session_123"
    
    # Prueba 1: Primer mensaje
    print("\n🔍 PRUEBA 1: Primer mensaje")
    print("Mensaje: 'Quiero ayuda con Despido...'")
    
    try:
        respuesta = await chat_agent.procesar_mensaje(session, "Quiero ayuda con Despido...", session_id)
        print(f"✅ Respuesta recibida: {respuesta.get('mensaje', 'Sin mensaje')[:100]}...")
        print(f"📊 Estado: {session.get('estado')}")
        print(f"👤 Datos cliente: {session.get('datos_cliente')}")
    except Exception as e:
        print(f"❌ Error en prueba 1: {e}")
    
    # Prueba 2: Agregar datos del cliente
    print("\n🔍 PRUEBA 2: Agregar datos del cliente")
    print("Mensaje: 'El cliente se llama Juan Pérez, DNI 12345678'")
    
    try:
        respuesta = await chat_agent.procesar_mensaje(session, "El cliente se llama Juan Pérez, DNI 12345678", session_id)
        print(f"✅ Respuesta recibida: {respuesta.get('mensaje', 'Sin mensaje')[:100]}...")
        print(f"📊 Estado: {session.get('estado')}")
        print(f"👤 Datos cliente: {session.get('datos_cliente')}")
    except Exception as e:
        print(f"❌ Error en prueba 2: {e}")
    
    # Prueba 3: Agregar hechos
    print("\n🔍 PRUEBA 3: Agregar hechos")
    print("Mensaje: 'Fue despedido sin causa el 15 de marzo, trabajaba en la empresa ABC'")
    
    try:
        respuesta = await chat_agent.procesar_mensaje(session, "Fue despedido sin causa el 15 de marzo, trabajaba en la empresa ABC", session_id)
        print(f"✅ Respuesta recibida: {respuesta.get('mensaje', 'Sin mensaje')[:100]}...")
        print(f"📊 Estado: {session.get('estado')}")
        print(f"📝 Hechos: {session.get('hechos_adicionales', '')[:100]}...")
    except Exception as e:
        print(f"❌ Error en prueba 3: {e}")
    
    # Prueba 4: Mensaje con mucha información
    print("\n🔍 PRUEBA 4: Mensaje con mucha información")
    print("Mensaje: 'María González, DNI 87654321, vive en Paraguay 1234, teléfono 11-1234-5678, fue empleada doméstica en negro durante 2 años'")
    
    try:
        respuesta = await chat_agent.procesar_mensaje(session, "María González, DNI 87654321, vive en Paraguay 1234, teléfono 11-1234-5678, fue empleada doméstica en negro durante 2 años", session_id)
        print(f"✅ Respuesta recibida: {respuesta.get('mensaje', 'Sin mensaje')[:100]}...")
        print(f"📊 Estado: {session.get('estado')}")
        print(f"👤 Datos cliente: {session.get('datos_cliente')}")
    except Exception as e:
        print(f"❌ Error en prueba 4: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 PRUEBAS COMPLETADAS")
    print(f"📊 Estado final: {session.get('estado')}")
    print(f"👤 Datos finales: {session.get('datos_cliente')}")
    print(f"📝 Hechos finales: {session.get('hechos_adicionales', '')[:100]}...")

if __name__ == "__main__":
    asyncio.run(test_chat_agent()) 