#!/usr/bin/env python3
"""
Script de prueba para verificar que el sistema funciona correctamente
con el mensaje inicial y la lógica de conversación.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from rag.chat_agent import ChatAgentInteligente
import asyncio

async def test_sistema_completo():
    """Prueba completa del sistema de chat."""
    
    print("🧪 INICIANDO PRUEBA COMPLETA DEL SISTEMA")
    print("=" * 60)
    
    # Crear agente con user_id de prueba
    user_id = "test-user-123"
    agent = ChatAgentInteligente(user_id)
    
    # Simular sesión nueva (estado = "inicio")
    session = {
        "estado": "inicio",
        "datos_cliente": {},
        "tipo_demanda": "",
        "hechos_adicionales": "",
        "notas_abogado": "",
        "user_id": user_id
    }
    
    session_id = "test-session-123"
    
    print("\n📝 PRUEBA 1: Mensaje inicial en conversación nueva")
    print("Mensaje: 'Hola'")
    
    mensaje1 = "Hola"
    resultado1 = await agent.procesar_mensaje(session.copy(), mensaje1, session_id)
    
    print(f"✅ Respuesta obtenida: {len(resultado1['mensaje'])} caracteres")
    print(f"📄 Primeros 100 chars: {resultado1['mensaje'][:100]}...")
    print(f"🎛️ Estado final: {session.get('estado', 'N/A')}")
    
    # Verificar que contiene el mensaje inicial
    if "¡Hola doctor!" in resultado1['mensaje']:
        print("✅ MENSAJE INICIAL MOSTRADO CORRECTAMENTE")
    else:
        print("❌ MENSAJE INICIAL NO SE MOSTRÓ")
    
    print("\n" + "=" * 60)
    print("📝 PRUEBA 2: Selección de tipo de demanda")
    print("Mensaje: 'Quiero ayuda con Despido'")
    
    # Simular que ya no es el primer mensaje (estado cambió a conversando)
    session2 = {
        "estado": "conversando",
        "datos_cliente": {},
        "tipo_demanda": "",
        "hechos_adicionales": "",
        "notas_abogado": "",
        "user_id": user_id
    }
    
    mensaje2 = "Quiero ayuda con Despido"
    resultado2 = await agent.procesar_mensaje(session2, mensaje2, session_id)
    
    print(f"✅ Respuesta obtenida: {len(resultado2['mensaje'])} caracteres")
    print(f"📄 Respuesta: {resultado2['mensaje']}")
    print(f"🎛️ Estado final: {session2.get('estado', 'N/A')}")
    
    # Verificar que detectó el tipo de demanda
    if "Despido" in resultado2['mensaje']:
        print("✅ TIPO DE DEMANDA DETECTADO CORRECTAMENTE")
    else:
        print("❌ TIPO DE DEMANDA NO DETECTADO")
    
    print("\n" + "=" * 60)
    print("📝 PRUEBA 3: Proporcionar datos del cliente")
    print("Mensaje: 'El cliente se llama Juan Pérez, DNI 12345678'")
    
    # Simular que ya tiene tipo de demanda
    session3 = {
        "estado": "necesita_datos_cliente",
        "datos_cliente": {},
        "tipo_demanda": "Despido",
        "hechos_adicionales": "",
        "notas_abogado": "",
        "user_id": user_id
    }
    
    mensaje3 = "El cliente se llama Juan Pérez, DNI 12345678"
    resultado3 = await agent.procesar_mensaje(session3, mensaje3, session_id)
    
    print(f"✅ Respuesta obtenida: {len(resultado3['mensaje'])} caracteres")
    print(f"📄 Respuesta: {resultado3['mensaje']}")
    print(f"🎛️ Estado final: {session3.get('estado', 'N/A')}")
    
    # Verificar que detectó los datos del cliente
    if "Juan Pérez" in resultado3['mensaje'] or "12345678" in resultado3['mensaje']:
        print("✅ DATOS DEL CLIENTE DETECTADOS CORRECTAMENTE")
    else:
        print("❌ DATOS DEL CLIENTE NO DETECTADOS")
    
    print("\n" + "=" * 60)
    print("✅ PRUEBA COMPLETA FINALIZADA")

if __name__ == "__main__":
    asyncio.run(test_sistema_completo()) 